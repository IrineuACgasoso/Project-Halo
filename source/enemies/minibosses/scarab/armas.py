"""As armas do Scarab: canhão de foco, torreta de plasma e desembarque. Cada uma corre no seu tempo, por
fora das rotinas (ele atira andando, pisando ou sentado); só a queda e a morte as desligam."""
import random

import pygame

from source.enemies.standard.elite import Elite
from source.enemies.standard.grunt import GruntBlue, GruntRed
from source.enemies.standard.jackal import Jackal
from source.feats.projetil import PlasmaGun
from source.systems.entitymanager import entity_manager
from source.utils.vetores import direcao_segura

from .config import CFG, ESCOTILHAS, FASE_CRITICA, PIVO_TORRETA, PONTA_CANHAO, TORRETA_SENTADO_DY
from .corpo import pivo_torreta

V2 = pygame.math.Vector2

GUARNICAO = {'grunt_blue': GruntBlue, 'grunt_red': GruntRed, 'jackal': Jackal, 'elite': Elite}
HISTERESE_MIRA = 60      # px: o canhão só troca de lado quando o alvo passa disto


class ScarabArmas:
    @property
    def critico(self):
        return self.fase >= FASE_CRITICA

    @property
    def armas_ligadas(self):
        return not (self.desabado or self.morrendo)

    def atualizar_armas(self, agora, delta_time):
        if not self.armas_ligadas:
            return
        self.atualizar_feixe(agora, delta_time)
        self.atualizar_torreta(agora)
        self.atualizar_desembarque(agora)

    def desligar_armas(self):
        self.feixe_estado = 'espera'
        self.tiros_restantes = 0
        self.desembarque_em_curso = None

    def rearmar(self):
        """Ao se erguer: nada dispara na hora."""
        minimo = self._agora + CFG.rearme_ms
        self.proximo_feixe = max(self.proximo_feixe, minimo)
        self.proxima_rajada = max(self.proxima_rajada, minimo)
        self.proximo_desembarque = max(self.proximo_desembarque, minimo)

    def _sortear(self, faixa, mult=1.0):
        return int(self.novo_cooldown(*faixa) * self.fase_cfg.mult_cooldown * mult)

    # ------------------------------------------------------------ canhão de foco
    @property
    def torreta_dy(self):
        return TORRETA_SENTADO_DY if self.pose == 'sentado' else 0

    @property
    def ponta_canhao(self):
        """De onde o feixe sai: a ponta do cano, para o lado em que ele aponta."""
        sentido = 1 if self.mira_torreta == 'right' else -1
        x = pivo_torreta(self.animador.lado) + sentido * (PONTA_CANHAO[0] - PIVO_TORRETA)
        meio = self.rect.width / 2
        return V2(self.posicao.x + x - meio,
                  self.posicao.y + PONTA_CANHAO[1] - meio + self.torreta_dy - self.impulso_y)

    def mirar_torreta(self):
        """O canhão gira sozinho para o lado do alvo (o casco demora)."""
        alvo_x = self.feixe.mira_atual.x if self.feixe_estado == 'disparo' else self.jogador.posicao.x
        dx = alvo_x - self.posicao.x
        if abs(dx) > HISTERESE_MIRA:
            self.mira_torreta = 'right' if dx > 0 else 'left'

    def atualizar_feixe(self, agora, delta_time):
        cfg = CFG.feixe
        if not self.em_repouso or self.feixe_estado != 'espera':
            self.mirar_torreta()
        if self.feixe_estado == 'espera':
            perto = self.contexto.dist_sq <= cfg.alcance ** 2
            if perto and agora >= self.proximo_feixe:
                self.feixe_estado = 'carga'
                self.feixe_fim = agora + cfg.carga_ms
        elif self.feixe_estado == 'carga':
            self.tremer(cfg.shake_carga, 100)
            if agora >= self.feixe_fim:
                self.feixe_estado = 'disparo'
                self.feixe_fim = agora + cfg.duracao_ms
                self.feixe.suavizacao = cfg.suavizacao_critica if self.critico else cfg.suavizacao
                self.feixe.comecar()
        else:
            self.tremer(cfg.shake, 100)
            self.feixe.update(delta_time, self.jogador.posicao)
            if agora >= self.feixe_fim:
                self.feixe_estado = 'espera'
                self.proximo_feixe = agora + self._sortear(cfg.cooldown_ms)

    # ------------------------------------------------------------ torreta de plasma
    def atualizar_torreta(self, agora):
        mult = CFG.torreta_mult_critica if self.critico else 1.0
        if self.tiros_restantes > 0:
            if agora >= self.proximo_tiro:
                self.plasma_array()
                self.tiros_restantes -= 1
                self.proximo_tiro = agora + CFG.torreta_intervalo_ms * mult
                if self.tiros_restantes == 0:
                    minimo, maximo = CFG.torreta_cooldown_ms
                    self.proxima_rajada = agora + int(self.novo_cooldown(minimo, maximo) * mult)
        elif agora >= self.proxima_rajada and self.contexto.dist_sq <= CFG.torreta_alcance ** 2:
            self.tiros_restantes = CFG.torreta_tiros
            self.proximo_tiro = agora

    def plasma_array(self):
        for canhao in CFG.torreta_canhoes:
            origem = self.posicao + V2(canhao)
            PlasmaGun(
                posicao_inicial=origem,
                grupos=(entity_manager.all_sprites,),
                jogador=self.jogador,
                game=self.game,
                dono='INIMIGO', fonte=self,
                tamanho=CFG.torreta_tamanho,      # plasma pesado
                dano=CFG.torreta_dano,
                velocidade=CFG.torreta_velocidade,
                direcao_spread=direcao_segura(origem, self.jogador.posicao),
                vai_rotacionar=True,
            )

    # ------------------------------------------------------------ desembarque
    def atualizar_desembarque(self, agora):
        if self.desembarque_em_curso is not None:
            self.efeito_da_escotilha()
            if agora >= self.desembarque_em_curso:
                self.desembarque_em_curso = None
                self.desembarcar()
            return
        if agora < self.proximo_desembarque:
            return
        self.proximo_desembarque = agora + self._sortear(CFG.desembarque_ms)
        self.guarnicao = [i for i in self.guarnicao if i.alive()]
        if len(self.guarnicao) + CFG.desembarque_qtd[0] <= CFG.desembarque_max_vivos:
            self.desembarque_em_curso = agora + CFG.desembarque_aviso_ms

    def desembarcar(self):
        """Grupos pelas duas escotilhas; cada um pode soltar um orbe de vida."""
        vagas = CFG.desembarque_max_vivos - len(self.guarnicao)
        nomes = list(CFG.desembarque_pesos)
        pesos = list(CFG.desembarque_pesos.values())
        for i in range(min(vagas, random.randint(*CFG.desembarque_qtd))):
            classe = GUARNICAO[random.choices(nomes, weights=pesos)[0]]
            inimigo = classe(posicao=self._ponto_de_desembarque(i), game=self.game)
            inimigo.tabela_drop = {**inimigo.tabela_drop, 'life_orb': (1, CFG.desembarque_life_orb, 100)}
            self.efeito_do_desembarque(inimigo.posicao)
            self.guarnicao.append(inimigo)

    def _ponto_de_desembarque(self, indice):
        """Perto de uma escotilha; fora da arena (ele anda por cima dos prédios), perto do jogador."""
        base = self.no_mundo(ESCOTILHAS[indice % len(ESCOTILHAS)])
        for tentativa in range(16):
            centro, raio = (base, 110) if tentativa < 6 else (self.jogador.posicao, 420)
            ponto = centro + V2(random.uniform(0.3, 1) * raio, 0).rotate(random.uniform(0, 360))
            if self.verificar_posicao_valida(ponto):
                return ponto
        return V2(self.jogador.posicao)
