"""Espada de energia (cones e cortes azuis), granada de plasma, salto e o combo da quebra de escudo
(geradores: `yield` = 1 frame; todo `while` tem `yield`)."""
import random
from dataclasses import replace

import pygame

from source.feats.grenades import PlasmaGrenade
from source.feats.skills.artilharia import ArtilhariaAviso
from source.feats.skills.cone_strike import ConeStrikeAviso
from source.feats.skills.cone_strike.config import CONE_STRIKE_PRESETS
from source.feats.skills.dash import DASH_PRESETS
from source.feats.skills.rect_strike import RectStrikeAviso
from source.feats.skills.salto import Salto
from source.systems.entitymanager import entity_manager
from source.systems.status import BuffVelocidade, aplicar, remover

from .config import CFG
from .vfx import impacto_da_espada

V2 = pygame.math.Vector2


class ArbiterArsenal:
    # ------------------------------------------------------------------ golpes
    def _raio_lamina(self):
        return CONE_STRIKE_PRESETS[CFG.lamina_preset].raio

    def _lancar_cone(self, preset, direcao, duracao_mult=1.0, duracao=None, seguir=None, posicao=None):
        """Cria o cone (na posição atual, ou em `posicao`) e devolve a config efetiva."""
        cfg = CONE_STRIKE_PRESETS[preset]
        if duracao is None and duracao_mult != 1.0:
            duracao = int(cfg.duracao * duracao_mult)
        custom = replace(cfg, duracao=duracao) if duracao is not None else None
        ConeStrikeAviso(
            posicao=(self.posicao if posicao is None else posicao).copy(),
            direcao=direcao,
            grupos=(entity_manager.all_sprites,),
            game=self.game,
            dono=CFG.dono_skills, fonte=self,
            preset=preset,
            custom_config=custom,
            ao_explodir=impacto_da_espada,
            seguir=seguir,
        )
        return custom or cfg

    def _corte(self, origem, direcao, preset):
        """Retângulo azul saindo de `origem`. Devolve a duração do aviso (ms)."""
        aviso = RectStrikeAviso(V2(origem), direcao, (entity_manager.all_sprites,), self.game,
                                dono=CFG.dono_skills, preset=preset, fonte=self, ao_explodir=impacto_da_espada)
        return aviso.cfg.duracao

    # ------------------------------------------------------------------ lâmina (colado)
    def _avancar(self, ms, mult):
        """Investida curta em direção ao jogador (fecha o gap entre golpes do combo)."""
        if self.dist_jogador() < 90:
            return
        fim = self._agora + ms
        while self._agora < fim:
            self._ir(self.dir_jogador(), mult)
            self.animador.tocar('investida')
            yield

    def rotina_lamina(self, emboscada=False):
        """Combo de espada de perto: cada golpe é um cone azul (mira travada no início) -> dano ->
        avanço -> próximo golpe, mais rápido."""
        golpes = 1 if emboscada else self.fase_cfg.lamina_golpes
        for i in range(golpes):
            cfg = self._lancar_cone(CFG.lamina_preset, self.dir_jogador(), CFG.lamina_combo_mult ** i)
            if emboscada or self.invisivel:     # golpear o revela: janela de contra-ataque
                self.trigger_flash(cfg.duracao + 250, 150)
            yield from self._esperar(cfg.duracao + CFG.lamina_flash)
            if i < golpes - 1:
                yield from self._avancar(CFG.lamina_avanco_ms, CFG.lamina_avanco_mult)
                yield from self._esperar(CFG.lamina_pausa)
        yield from self._esperar(CFG.lamina_recuperacao)
        self.agendar('lamina')
        if not emboscada:
            self.wait = 500

    # ------------------------------------------------------------------ investida (Prophet's Bane)
    def rotina_investida(self):
        """Saca a espada, investe e o cone já carrega no caminho (vai junto com ele): estoura quando
        ele chega. Depois fica atordoado, inofensivo e com as costas expostas (dano dobrado)."""
        yield from self._esperar(CFG.investida_preparo_ms)
        alvo = V2(self.jogador.posicao)
        linha = alvo - self.posicao
        dist = linha.length()
        if dist > CFG.investida_para_antes:
            alvo = self.posicao + linha / dist * (dist - CFG.investida_para_antes)
        dash_cfg = DASH_PRESETS[CFG.investida_dash]
        viagem_ms = min(self.posicao.distance_to(alvo) / dash_cfg.velocidade * 1000, dash_cfg.duracao_ms)
        carga = max(CFG.investida_cone_min_ms, int(viagem_ms + CFG.investida_cone_folga_ms))
        direcao = (alvo - self.posicao)
        direcao = direcao.normalize() if direcao.length_squared() > 1e-6 else self.dir_jogador()
        inicio = self._agora
        self._lancar_cone(CFG.investida_cone, direcao, duracao=carga, seguir=self)
        direcao = yield from self._dash(CFG.investida_dash, alvo=alvo)
        self.is_inofensivo = True           # parado em cima de onde o jogador estava: quem fere é o cone
        try:
            yield from self._esperar(max(0, carga - (self._agora - inicio)), olhar_x=direcao.x)
            self._costas = (-direcao, self._agora + CFG.investida_stun_ms)
            yield from self._esperar(CFG.investida_stun_ms, olhar_x=direcao.x)
        finally:
            self.is_inofensivo = False
            self._costas = None
        self.agendar('investida')
        self.wait = 300

    # ------------------------------------------------------------------ salto curto + golpe frontal
    def rotina_salto(self, preset=None, agendar=True):
        """Salto baixo que pousa antes do jogador, na direção dele, e golpeia um retângulo largo à frente.
        No ar não é mirado nem atingido. É também o anti-stuck (passa por cima da parede)."""
        yield from self._esperar(CFG.salto_preparo_ms)
        salto = self._salto = Salto(self, preset=preset or CFG.salto_preset)
        try:
            while not salto.atualizar(self._dt):
                self._parar(salto.direcao.x)
                self.animador.tocar('investida')
                yield
        finally:
            salto.cancelar()
            self._salto = None
        direcao = salto.direcao
        aviso = self._corte(self.posicao, direcao, CFG.salto_golpe)
        yield from self._esperar(aviso + CFG.salto_recuperacao_ms, olhar_x=direcao.x)
        if agendar:
            self.agendar('salto')
            self.wait = 400

    # ------------------------------------------------------------------ granada
    def _validar_alvo_granada(self, alvo):
        """Garante distancia minima/maxima de arremesso e que o ponto de queda esteja em chao valido."""
        to = alvo - self.posicao
        dist = to.length()
        direcao = to.normalize() if dist > 1e-6 else self.dir_jogador()
        dist = max(CFG.granada_dist_min, min(CFG.granada_dist_max, dist))
        alvo = self.posicao + direcao * dist
        for t in (1.0, 0.85, 0.7, 0.55, 0.4):
            p = self.posicao + (alvo - self.posicao) * t
            if self.verificar_posicao_valida(p):
                return p
        return V2(self.jogador.posicao)

    def _alvo_granada(self, indice):
        """1a granada: onde o jogador vai estar. Seguintes: fecham o cerco pelos lados."""
        base = self.ponto_antecipado(CFG.granada_vel, CFG.granada_antecipacao)
        if indice > 0:
            d = self.dir_jogador()
            lado = 1 if indice % 2 else -1
            base = base + V2(-d.y, d.x) * lado * CFG.granada_offset_lateral
        return self._validar_alvo_granada(base)

    def _lancar_granada(self, alvo):
        PlasmaGrenade(
            posicao_inicial=self.posicao.copy(),
            posicao_alvo=alvo,
            grupos=(entity_manager.all_sprites,),
            game=self.game,
            dono=CFG.dono_skills, fonte=self,
            inimigos_grupo=self.jogador,       # sprite unico: gruda no JOGADOR
            preset=CFG.granada_preset,
        )

    def rotina_granada(self):
        n = self.fase_cfg.granadas
        yield from self._esperar(CFG.granada_preparo, strafe=0.25)      # telegraph: quase parado
        for i in range(n):
            self._lancar_granada(self._alvo_granada(i))
            if i < n - 1:
                yield from self._esperar(CFG.granada_intervalo, strafe=0.25)
        yield from self._esperar(CFG.granada_recuperacao, strafe=0.4)
        self.agendar('granada')
        self.wait = 600

    # ------------------------------------------------------------------ quebra de escudo
    def _grito(self):
        """Sub-rotina: a pose do grito Sangheili (parado, o corpo treme, faíscas e tremor)."""
        self.grito_vfx()
        fim = self._agora + CFG.grito_ms
        while self._agora < fim:
            self._parar()
            self.animador.tocar('grito')
            yield

    def _iniciar_furia(self):
        aplicar(self, BuffVelocidade(CFG.furia_buff), chave=self)
        self._furia_ate = float('inf')          # o fim é contado do fim do combo

    def _atualizar_furia(self, agora):
        if self._furia_ate is not None and agora >= self._furia_ate:
            self._furia_ate = None
            remover(self, BuffVelocidade, chave=self)

    def _golpe_do_combo(self, tipo, posicao, direcao):
        """Solta o golpe de um dash do combo em `posicao`. Devolve quando ele estoura (ms de jogo)."""
        if tipo == 'artilharia':
            duracao = ArtilhariaAviso(posicao=V2(posicao), grupos=(entity_manager.all_sprites,),
                                      game=self.game, dono=CFG.dono_skills, fonte=self,
                                      preset=CFG.combo_artilharia).cfg.duracao
        elif tipo == 'cone':
            duracao = self._lancar_cone(CFG.combo_cone, direcao, posicao=posicao).duracao
        elif tipo == 'linha':
            duracao = self._corte(posicao, direcao, CFG.combo_linha)
        else:   # 'frontal'
            duracao = self._corte(posicao, direcao, CFG.combo_frontal)
        return self._agora + duracao

    def rotina_combo(self):
        """Grito, Fúria Honorável e 5 dashes até o jogador. Cada um: prepara (parado, encarando),
        investe e solta um golpe sorteado (nunca o mesmo duas vezes seguidas), e fica na pose até o
        golpe estourar antes de preparar o próximo:
        - artilharia: explosão onde ele parou;
        - frontal: o corte largo do salto para a frente;
        - cone: o cone da investida para a frente;
        - linha: um corte fino e bem comprido para a frente (pune quem recuou em linha reta).
        Não fica vulnerável em nenhum deles."""
        yield from self._grito()
        self._iniciar_furia()
        self.is_inofensivo = True           # o corpo não fere no combo: os golpes de cada dash, sim
        anterior = None
        try:
            for _ in range(CFG.combo_dashes):
                tipo = random.choice([t for t in CFG.combo_tipos if t != anterior])
                anterior = tipo
                yield from self._esperar(random.randint(*CFG.combo_preparo_ms), olhar_x=self.dir_jogador().x)
                direcao = yield from self._dash(CFG.combo_dash)
                estouro = self._golpe_do_combo(tipo, self.posicao, direcao)
                espera = max(0, estouro - self._agora) + random.randint(*CFG.combo_pausa_ms)
                yield from self._esperar(espera, olhar_x=direcao.x)
            yield from self._esperar(CFG.combo_recuperacao_ms)
        finally:
            self.is_inofensivo = False
            self._furia_ate = self._agora + CFG.furia_ms
        self.agendar('combo')
        self.wait = 200
