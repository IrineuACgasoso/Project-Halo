"""GameClock, paths, vetores e geometria de colisão com paredes."""
import os
import sys

import pygame
import pytest

from source.systems.gameclock import (
    AcumuladorPassoFixo, GameClock, MAX_PASSOS_POR_FRAME, PASSO_FIXO, _OFFSET_INICIAL_MS,
)
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


# ── AcumuladorPassoFixo (roteiro B1) ─────────────────────────────────────────
def test_passo_fixo_frame_de_60fps_da_um_passo():
    a = AcumuladorPassoFixo()
    assert [a.passos(1 / 60) for _ in range(120)] == [1] * 120


def test_passo_fixo_acumula_frames_curtos():
    # 144 FPS: ~6,9 ms por frame; a soma vira passos sem perder tempo
    a = AcumuladorPassoFixo()
    total = sum(a.passos(1 / 144) for _ in range(144))
    assert total in (59, 60)


def test_passo_fixo_tick_em_ms_inteiros_nao_perde_nem_ganha_tempo():
    # clock.tick devolve ms inteiros (16, 17, 17...): em 6 s de jogo saem 360 passos (±1)
    a = AcumuladorPassoFixo()
    ticks = [16, 17, 17] * 120
    assert abs(sum(a.passos(ms / 1000) for ms in ticks) - 360) <= 1


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


def test_passo_fixo_dt_zero_ou_negativo_nao_gera_passo():
    a = AcumuladorPassoFixo()
    assert a.passos(0) == 0
    assert a.passos(-1.0) == 0
    assert a.acumulado == 0


@pytest.mark.parametrize('passo, max_passos', [(0, 5), (-1 / 60, 5), (1 / 60, 0)])
def test_passo_fixo_parametros_invalidos(passo, max_passos):
    with pytest.raises(ValueError):
        AcumuladorPassoFixo(passo, max_passos)


class _RelogioFalso:
    """Substitui pygame.time.Clock: devolve ms pré-definidos e encerra o loop no fim."""
    def __init__(self, game, ticks_ms):
        self.game, self.ticks = game, list(ticks_ms)

    def tick(self, _fps):
        ms = self.ticks.pop(0)
        if not self.ticks:
            self.game.running = False
        return ms


def test_game_run_usa_passo_fixo_e_um_draw_por_frame(game, monkeypatch):
    chamadas = []
    monkeypatch.setattr(game, 'eventos', lambda: chamadas.append('eventos'))
    monkeypatch.setattr(game, 'update', lambda dt: chamadas.append(dt))
    monkeypatch.setattr(game, 'draw', lambda: chamadas.append('draw'))
    monkeypatch.setattr(game, 'clock', _RelogioFalso(game, [17, 10, 1000]))
    monkeypatch.setattr(game, 'running', True)
    game.run()
    passo = PASSO_FIXO
    assert chamadas == [
        'eventos', passo, 'draw',                       # 17 ms: 1 passo, sobra ~0,3 ms
        'eventos', 'draw',                              # 10 ms: ainda não completa um passo
        'eventos', passo, passo, passo, passo, passo, 'draw',   # engasgo de 1 s: teto de 5
    ]


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
