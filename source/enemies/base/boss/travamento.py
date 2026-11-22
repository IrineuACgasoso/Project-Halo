"""Anti-stuck por CAMINHO percorrido (não deslocamento líquido: dava falso positivo quando o
strafe invertia de lado)."""
import math
from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class ConfigTravamento:
    janela_ms: int        # de quanto em quanto tempo o caminho é conferido
    caminho_min: float    # andou menos que isso (px) na janela, livre de rotina = travado...
    dist_min: float       # ...se estiver mais longe do jogador que isso (px)

    def __post_init__(self):
        for campo in ('janela_ms', 'caminho_min', 'dist_min'):
            valor = getattr(self, campo)
            if not (isinstance(valor, (int, float)) and math.isfinite(valor) and valor > 0):
                raise ValueError(f'ConfigTravamento.{campo} {valor!r} (precisa ser > 0 e finito)')


class DetectorTravamento:
    def __init__(self, config, agora, posicao):
        self.config = config
        self._dist_min_sq = config.dist_min ** 2
        self.ultimo_check = agora
        self.caminho = 0.0
        self._pos_ant = pygame.math.Vector2(posicao)

    def registrar(self, posicao, livre):
        """1× por frame, com a posição já resolvida contra as paredes. Só conta o caminho feito
        livre (fora de rotina): teleporte e investida não mascaram um travamento."""
        if livre:
            self.caminho += posicao.distance_to(self._pos_ant)
        self._pos_ant.update(posicao)

    def resetar(self, agora):
        self.ultimo_check = agora
        self.caminho = 0.0

    def travou(self, agora, dist_sq):
        """Confere no fim de cada janela (e recomeça a contagem): quase parado e longe do jogador."""
        if agora - self.ultimo_check <= self.config.janela_ms:
            return False
        caminho = self.caminho
        self.resetar(agora)
        return caminho < self.config.caminho_min and dist_sq > self._dist_min_sq
