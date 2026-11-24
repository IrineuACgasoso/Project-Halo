"""GameClock, paths, vetores e geometria de colisão com paredes."""
import math
import os
import random
import sys

import pygame
import pytest

from source.systems.gameclock import (
    AcumuladorPassoFixo, MAX_PASSOS_POR_FRAME,
)
from source.utils.collision_utils import empurrao_do_segmento
from source.utils.paths import path
from source.utils.vetores import direcao_segura, no_cone

V = pygame.math.Vector2


# ── GameClock ────────────────────────────────────────────────────────────────


def test_relogio_congela_fora_do_estado_jogando(novo_jogo):
    from source.systems.gameclock import relogio
    novo_jogo.mudar_estado('pausa')
    antes = relogio.agora()
    novo_jogo.update(0.5)
    assert relogio.agora() == antes


# ── AcumuladorPassoFixo (roteiro B1) ─────────────────────────────────────────


def test_passo_fixo_acumula_frames_curtos():
    # 144 FPS: ~6,9 ms por frame; a soma vira passos sem perder tempo
    a = AcumuladorPassoFixo()
    total = sum(a.passos(1 / 144) for _ in range(144))
    assert total in (59, 60)


def test_passo_fixo_frame_lento_tem_no_maximo_cinco_passos():
    a = AcumuladorPassoFixo()
    assert a.passos(3 / 60) == 3
    assert a.passos(2.0) == MAX_PASSOS_POR_FRAME == 5


def test_passo_fixo_nao_entra_em_espiral_depois_de_engasgo():
    # o atraso que passou do teto é descartado: o frame seguinte normal volta a dar 1 passo
    a = AcumuladorPassoFixo()
    a.passos(10.0)
    assert a.acumulado == 0
    assert a.passos(1 / 60) == 1


# ── paths ────────────────────────────────────────────────────────────────────


def test_path_usa_meipass_dentro_do_executavel(monkeypatch):
    monkeypatch.setattr(sys, '_MEIPASS', 'C:/bundle', raising=False)
    assert path('assets', 'x.png') == os.path.join('C:/bundle', 'assets', 'x.png')


# ── vetores ──────────────────────────────────────────────────────────────────


def test_direcao_segura_pontos_iguais_devolve_padrao_sem_erro():
    assert direcao_segura((5, 5), (5, 5)) == V(1, 0)
    assert direcao_segura((5, 5), (5, 5), padrao=(0, -1)) == V(0, -1)


@pytest.mark.parametrize('graus', [5, 30, 45, 89, 90, 120, 179])
def test_no_cone_bate_com_o_angulo_calculado(graus):
    """Equivale a `ângulo(eixo, v) <= θ` pelo acos, para pontos sorteados (fora da borda exata)."""
    rnd = random.Random(graus)
    eixo = V(1, 0).rotate(rnd.uniform(0, 360))
    cos_meio = math.cos(math.radians(graus))
    for _ in range(500):
        p = V(rnd.uniform(-500, 500), rnd.uniform(-500, 500))
        angulo = eixo.angle_to(p) % 360
        angulo = min(angulo, 360 - angulo)
        if abs(angulo - graus) < 1e-6:
            continue
        assert no_cone((0, 0), eixo, p, cos_meio) is (angulo <= graus)


# ── empurrao_do_segmento ─────────────────────────────────────────────────────


def test_projecao_empurra_para_fora_ate_o_raio():
    dx, dy = empurrao_do_segmento(0, 10, -50, 0, 50, 0, raio=20)
    assert dx == 0
    assert 10 + dy == pytest.approx(20.1)


def test_projecao_segmento_degenerado_ignorado():
    assert empurrao_do_segmento(0, 0, 1, 1, 1, 1, raio=20) is None
