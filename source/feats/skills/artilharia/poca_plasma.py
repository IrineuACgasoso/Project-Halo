import math
import random

import pygame
from source.feats.assets import ASSETS
from source.feats.particulas import emitir, emitir_leque, imagem_pixel
from source.systems.gameclock import relogio
from source.utils.superficies import camada_alpha
from .core import ArtilhariaAviso

# Quentes primeiro: o respingo da explosão usa todas, o vapor só as frias
CORES_PLASMA = ((246, 255, 205), (205, 255, 105), (120, 245, 55), (45, 200, 45))
CORES_VAPOR = CORES_PLASMA[2:]

_QUADROS = {}   # raio -> quadros da poça no diâmetro certo


def quadros_da_poca(raio):
    """Quadros da poça (ASSETS['effects']['fuel_rod_area']) no diâmetro de `raio`, em cache."""
    quadros = _QUADROS.get(raio)
    if quadros is None:
        quadros = _QUADROS[raio] = [pygame.transform.scale(q, (raio * 2, raio * 2))
                                    for q in ASSETS['effects']['fuel_rod_area']]
    return quadros


class PocaDePlasma(ArtilhariaAviso):
    """Área do Fuel Rod. O efeito é o da artilharia (impacto + queimadura); muda o que se vê: clarão,
    respingo e uma poça de plasma fervendo, que solta vapor e esfria no fim."""

    MS_POR_QUADRO = 90
    MS_CLARAO = 220
    MS_ESFRIANDO = 700
    MS_ENTRE_VAPORES = 110
    RESPINGOS = 26

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._proximo_vapor = 0

    def update(self, delta_time, paredes=None):
        estava_ativa = self.dot_ativo
        super().update(delta_time, paredes)
        if not self.dot_ativo:
            return
        # O Renderer ordena pelo rect: a poça fica no chão, por baixo de quem está dentro dela
        self.rect.center = (round(self.posicao.x), round(self.posicao.y - self.cfg.raio_explosao))
        if not estava_ativa:   # acabou de explodir
            emitir_leque(self.posicao, (1, 0), self.RESPINGOS, CORES_PLASMA, (4, 6, 8),
                         velocidade=(120, 420), duracao_ms=(300, 650))
        agora = relogio.agora()
        if agora >= self._proximo_vapor:
            self._proximo_vapor = agora + self.MS_ENTRE_VAPORES
            self._soltar_vapor()

    def _soltar_vapor(self):
        distancia = math.sqrt(random.random()) * self.cfg.raio_explosao * 0.8
        ponto = self.posicao + pygame.math.Vector2(distancia, 0).rotate(random.uniform(0, 360))
        imagem = imagem_pixel(random.choice(CORES_VAPOR), random.choice((4, 6)))
        emitir(ponto, imagem, (random.uniform(-12, 12), random.uniform(-70, -35)), random.uniform(500, 900))

    def alpha_da_poca(self, agora):
        restante = self.cfg.duracao_dot - (agora - self.dot_inicio)
        return round(255 * max(0.0, min(1.0, restante / self.MS_ESFRIANDO)))

    def draw(self, surface, offset):
        if not self.dot_ativo:
            super().draw(surface, offset)
            return
        agora = relogio.agora()
        idade = agora - self.dot_inicio
        raio = self.cfg.raio_explosao
        quadros = quadros_da_poca(raio)
        quadro = quadros[int(idade // self.MS_POR_QUADRO) % len(quadros)]
        quadro.set_alpha(self.alpha_da_poca(agora))   # superfície compartilhada: alpha antes de cada blit
        centro = self.posicao - offset
        surface.blit(quadro, (round(centro.x) - raio, round(centro.y) - raio))
        if idade < self.MS_CLARAO:
            self._desenhar_clarao(surface, centro, raio, idade / self.MS_CLARAO)

    def _desenhar_clarao(self, surface, centro, raio, progresso):
        x, y = round(centro.x), round(centro.y)
        camada, area = camada_alpha(surface, (x - raio, y - raio, raio * 2, raio * 2))
        if camada is None:
            return
        forca = 1 - progresso
        r, g, b, a = self.cfg.cor_explosao
        pygame.draw.circle(camada, (r, g, b, round(a * forca)), (x, y), round(raio * (0.55 + 0.45 * progresso)))
        pygame.draw.circle(camada, (255, 255, 240, round(255 * forca)), (x, y), max(1, round(raio * 0.5 * forca)))
        surface.blit(camada, area.topleft, area)
