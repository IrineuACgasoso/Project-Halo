"""Movimentos do Guilty: a ronda (passeio por caminhos que passam perto do jogador) e o teleporte."""
import random

import pygame

from source.utils.vetores import direcao_segura

from .config import CFG
from .vfx import TeleporteVFX

V2 = pygame.math.Vector2


class GuiltyMovement:
    def _parar(self):
        self.velocidade = 0

    def _esperar(self, ms):
        """Sub-rotina: `ms` de tempo de jogo parado."""
        fim = self._agora + ms
        while self._agora < fim:
            self._parar()
            yield

    # ------------------------------------------------------------ ronda
    def rondar(self, agora, delta_time):
        """Um frame de passeio, em linha reta até o destino sorteado."""
        self._medir_travamento(delta_time)
        travado = self._travado_ms >= CFG.travado_ms
        if (travado or agora >= self.ronda_ate
                or self.posicao.distance_squared_to(self.ronda_destino) < CFG.ronda_chegou ** 2):
            self.ronda_destino = self._sortear_destino(qualquer_rumo=travado)
            self.ronda_ate = agora + CFG.ronda_max_ms
            self._travado_ms = 0.0
        self.ronda_direcao = direcao_segura(self.posicao, self.ronda_destino)
        self._ir(self.ronda_direcao, self.fator_de_ronda)

    @property
    def fator_de_ronda(self):
        return CFG.mult_sem_barreira if self.fase == 1 and not self.barreira_ativa else 1.0

    def _medir_travamento(self, delta_time):
        """Andou bem menos que devia desde o último frame de ronda (parede)?"""
        andou = self.posicao.distance_to(self._pos_ronda)
        self._pos_ronda.update(self.posicao)
        esperado = self.velocidade_base * self.fase_cfg.mult_velocidade * self.fator_de_ronda * delta_time
        self._travado_ms = self._travado_ms + delta_time * 1000 if andou < esperado * 0.3 else 0.0

    def _sortear_destino(self, qualquer_rumo=False):
        """Um ponto além do jogador, num caminho que passa a até `ronda_desvio` de onde ele está agora.
        `qualquer_rumo` (preso numa parede): uma direção qualquer."""
        jogador = self.jogador.posicao
        for _ in range(CFG.ronda_tentativas):
            if qualquer_rumo:
                passagem = self.posicao
                rumo = V2(1, 0).rotate(random.uniform(0, 360))
            else:
                para = direcao_segura(self.posicao, jogador)
                lateral = random.uniform(-CFG.ronda_desvio, CFG.ronda_desvio)
                passagem = jogador + V2(-para.y, para.x) * lateral
                rumo = direcao_segura(self.posicao, passagem)
            destino = passagem + rumo * random.uniform(*CFG.ronda_alem)
            if self.verificar_posicao_valida(destino):
                return destino
        return V2(jogador)      # cercado de pontos inválidos: até o jogador sempre dá

    def orientar(self):
        """Passeando, olha para onde vai; atacando, para o jogador."""
        if self.rotina is None:
            self.set_sprite_direction(self.ronda_direcao.x)
        else:
            super().orientar()

    # ------------------------------------------------------------ teleporte
    def ponto_de_teleporte(self):
        """Um ponto válido em volta do jogador (ou onde ele já está, se não houver)."""
        for _ in range(CFG.tp_tentativas):
            ponto = self.jogador.posicao + V2(random.uniform(*CFG.tp_raio), 0).rotate(random.uniform(0, 360))
            if self.verificar_posicao_valida(ponto):
                return ponto
        return V2(self.posicao)

    def _teleportar(self):
        """Sub-rotina: some num lugar e aparece em outro. Fora do mundo até aparecer."""
        try:
            TeleporteVFX(self.posicao)
            self.em_teleporte = True
            yield from self._esmaecer(255, 0)
            self.posicao.update(self.ponto_de_teleporte())
            self.sync_rect()
            TeleporteVFX(self.posicao)
            yield from self._esmaecer(0, 255)
        finally:
            self.em_teleporte = False
            self._aplicar_alpha(255)

    def _esmaecer(self, de, ate):
        inicio = self._agora
        while self._agora - inicio < CFG.tp_fade_ms:
            t = (self._agora - inicio) / CFG.tp_fade_ms
            self._aplicar_alpha(de + (ate - de) * t)
            self._parar()
            yield
        self._aplicar_alpha(ate)
