"""Grade espacial de paredes (roteiro C1): consulta por posição e equivalência com o empurrão antigo."""
import math
import random

import pygame
import pytest

from source.systems.mapmanager import Mapa
from source.systems.mapmanager.grade_paredes import MARGEM_GRADE, TAMANHO_CELULA, GradeParedes
from source.utils.collision_utils import sair_das_paredes
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
def test_segmentos_viram_tuplas_de_float_na_ordem_do_mapa():
    grade = GradeParedes([_parede((0, 0), (100, 0), (100, 50)), _parede((300, 300), (400, 300))])
    assert grade.segmentos == ((0, 0.0, 0.0, 100.0, 0.0), (1, 100.0, 0.0, 100.0, 50.0),
                               (2, 300.0, 300.0, 400.0, 300.0))
    assert all(type(v) is float for seg in grade.segmentos for v in seg[1:])


def test_segmento_degenerado_fica_de_fora():
    grade = GradeParedes([_parede((5, 5), (5, 5), (50, 5))])
    assert [s[1:] for s in grade.segmentos] == [(5.0, 5.0, 50.0, 5.0)]


def test_mapa_sem_paredes_nao_devolve_nada():
    grade = GradeParedes([])
    assert grade.perto(0, 0, 15) == ()
    assert grade.perto(0, 0, MARGEM_GRADE + 100) == []


@pytest.mark.parametrize('celula, margem', [(0, 64), (-128, 64), (128, -1)])
def test_parametros_invalidos(celula, margem):
    with pytest.raises(ValueError):
        GradeParedes([], celula, margem)


def test_mapa_carregado_ja_tem_a_grade():
    mapa = Mapa(path('assets', 'img', 'map', '0', 'm0.tmj'), 0)
    pares = [(a, b) for p in mapa.paredes for a, b in zip(p['pontos'], p['pontos'][1:])]
    assert len(mapa.grade_paredes.segmentos) == sum(a != b for a, b in pares)   # o m0 tem 16 degenerados


# ── Consulta ─────────────────────────────────────────────────────────────────
def test_perto_devolve_parede_proxima_e_nada_longe():
    grade = GradeParedes([_parede((100, 0), (100, 200))])
    assert len(grade.perto(110, 100, 15)) == 1
    assert grade.perto(5000, 5000, 15) == ()


def test_consulta_de_celula_unica_nao_aloca():
    grade = GradeParedes([_parede((100, 0), (100, 200))])
    assert grade.perto(110, 100, 15) is grade.perto(120, 90, 15)   # a mesma tupla guardada


def test_coordenadas_negativas_e_borda_de_celula():
    grade = GradeParedes([_parede((-10, -300), (-10, 300))])
    assert grade.perto(-5, 0, 15)
    assert grade.perto(0.0, 0.0, 15)                       # exatamente na borda entre 4 células
    assert grade.perto(TAMANHO_CELULA * -1.0, 0.0, 15)


def test_raio_maior_que_a_margem_junta_celulas_sem_repetir_e_em_ordem():
    paredes = [_parede((0, 0), (1000, 0)), _parede((0, 300), (1000, 300)), _parede((0, 150), (1000, 150))]
    grade = GradeParedes(paredes)
    achados = grade.perto(500, 150, 200)
    assert [s[0] for s in achados] == [0, 1, 2]


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


# ── Equivalência com o código antigo ─────────────────────────────────────────
def _projetar_antigo(pos_player, p1, p2, raio):
    """Cópia literal de `projetar_fora_da_linha` (removida na C1), a referência da equivalência."""
    aresta = p2 - p1
    if aresta.length_squared() == 0:
        return None
    t = max(0, min(1, (pos_player - p1).dot(aresta) / aresta.length_squared()))
    ponto_mais_proximo = p1 + t * aresta
    diff = pos_player - ponto_mais_proximo
    distancia = diff.length()
    if distancia < raio:
        if distancia == 0:
            return pygame.math.Vector2(0, -1) * raio
        push_mag = raio - distancia + 0.1
        return diff.normalize() * push_mag
    return None


def _colisao_antiga(posicao, paredes, raio, iteracoes):
    """O laço antigo de `aplicar_colisao_mapa`/`mover_com_colisao`, sobre uma lista de paredes."""
    for _ in range(iteracoes):
        for parede in paredes:
            pontos = parede['pontos']
            for i in range(len(pontos) - 1):
                push = _projetar_antigo(posicao, pontos[i], pontos[i + 1], raio)
                if push:
                    posicao += push


@pytest.mark.parametrize('raio, iteracoes', [(15, 2), (48, 3)], ids=['inimigo', 'jogador'])
def test_empurrao_novo_igual_ao_antigo_em_10_mil_posicoes(raio, iteracoes):
    """Mapa real da fase 0. O código antigo recebe TODAS as paredes (a parede relevante sempre está
    na lista); o novo só as da grade. Metade das posições é sorteada colada numa parede."""
    mapa = Mapa(path('assets', 'img', 'map', '0', 'm0.tmj'), 0)
    rnd = random.Random(2026)
    segs = mapa.grade_paredes.segmentos
    empurradas = 0
    for i in range(10_000):
        if i % 2:
            _, x1, y1, x2, y2 = rnd.choice(segs)
            t = rnd.random()
            pos = (x1 + t * (x2 - x1) + rnd.uniform(-raio, raio), y1 + t * (y2 - y1) + rnd.uniform(-raio, raio))
        else:
            pos = (rnd.uniform(0, mapa.largura_mapa_pixels), rnd.uniform(0, mapa.altura_mapa_pixels))
        antigo, novo = V(pos), V(pos)
        _colisao_antiga(antigo, mapa.paredes, raio, iteracoes)
        sair_das_paredes(novo, raio, mapa.grade_paredes, iteracoes)
        assert novo == antigo, f'posição {pos}: antigo {antigo}, novo {novo}'
        empurradas += novo != V(pos)
    assert empurradas > 2000   # o teste exercita o empurrão, não só posições livres


def test_sair_das_paredes_altera_o_vetor_no_lugar():
    grade = GradeParedes([_parede((-50, 0), (50, 0))])
    posicao = V(0, 10)
    mesmo = posicao
    sair_das_paredes(posicao, 20, grade, 2)
    assert mesmo is posicao and posicao.y == pytest.approx(20.1)
