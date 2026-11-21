"""GameClock, paths, vetores e geometria de colisão com paredes."""
import os
import sys

import pygame
import pytest

from source.systems.gameclock import GameClock, _OFFSET_INICIAL_MS
from source.utils.collision_utils import projetar_fora_da_linha
from source.utils.paths import path
from source.utils.vetores import direcao_segura

V = pygame.math.Vector2


# ── GameClock ────────────────────────────────────────────────────────────────
def test_relogio_comeca_no_offset_para_cooldowns_prontos():
    assert GameClock().agora() == _OFFSET_INICIAL_MS


def test_relogio_avanca_em_ms_a_partir_de_dt_em_segundos():
    r = GameClock()
    r.avancar(0.5)
    r.avancar(0.25)
    assert r.agora() == _OFFSET_INICIAL_MS + 750


def test_relogio_acumula_fracoes_sem_perder_precisao():
    r = GameClock()
    for _ in range(60):
        r.avancar(1 / 60)
    assert r.agora() in (_OFFSET_INICIAL_MS + 999, _OFFSET_INICIAL_MS + 1000)


def test_relogio_congela_fora_do_estado_jogando(novo_jogo):
    from source.systems.gameclock import relogio
    novo_jogo.estado_do_jogo = 'pausa'
    antes = relogio.agora()
    novo_jogo.update(0.5)
    assert relogio.agora() == antes


# ── paths ────────────────────────────────────────────────────────────────────
def test_path_relativo_ao_cwd():
    assert path('assets', 'img') == os.path.join(os.path.abspath('.'), 'assets', 'img')


def test_path_usa_meipass_dentro_do_executavel(monkeypatch):
    monkeypatch.setattr(sys, '_MEIPASS', 'C:/bundle', raising=False)
    assert path('assets', 'x.png') == os.path.join('C:/bundle', 'assets', 'x.png')


# ── vetores ──────────────────────────────────────────────────────────────────
def test_direcao_segura_normaliza():
    d = direcao_segura((0, 0), (10, 0))
    assert d == V(1, 0)


def test_direcao_segura_pontos_iguais_devolve_padrao_sem_erro():
    assert direcao_segura((5, 5), (5, 5)) == V(1, 0)
    assert direcao_segura((5, 5), (5, 5), padrao=(0, -1)) == V(0, -1)


# ── projetar_fora_da_linha ───────────────────────────────────────────────────
def test_projecao_longe_da_linha_nao_empurra():
    assert projetar_fora_da_linha(V(0, 100), V(-50, 0), V(50, 0), raio=20) is None


def test_projecao_empurra_para_fora_ate_o_raio():
    pos = V(0, 10)
    push = projetar_fora_da_linha(pos, V(-50, 0), V(50, 0), raio=20)
    assert push is not None
    assert (pos + push).y == pytest.approx(20.1)


def test_projecao_usa_extremidade_do_segmento():
    # ponto além de p2: o mais próximo é o próprio p2
    push = projetar_fora_da_linha(V(55, 0), V(-50, 0), V(50, 0), raio=10)
    assert push.x > 0 and push.y == 0


def test_projecao_sobre_a_linha_empurra_para_cima():
    push = projetar_fora_da_linha(V(0, 0), V(-50, 0), V(50, 0), raio=20)
    assert push == V(0, -20)


def test_projecao_segmento_degenerado_ignorado():
    assert projetar_fora_da_linha(V(0, 0), V(1, 1), V(1, 1), raio=20) is None
