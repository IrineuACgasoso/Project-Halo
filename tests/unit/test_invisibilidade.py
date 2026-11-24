"""Skill de invisibilidade (`feats/skills/invisibilidade`): fases, tempos, alpha, encerrar e clarão."""
import math
import pathlib

import pygame
import pytest

from helpers import DT
from source.enemies.standard.elite import Elite
from source.enemies.standard.grunt import GruntRed
from source.feats.skills.invisibilidade import (FADE_IN, FADE_OUT, INVISIBILIDADE_PRESETS, OCULTO,
                                                Invisibilidade, InvisibilidadeConfig)

V = pygame.math.Vector2
RAIZ = pathlib.Path(__file__).resolve().parents[2]


@pytest.fixture
def grunt(novo_jogo):
    g = GruntRed(posicao=novo_jogo.player.posicao + V(300, 0), game=novo_jogo)
    g.invencivel = False
    return g


def _com(grunt, **kwargs):
    grunt.invisibilidade = Invisibilidade(grunt, config=InvisibilidadeConfig(**kwargs))
    return grunt.invisibilidade


def _passar(grunt, ms):
    for _ in range(round(ms / (DT * 1000))):
        grunt.atualizar_invisibilidade(DT)


# ── Fases e tempos ───────────────────────────────────────────────────────────
def test_duracao_nao_conta_os_fades(grunt):
    """Fade out 500 + 1000 invisível + fade in 250: cada fase dura o que o parâmetro diz."""
    inv = _com(grunt, fade_out_ms=500, duracao_ms=1000, fade_in_ms=250)
    quadros = {FADE_OUT: 0, OCULTO: 0, FADE_IN: 0}
    for _ in range(1000):
        quadros[inv.fase] += 1
        grunt.atualizar_invisibilidade(DT)
        if grunt.invisibilidade is None:
            break
    ms = {fase: n * DT * 1000 for fase, n in quadros.items()}
    assert ms[FADE_OUT] == pytest.approx(500, abs=20)
    assert ms[OCULTO] == pytest.approx(1000, abs=20)
    assert ms[FADE_IN] == pytest.approx(250, abs=20)


def test_alpha_desce_fica_em_zero_e_volta(grunt):
    inv = _com(grunt, fade_out_ms=500, duracao_ms=500, fade_in_ms=500)
    assert grunt.alpha_atual == 255 and inv.intensidade == 0
    _passar(grunt, 250)
    assert grunt.alpha_atual == pytest.approx(127, abs=3) and inv.intensidade == pytest.approx(0.5, abs=0.01)
    _passar(grunt, 300)
    assert inv.fase == OCULTO and grunt.alpha_atual == 0 and grunt.image.get_alpha() == 0
    assert inv.intensidade == 1
    _passar(grunt, 700)
    assert inv.fase == FADE_IN and 0 < grunt.alpha_atual < 255
    _passar(grunt, 400)
    assert grunt.invisibilidade is None and grunt.alpha_atual == 255 and grunt.image.get_alpha() == 255


def test_so_o_fade_in_pode_ser_mirado(grunt):
    inv = _com(grunt, fade_out_ms=100, duracao_ms=100, fade_in_ms=200)
    vistos = {}
    while grunt.invisibilidade is not None:
        vistos.setdefault(inv.fase, set()).add(grunt.alvejavel)
        grunt.atualizar_invisibilidade(DT)
    assert vistos[FADE_OUT] == {False} and vistos[OCULTO] == {False}
    assert True in vistos[FADE_IN]
    assert grunt.alvejavel


def test_sem_duracao_fica_oculto_ate_encerrar(grunt):
    inv = _com(grunt, fade_out_ms=100, duracao_ms=None, fade_in_ms=100)
    _passar(grunt, 60_000)
    assert inv.fase == OCULTO
    grunt.encerrar_invisibilidade()
    assert inv.fase == FADE_IN
    _passar(grunt, 150)
    assert grunt.invisibilidade is None and grunt.alpha_atual == 255


