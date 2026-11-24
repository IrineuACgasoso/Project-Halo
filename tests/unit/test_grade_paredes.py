"""Grade espacial de paredes: a consulta nunca esquece um segmento no raio."""
import math
import random

import pygame
import pytest

from source.systems.mapmanager import Mapa
from source.systems.mapmanager.grade_paredes import MARGEM_GRADE, TAMANHO_CELULA, GradeParedes
from source.utils.paths import path

V = pygame.math.Vector2


def _parede(*pontos):
    return {'tipo': 'linha', 'pontos': [V(p) for p in pontos]}


def _distancia(x, y, seg):
    _, x1, y1, x2, y2 = seg
    ax, ay = x2 - x1, y2 - y1
    t = max(0.0, min(1.0, ((x - x1) * ax + (y - y1) * ay) / (ax * ax + ay * ay)))
    return math.hypot(x - (x1 + t * ax), y - (y1 + t * ay))


# ── Montagem ─────────────────────────────────────────────────────────────────


def test_mapa_carregado_ja_tem_a_grade():
    mapa = Mapa(path('assets', 'img', 'map', '0', 'm0.tmj'), 0)
    pares = [(a, b) for p in mapa.paredes for a, b in zip(p['pontos'], p['pontos'][1:])]
    assert len(mapa.grade_paredes.segmentos) == sum(a != b for a, b in pares)   # o m0 tem 16 degenerados


# ── Consulta ─────────────────────────────────────────────────────────────────


def test_coordenadas_negativas_e_borda_de_celula():
    grade = GradeParedes([_parede((-10, -300), (-10, 300))])
    assert grade.perto(-5, 0, 15)
    assert grade.perto(0.0, 0.0, 15)                       # exatamente na borda entre 4 células
    assert grade.perto(TAMANHO_CELULA * -1.0, 0.0, 15)


@pytest.mark.parametrize('raio', [15, 48, MARGEM_GRADE, 100, 300])
def test_perto_nunca_esquece_segmento_dentro_do_raio(raio):
    """Propriedade da grade: todo segmento a menos de `raio` da posição está na resposta."""
    rnd = random.Random(raio)
    paredes = [_parede(*[(rnd.uniform(-500, 2500), rnd.uniform(-500, 2500)) for _ in range(rnd.randint(2, 5))])
               for _ in range(40)]
    grade = GradeParedes(paredes)
    for _ in range(2000):
        x, y = rnd.uniform(-600, 2600), rnd.uniform(-600, 2600)
        resposta = {s[0] for s in grade.perto(x, y, raio)}
        perto_de_fato = {s[0] for s in grade.segmentos if _distancia(x, y, s) < raio}
        assert perto_de_fato <= resposta
