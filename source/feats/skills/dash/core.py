"""Dash: investida em linha reta, reutilizável por qualquer inimigo.

No início trava a posição do alvo (ex.: o jogador naquele instante) e a direção até ela. Cada
`atualizar` anda `velocidade × mult_velocidade × dt` nessa direção e respeita as paredes. Com
`ate_o_alvo`, para ao alcançar o ponto travado (medido ao longo da direção: deslizar numa parede
não teleporta); sem ele, corre até o fim do tempo.

Uso numa rotina geradora:
    dash = Dash(self, self.jogador.posicao, preset='hunter')
    while not dash.atualizar(dt, paredes):
        yield
"""
import pygame

from source.utils.vetores import direcao_segura
from .config import DASH_PRESETS

_FOLGA = 1e-9   # s: soma de dt em float não fecha exata


class Dash:
    __slots__ = ('inimigo', 'cfg', 'alvo', 'direcao', 'restante', 'terminou')

    def __init__(self, inimigo, alvo, preset='padrao', config=None):
        if config is None and preset not in DASH_PRESETS:
            raise KeyError(f'preset de dash desconhecido: {preset!r}')
        self.inimigo = inimigo
        self.cfg = config if config is not None else DASH_PRESETS[preset]
        self.alvo = pygame.math.Vector2(alvo)                  # cópia: o alvo fica travado
        self.direcao = direcao_segura(inimigo.posicao, self.alvo)
        self.restante = self.cfg.duracao_ms / 1000
        self.terminou = False

    def atualizar(self, delta_time, paredes=None):
        """Um passo do dash. Devolve True quando acabou (e continua True nas chamadas seguintes)."""
        if self.terminou:
            return True
        inimigo = self.inimigo
        passo = min(delta_time, self.restante)
        distancia = self.cfg.velocidade * inimigo.status.mult_velocidade * passo
        if self.cfg.ate_o_alvo:
            falta = (self.alvo - inimigo.posicao).dot(self.direcao)   # ao longo da direção, sem raiz
            if falta <= distancia:
                distancia = max(falta, 0.0)
                self.terminou = True
        inimigo.posicao += self.direcao * distancia
        if paredes:
            inimigo.aplicar_colisao_mapa(paredes)
        inimigo.sync_rect()
        self.restante -= delta_time
        if self.restante <= _FOLGA:
            self.terminou = True
        return self.terminou
