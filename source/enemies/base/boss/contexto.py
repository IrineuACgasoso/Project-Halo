"""ContextoCombate: a percepção do boss, calculada 1× por frame no início do update e lida por
todas as decisões (plano_bosses §2, princípio 2)."""
import math

import pygame

VELOCIDADE_MAX_SQ = 4000 ** 2   # acima disso (px/s) foi teleporte ou dash: não entra na média
SUAVIZACAO = 0.25               # peso da amostra nova na média da velocidade do jogador


class ContextoCombate:
    def __init__(self, pos_jogador):
        self.dist_sq = 0.0
        self.razao_vida = 1.0
        self.vel_jogador = pygame.math.Vector2()
        self._pos_jogador_ant = pygame.math.Vector2(pos_jogador)

    @property
    def dist(self):
        return math.sqrt(self.dist_sq)

    def atualizar(self, boss, dt):
        pos = boss.jogador.posicao
        if dt > 1e-4:
            v = (pos - self._pos_jogador_ant) / dt
            if v.length_squared() < VELOCIDADE_MAX_SQ:
                self.vel_jogador = self.vel_jogador.lerp(v, SUAVIZACAO)
        self._pos_jogador_ant.update(pos)
        self.dist_sq = boss.posicao.distance_squared_to(pos)
        self.razao_vida = boss.vida / boss.vida_maxima if boss.vida_maxima > 0 else 1.0
