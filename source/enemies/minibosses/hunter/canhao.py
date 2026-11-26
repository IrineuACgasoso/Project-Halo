"""O tiro do canhão do Hunter, desenhado em código na paleta da `PlasmaGun` (verde-limão): uma bola de
energia em camadas com núcleo branco, fios de plasma girando em volta e um halo somado na tela que pulsa.
Voa em arco, com a sombra no chão encolhendo enquanto sobe e um rastro de plasma que fica no ar. Ao cair
vira um `AvisoPlasma` com o preset `hunter_cannon` (mesma paleta). Acerto, arco e dano continuam os do
`CanhaoParabolico`.

Só visual: o rastro usa sorteio próprio e as imagens são pintadas 1× (cache)."""
import math
import random
from functools import lru_cache

import pygame

from source.feats.particulas import emitir_leque, preparar
from source.feats.projetil import PlasmaGun
from source.feats.projetil.desenhado import brilho_aditivo
from source.feats.skills.artilharia import AvisoPlasma
from source.feats.skills.artilharia.plasma import EXPLOSAO_PLASMA_PRESETS
from source.feats.skills.mortar import CanhaoParabolico
from source.systems.gameclock import relogio
from source.utils.superficies import camada_alpha

QUADROS_ORBE = 8
QUADRO_MS = 45
FIOS = 3                  # fios de plasma girando em volta da bola
COR_FIO = (215, 255, 120)
CORES_RASTRO = ((110, 255, 30), (170, 255, 0), (215, 255, 120), (250, 255, 230))
TAMANHOS_RASTRO = (4, 6, 8)
_SORTEIO = random.Random()


def preparar_canhao(preset):
    """No spawn do Hunter: a bola, o rastro e as partículas da explosão do `preset` já pintados."""
    quadros_do_orbe(CanhaoDoHunter.RAIO_ORBE)
    preparar(CORES_RASTRO, TAMANHOS_RASTRO)
    vfx = EXPLOSAO_PLASMA_PRESETS[preset]
    for cores, tamanhos in ((vfx.cores_faisca, vfx.tamanhos_faisca), (vfx.cores_gota, vfx.tamanhos_gota),
                            (vfx.cores_lenta, vfx.tamanhos_lenta)):
        preparar(cores, tamanhos)


def _degrade(camadas, passos=5):
    """As camadas `(cor, alpha, escala)` da `PlasmaGun` com `passos` degraus entre cada par (bola lisa)."""
    saida = []
    for (c0, a0, e0), (c1, a1, e1) in zip(camadas, camadas[1:]):
        for i in range(passos):
            t = i / passos
            saida.append((tuple(round(x + (y - x) * t) for x, y in zip(c0, c1)), round(a0 + (a1 - a0) * t),
                          e0 + (e1 - e0) * t))
    saida.append(camadas[-1])
    return saida


def _fios(surf, cx, cy, raio, fase, cor, alpha, espessura):
    """FIOS cometas de plasma girando em volta da bola: cabeça forte, cauda que afina."""
    for k in range(FIOS):
        inicio = (fase + k / FIOS) * 2 * math.pi
        distancia = raio * (1.1 + 0.15 * math.sin(inicio * 3))
        for i in range(11, -1, -1):                                 # da cauda para a cabeça
            t = i / 11
            ang = inicio - t * 1.4
            ponto = (cx + math.cos(ang) * distancia, cy + math.sin(ang) * distancia)
            if alpha is None:
                pygame.draw.circle(surf, [round(c * (1 - t)) for c in cor], ponto, max(1.0, espessura * (1 - t * 0.6)))
            else:
                pygame.draw.circle(surf, (*cor, round(alpha * (1 - t) ** 1.2)), ponto, max(1.0, espessura * (1 - t * 0.6)))