def test_encerrar_no_meio_do_fade_out_volta_do_alpha_em_que_estava(grunt):
    inv = _com(grunt, fade_out_ms=1000, duracao_ms=1000, fade_in_ms=1000)
    _passar(grunt, 500)
    alpha = grunt.alpha_atual
    grunt.encerrar_invisibilidade()
    _passar(grunt, DT * 1000)
    assert inv.fase == FADE_IN and alpha <= grunt.alpha_atual <= alpha + 5   # sem piscar para 0
    assert grunt.alvejavel


def test_encerrar_de_novo_nao_reinicia_o_fade_in(grunt):
    _com(grunt, fade_out_ms=100, duracao_ms=100, fade_in_ms=500)
    _passar(grunt, 400)
    alpha = grunt.alpha_atual
    for _ in range(5):
        grunt.encerrar_invisibilidade()
        _passar(grunt, DT * 1000)
    assert grunt.alpha_atual > alpha


def test_visivel_nada_acontece(grunt):
    grunt.atualizar_invisibilidade(DT)
    grunt.encerrar_invisibilidade()
    grunt.trigger_flash()
    assert grunt.invisibilidade is None and grunt.fase_invisibilidade is None and grunt.alpha_atual == 255


def test_iniciar_de_novo_recomeca(grunt):
    grunt.iniciar_invisibilidade('padrao')
    _passar(grunt, 1000)
    grunt.iniciar_invisibilidade('padrao')
    assert grunt.fase_invisibilidade == FADE_OUT and grunt.alpha_atual == 255


# ── Clarão ───────────────────────────────────────────────────────────────────
def test_clarao_mostra_por_um_instante_sem_virar_alvo(grunt):
    inv = _com(grunt, fade_out_ms=100, duracao_ms=5000, fade_in_ms=100)
    _passar(grunt, 200)
    assert grunt.alpha_atual == 0
    grunt.trigger_flash(100, 60)
    _passar(grunt, DT * 1000)
    assert grunt.alpha_atual == 60 and inv.revelada and not grunt.alvejavel
    assert inv.intensidade == 1            # a distorção não muda com o clarão
    _passar(grunt, 200)
    assert grunt.alpha_atual == 0 and not inv.revelada


# ── Presets e config ─────────────────────────────────────────────────────────
@pytest.mark.parametrize('campos', [
    dict(fade_out_ms=0, duracao_ms=100, fade_in_ms=100), dict(fade_out_ms=100, duracao_ms=100, fade_in_ms=0),
    dict(fade_out_ms=100, duracao_ms=-1, fade_in_ms=100), dict(fade_out_ms=math.nan, duracao_ms=1, fade_in_ms=1),
    dict(fade_out_ms=1, duracao_ms=math.inf, fade_in_ms=1),
])
def test_config_invalida(campos):
    with pytest.raises(ValueError):
        InvisibilidadeConfig(**campos)


def test_preset_desconhecido(grunt):
    with pytest.raises(KeyError):
        grunt.iniciar_invisibilidade('nao_existe')


def test_presets_imutaveis():
    with pytest.raises(AttributeError):
        INVISIBILIDADE_PRESETS['padrao'].duracao_ms = 1


def test_elite_ferido_usa_a_skill(novo_jogo):
    elite = Elite(posicao=novo_jogo.player.posicao + V(500, 0), game=novo_jogo)
    elite.vida = elite.vida_base / 2
    elite.update(DT)
    assert elite.invisibilidade.cfg is INVISIBILIDADE_PRESETS['elite']


def test_a_maquina_antiga_saiu_do_codigo():
    """Um lugar só para a camuflagem: ninguém mexe em `invis_*` por fora da skill."""
    usos = [c.relative_to(RAIZ).as_posix() for c in (RAIZ / 'source').rglob('*.py')
            if 'invis_phase' in c.read_text(encoding='utf-8')]
    assert usos == []
