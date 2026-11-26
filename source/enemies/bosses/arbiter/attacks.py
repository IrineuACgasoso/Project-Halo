"""Rotinas do Arbiter de média/longa distância, reações e o que corre fora da rotina
(geradores: `yield` = 1 frame; todo `while` tem `yield`)."""
import math
import random

import pygame

from source.enemies.standard.elite import Elite
from source.feats.projetil import Carabin
from source.feats.skills.invisibilidade import FADE_IN, FADE_OUT, OCULTO
from source.feats.skills.purge_grid import PurgeGrid
from source.systems.entitymanager import entity_manager

from .config import CFG

V2 = pygame.math.Vector2


class ArbiterAttacks:
    # ================================================================ fora da rotina
    def _fora_da_rotina(self):
        """Bombardeio e invocação: ordens dadas sem parar o que está fazendo."""
        agora = self._agora
        if agora >= self.cd_fora['bombardeio']:
            self._bombardear()
            self._agendar_fora('bombardeio')
        if (self.fase_cfg.invoca and agora >= self.cd_fora['invocacao']
                and not self.invisivel and not self.no_ar):
            if self._invocar_elites(CFG.elites_por_invocacao):
                self._agendar_fora('invocacao')
            else:   # escolta cheia ou sem chão: tenta de novo logo, sem queimar o cooldown inteiro
                self.cd_fora['invocacao'] = agora + 3000

    def _agendar_fora(self, nome):
        minimo, maximo = CFG.cooldown_fora[nome]
        self.cd_fora[nome] = self._agora + int(self.novo_cooldown(minimo, maximo) * self.fase_cfg.mult_cooldown)

    def _bombardear(self):
        """Phantom: uma linha de plasma varre o mapa passando pelo jogador, em ângulo sorteado."""
        purge = PurgeGrid(self.game, self, preset=CFG.bombardeio_preset)
        purge.habilidade = None        # não é da rotina em curso (a memória não confunde)
        purge.iniciar(self._agora)

    # ================================================================ invocação
    def _podar_elites(self):
        self.elites_invocados = [e for e in self.elites_invocados if e.alive()]

    @property
    def escoltas_vivas(self):
        """Elites invocados ainda vivos (a escolta que cobre o recuo)."""
        self._podar_elites()
        return self.elites_invocados

    def _posicoes_spawn(self, quantidade):
        posicoes = []
        for _ in range(quantidade):
            for _t in range(CFG.spawn_tentativas):
                ang = random.uniform(0, 2 * math.pi)
                r = random.uniform(*CFG.spawn_raio)
                p = self.posicao + V2(math.cos(ang), math.sin(ang)) * r
                if self.verificar_posicao_valida(p) and all(p.distance_to(o) > 45 for o in posicoes):
                    posicoes.append(p)
                    break
        return posicoes

    def _invocar_elites(self, quantidade):
        """Retorna quantos Elites realmente nasceram (respeita o teto). Chegam camuflados."""
        self._podar_elites()
        vagas = CFG.max_elites - len(self.elites_invocados)
        nasceram = 0
        for pos in self._posicoes_spawn(min(quantidade, max(0, vagas))):
            elite = Elite(pos, game=self.game)
            entity_manager.all_sprites.add(elite)
            entity_manager.inimigos_grupo.add(elite)
            elite.materializar()
            self.elites_invocados.append(elite)
            nasceram += 1
        return nasceram

    # ================================================================== carabina
    def atirar_carabina(self, spread=0.03, dano=None, direcao=None):
        """`direcao` None = mira no jogador com spread por eixo; dada = esse vetor com jitter angular."""
        dano = CFG.carabina_dano if dano is None else dano
        if direcao is None:
            direcao = self.calcular_direcao_tiro(spread)
        else:
            direcao = direcao.rotate(random.uniform(-1, 1) * math.degrees(spread))

        self.trigger_flash(CFG.revelar_tiro_ms, CFG.revelar_tiro_alpha)
        Carabin(
            posicao_inicial=self.posicao.copy(),
            grupos=(entity_manager.all_sprites,),
            jogador=self.jogador,
            game=self.game,
            dono=CFG.dono_projetil, fonte=self,
            tamanho=(CFG.carabina_tamanho, CFG.carabina_tamanho),
            dano=dano,
            velocidade=CFG.carabina_vel_proj,
            direcao_spread=direcao,
        )

    def rotina_carabina(self):
        """Rajada de precisão: mira (telegraph) -> 6 tiros com antecipação, circulando o tempo todo."""
        yield from self._esperar(CFG.carabina_mira, strafe=0.35)
        base = self.direcao_antecipada(CFG.carabina_vel_proj, CFG.carabina_antecipacao)
        for _ in range(CFG.carabina_tiros):
            self.atirar_carabina(CFG.carabina_spread, direcao=base)
            alvo = self.direcao_antecipada(CFG.carabina_vel_proj, CFG.carabina_antecipacao)
            mix = base * (1 - CFG.carabina_rastreio) + alvo * CFG.carabina_rastreio
            base = mix.normalize() if mix.length_squared() > 1e-6 else alvo
            yield from self._esperar(CFG.carabina_intervalo, strafe=CFG.carabina_strafe)
        yield from self._esperar(CFG.carabina_recuperacao, strafe=0.4)
        self.agendar('carabina')
        self.wait = 500

    # ================================================================ emboscada
    def _ponto_de_flanco(self):
        """Ponto válido do outro lado do jogador (ângulo sorteado a partir de jogador -> Arbiter)."""
        para_mim = self.posicao - self.jogador.posicao
        if para_mim.length_squared() < 1e-6:
            para_mim = V2(1, 0)
        para_mim.normalize_ip()
        for _ in range(CFG.flanco_tentativas):
            angulo = random.uniform(*CFG.flanco_angulo) * random.choice((-1, 1))
            ponto = self.jogador.posicao + para_mim.rotate(angulo) * random.uniform(*CFG.flanco_raio)
            if self.verificar_posicao_valida(ponto):
                return ponto
        return None

    def rotina_emboscada(self):
        """Golpe fantasma: camuflagem -> some do campo de visão e reaparece no flanco -> sprint
        invisível -> golpe de espada (o cone azul aparece mesmo com ele invisível)."""
        self.iniciar_invisibilidade(CFG.emboscada_preset)
        teleportou = False
        try:
            while self.invisibilidade is not None:
                fase = self.fase_invisibilidade
                self._ir(self.dir_jogador(), CFG.emboscada_mult_vel if fase != FADE_OUT else 0.5)
                self.animador.tocar('reaparecer' if fase == FADE_IN else 'furtivo')
                if fase == OCULTO and not teleportou:
                    teleportou = True
                    ponto = self._ponto_de_flanco()
                    if ponto is not None:
                        self.posicao.update(ponto)
                        self.sync_rect()
                if teleportou and fase in (OCULTO, FADE_IN) and self.dist_jogador() <= CFG.emboscada_dist:
                    yield from self.rotina_lamina(emboscada=True)
                    break
                yield
        finally:
            self.encerrar_invisibilidade()
        self.agendar('emboscada')
        self.wait = 700

    # ================================================================ esquiva
    def _lado_da_esquiva(self):
        """De lado (sai da linha dos tiros); sem escudo e recuando, na diagonal para trás."""
        to = self.dir_jogador()
        lados = [V2(-to.y, to.x), V2(to.y, -to.x)]
        if self.postura == 'recuo':
            lados = [lados[0].rotate(CFG.recuo_esquiva_graus), lados[1].rotate(-CFG.recuo_esquiva_graus)]
        random.shuffle(lados)
        for lado in lados:
            if self.verificar_posicao_valida(self.posicao + lado * CFG.esquiva_dist_teste):
                return lado
        return lados[0]

    def rotina_esquiva(self):
        """Muito dano em pouco tempo: dash perpendicular ao jogador (sai da linha dos tiros). Às vezes
        (só com a carabina) some no dash e revida com um spray antes de reaparecer."""
        spray = self.fase_cfg.carabina and random.random() < CFG.esquiva_spray_chance
        if spray:
            self.iniciar_invisibilidade(CFG.esquiva_preset)
        try:
            lado = self._lado_da_esquiva()
            yield from self._dash(CFG.esquiva_dash, alvo=self.posicao + lado * CFG.esquiva_dist_teste)
            if spray:
                for _ in range(CFG.spray_tiros):
                    self.atirar_carabina(spread=CFG.spray_spread, dano=CFG.spray_dano)
                    yield from self._esperar(CFG.spray_intervalo)
                yield from self._esperar(CFG.spray_saida_ms, strafe=0.6)
        finally:
            self.encerrar_invisibilidade()
        self.agendar('esquiva')
        self.wait = 300

    # ================================================================ anti-stuck
    def rotina_antistuck(self):
        """Preso longe do jogador: salta por cima do que o prende e pousa onde o jogador está, com o golpe frontal."""
        yield from self.rotina_salto(preset=CFG.antistuck_salto, agendar=False)

    # ================================================================ transição
    def rotina_transicao(self):
        """Espada e Honra: grito, onda de choque 360 (expulsa quem está colado) e escudo cheio."""
        yield from self._grito()
        self.adicionar_escudo(self.escudo_maximo)
        self.sem_escudo = False
        self._escudo_quebrou = False
        cfg = self._lancar_cone(CFG.transicao_cone, self.dir_jogador())
        yield from self._esperar(cfg.duracao + 200)
        self.wait = 600