@lru_cache(maxsize=None)
def quadros_do_orbe(raio):
    """QUADROS_ORBE pares (corpo SRCALPHA, brilho sem alpha para somar): as camadas da `PlasmaGun` em bola
    lisa, núcleo que pulsa, fios de plasma que giram uma volta por ciclo e halo que respira."""
    camadas = _degrade(PlasmaGun.CAMADAS)
    quadros = []
    for q in range(QUADROS_ORBE):
        fase = q / QUADROS_ORBE
        onda = math.sin(fase * 2 * math.pi * 2)                    # dois pulsos por volta dos fios
        pulso = 1 + 0.12 * onda
        lado = round(raio * 1.7 * 2) + 4
        corpo = pygame.Surface((lado, lado), pygame.SRCALPHA)
        cx = cy = lado / 2
        for cor, alpha, escala in camadas:
            fator = pulso if escala < 0.75 else 1.0
            pygame.draw.circle(corpo, (*cor, alpha), (cx, cy), raio * escala * fator)
        pygame.draw.circle(corpo, (255, 255, 255, 255), (cx, cy), raio * 0.24 * pulso)
        fios = pygame.Surface((lado, lado), pygame.SRCALPHA)        # à parte: o alpha da cauda mistura
        _fios(fios, cx, cy, raio, fase, COR_FIO, 255, 4.0)
        corpo.blit(fios, (0, 0))
        halo = raio * 2.6 * pulso
        lado_brilho = round(raio * 2.6 * 1.12 * 2) + 2
        brilho = brilho_aditivo(halo, PlasmaGun.COR_HALO, forca=0.8 + 0.2 * onda, lado=lado_brilho)
        c = lado_brilho / 2
        _fios(brilho, c, c, raio, fase, (120, 200, 40), None, 6.0)    # os fios também acendem a tela
        quadros.append((corpo, brilho))
    return tuple(quadros)


class CanhaoDoHunter(CanhaoParabolico):
    CLASSE_AVISO = AvisoPlasma
    RAIO_ORBE = 22
    RASTRO_MS = 28           # de quanto em quanto tempo solta plasma no rastro

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._quadros = quadros_do_orbe(self.RAIO_ORBE)
        self._altura = 0.0
        self._proximo_rastro = 0

    def update(self, delta_time):
        super().update(delta_time)
        if not self.alive():
            return
        self._altura = max(0.0, self.posicao.y - self.rect.centery)
        agora = relogio.agora()
        if agora >= self._proximo_rastro:
            self._proximo_rastro = agora + self.RASTRO_MS
            emitir_leque(self.rect.center, -self.direcao, 3, CORES_RASTRO, TAMANHOS_RASTRO, 80, (15, 70), (320, 600),
                         gravidade=-30, sorteio=_SORTEIO)

    def draw(self, surface, offset):
        # Sombra no chão (a posição sem a altura): menor e mais fraca quanto mais alto
        subida = min(1.0, self._altura / self.max_height) if self.max_height > 0 else 0.0
        largura = round(self.RAIO_ORBE * (2.4 - 1.2 * subida))
        altura = max(2, round(largura * 0.4))
        x, y = round(self.posicao.x - offset.x), round(self.posicao.y - offset.y)
        caixa = pygame.Rect(x - largura, y - altura, largura * 2, altura * 2)
        camada, area = camada_alpha(surface, caixa)
        if camada is not None:
            pygame.draw.ellipse(camada, (10, 35, 0, round(150 - 80 * subida)), caixa)
            pygame.draw.ellipse(camada, (*PlasmaGun.COR_HALO, round(80 - 45 * subida)), caixa.inflate(-largura, -altura))
            surface.blit(camada, area.topleft, area)
        corpo, brilho = self._quadros[int(relogio.agora() // QUADRO_MS) % QUADROS_ORBE]
        centro = (self.rect.centerx - offset.x, self.rect.centery - offset.y)
        surface.blit(corpo, corpo.get_rect(center=centro))
        surface.blit(brilho, brilho.get_rect(center=centro), special_flags=pygame.BLEND_RGB_ADD)
