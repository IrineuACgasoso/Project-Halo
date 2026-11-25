"""Disparo que cai do céu no ponto de uma artilharia do bombardeio (ex.: o canhão de plasma do Phantom).

Só visual: o dano é da artilharia. Nasce junto com ela, aparece `queda_ms` antes da explosão e chega
no ponto no instante em que ela estoura, sempre vindo do mesmo lado (a nave parada no céu). Desenhado
direto na tela com cores opacas (sem Surface por frame); fica no grupo das partículas (teto global,
fora das contagens da simulação) e por cima de tudo. Faíscas do impacto com sorteio próprio."""
import random
from dataclasses import dataclass
from typing import Tuple

import pygame

from source.feats.particulas import emitir_leque
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.utils.superficies import SUPERFICIE_VAZIA

Cor = Tuple[int, int, int]
_SORTEIO = random.Random()


@dataclass(frozen=True)
class DisparoConfig:
    queda_ms: int = 280                       # tempo de voo visível até o ponto
    vindo_de: Tuple[float, float] = (0.4, -1.0)   # de onde vem (direção a partir do ponto)
    distancia: float = 900                    # px: de quão longe ele começa
    comprimento: float = 170                  # px: rastro atrás da cabeça
    # camadas de fora para dentro: cor, largura do rastro, fração do comprimento, raio da cabeça
    camadas: Tuple[Tuple[Cor, int, float, int], ...] = (
        ((110, 60, 220), 24, 1.0, 15),
        ((180, 130, 255), 15, 0.75, 10),
        ((250, 245, 255), 7, 0.45, 5),
    )
    faiscas: int = 10
    cores_faisca: Tuple[Cor, ...] = ((170, 110, 255), (215, 190, 255), (250, 245, 255))


DISPARO_PRESETS = {
    # Canhão de plasma do Phantom (bombardeio do Arbiter): roxo-azulado do plasma Covenant
    'phantom': DisparoConfig(),
}


class DisparoCaindo(pygame.sprite.Sprite):
    y_desenho = float('inf')      # o tiro vem do céu: por cima de quem estiver no chão

    def __init__(self, alvo, chegada_ms, preset='phantom'):
        super().__init__(entity_manager.all_sprites, entity_manager.particulas_grupo)
        self.cfg = DISPARO_PRESETS[preset]
        self.alvo = pygame.math.Vector2(alvo)
        self.chegada = chegada_ms
        self.inicio = chegada_ms - self.cfg.queda_ms
        self.vindo_de = pygame.math.Vector2(self.cfg.vindo_de).normalize()
        self.origem = self.alvo + self.vindo_de * self.cfg.distancia
        self.image = SUPERFICIE_VAZIA
        self.rect = self.image.get_rect(center=(round(self.alvo.x), round(self.alvo.y)))

    def update(self, delta_time, paredes=None):
        if relogio.agora() >= self.chegada:
            cfg = self.cfg
            emitir_leque(self.alvo, self.vindo_de, cfg.faiscas, cfg.cores_faisca, (3, 4, 6), 160,
                         velocidade=(120, 320), duracao_ms=(220, 420), sorteio=_SORTEIO)
            self.kill()

    def draw(self, surface, offset):
        agora = relogio.agora()
        if agora < self.inicio:
            return
        cfg = self.cfg
        progresso = min(1.0, (agora - self.inicio) / cfg.queda_ms)
        cabeca = self.origem.lerp(self.alvo, progresso) - offset
        lado = pygame.math.Vector2(-self.vindo_de.y, self.vindo_de.x)
        for cor, largura, fracao, raio in cfg.camadas:     # rastro em cunha: largo na cabeça, ponta fina
            meia = lado * (largura / 2)
            pygame.draw.polygon(surface, cor, (cabeca + meia, cabeca - meia,
                                               cabeca + self.vindo_de * (cfg.comprimento * fracao)))
            pygame.draw.circle(surface, cor, cabeca, raio)
