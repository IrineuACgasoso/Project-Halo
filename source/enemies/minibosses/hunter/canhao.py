"""O tiro do canhão do Hunter, desenhado em código: uma bola de plasma verde (halo que pulsa, núcleo
branco) em arco, com a sombra no chão encolhendo enquanto ela sobe e um rastro de plasma que fica no ar.
Ao cair vira um `AvisoPlasma` com o preset `hunter_cannon` (anéis no aviso, explosão em camadas verde e
plasma lento). Acerto, arco e dano continuam os do `CanhaoParabolico`.

Só visual: o rastro usa sorteio próprio e as imagens são pintadas 1× (cache)."""
import math
import random
from functools import lru_cache

import pygame

from source.feats.particulas import emitir_leque, preparar
from source.feats.skills.artilharia import AvisoPlasma
from source.feats.skills.artilharia.plasma import EXPLOSAO_PLASMA_PRESETS
from source.feats.skills.mortar import CanhaoParabolico
from source.systems.gameclock import relogio
from source.utils.superficies import camada_alpha

QUADROS_ORBE = 4
QUADRO_MS = 60
CORES_RASTRO = ((60, 230, 80), (130, 255, 110), (200, 255, 170), (30, 170, 60))
# (cor, escala do raio), de fora para dentro
CAMADAS_ORBE = (((35, 190, 45), 1.0), ((100, 250, 80), 0.8), ((190, 255, 160), 0.55), ((255, 255, 240), 0.3))
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


def _pintar_halo(surf, centro, raio, cor, alpha_max, degraus=7):
    """Brilho redondo com alpha: de quase nada na borda a `alpha_max` no centro (de fora para dentro)."""
    for i in range(degraus, 0, -1):
        fracao = i / degraus
        alpha = round(alpha_max * ((1 - fracao) ** 1.6 + 0.12))
        pygame.draw.circle(surf, (*cor, min(255, alpha)), centro, max(1.0, raio * fracao))


@lru_cache(maxsize=None)
def quadros_do_orbe(raio):
    """A bola de plasma em QUADROS_ORBE pulsos (halo e núcleo crescem e voltam)."""
    quadros = []
    for q in range(QUADROS_ORBE):
        pulso = 1 + 0.14 * math.sin(q * 2 * math.pi / QUADROS_ORBE)
        halo = raio * 2.1 * pulso
        lado = round(halo * 2) + 4
        surf = pygame.Surface((lado, lado), pygame.SRCALPHA)
        centro = (lado / 2, lado / 2)
        _pintar_halo(surf, centro, halo, (90, 255, 70), 140)
        for cor, escala in CAMADAS_ORBE:
            fator = pulso if escala < 0.6 else 1.0
            pygame.draw.circle(surf, (*cor, 255), centro, raio * escala * fator)
        pygame.draw.circle(surf, (255, 255, 255, 230), (centro[0] - raio * 0.3, centro[1] - raio * 0.32), raio * 0.17)
        quadros.append(surf)
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
            pygame.draw.ellipse(camada, (5, 35, 10, round(150 - 80 * subida)), caixa)
            pygame.draw.ellipse(camada, (60, 230, 80, round(70 - 40 * subida)), caixa.inflate(-largura, -altura))
            surface.blit(camada, area.topleft, area)
        quadro = self._quadros[int(relogio.agora() // QUADRO_MS) % QUADROS_ORBE]
        surface.blit(quadro, quadro.get_rect(center=(self.rect.centerx - offset.x, self.rect.centery - offset.y)))
