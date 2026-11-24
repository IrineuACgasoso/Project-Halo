"""Blocos de habilidade reutilizáveis (`source/feats/skills/`): dash, ataque retangular e o gancho `ao_explodir`."""

import pygame
import pytest

from helpers import DT
from source.enemies.standard.grunt import GruntRed
from source.feats.skills.artilharia import ArtilhariaAviso
from source.feats.skills.dash import Dash, DashConfig
from source.feats.skills.rect_strike import RectStrikeAviso, RectStrikeConfig
from source.systems.dano import AREA, Dano
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.systems.mapmanager.grade_paredes import GradeParedes

V = pygame.math.Vector2


def _grunt(game, posicao=V(1000, 1000)):
    return GruntRed(posicao=V(posicao), game=game)


def _correr(dash, segundos, paredes=None):
    """Passos de DT até o dash acabar ou o tempo passar; devolve quantos passos deu."""
    for passo in range(1, round(segundos / DT) + 1):
        relogio.avancar(DT)
        if dash.atualizar(DT, paredes):
            return passo
    return None


# ── Dash ─────────────────────────────────────────────────────────────────────


def test_dash_ate_o_alvo_para_no_ponto_travado(novo_jogo):
    grunt = _grunt(novo_jogo)
    dash = Dash(grunt, V(1000, 1200), config=DashConfig(velocidade=600, duracao_ms=5000, ate_o_alvo=True))
    passos = _correr(dash, 5)
    assert passos == 20                                  # 200 px a 600 px/s = 1/3 s
    assert tuple(grunt.posicao) == pytest.approx((1000, 1200))


def test_dash_nao_atravessa_parede(novo_jogo):
    grunt = _grunt(novo_jogo)
    paredes = GradeParedes([{'tipo': 'linha', 'pontos': [V(1150, 800), V(1150, 1200)]}])
    dash = Dash(grunt, V(2000, 1000), preset='hunter')
    _correr(dash, 3, paredes)
    assert grunt.posicao.x <= 1150 - grunt.raio_colisao_mapa + 1e-6


@pytest.mark.parametrize('velocidade', [900, 1500, 3000])
def test_dash_rapido_nao_pula_a_parede(novo_jogo, velocidade):
    """Um passo maior que o raio de colisão (15 px) jogava o centro para o outro lado da linha."""
    grunt = _grunt(novo_jogo)
    paredes = GradeParedes([{'tipo': 'linha', 'pontos': [V(1150, 800), V(1150, 1200)]}])
    dash = Dash(grunt, V(2000, 1000), config=DashConfig(velocidade=velocidade, duracao_ms=1000))
    _correr(dash, 2, paredes)
    assert grunt.posicao.x < 1150


def test_dash_com_alvo_na_propria_posicao_nao_quebra(novo_jogo):
    grunt = _grunt(novo_jogo)
    dash = Dash(grunt, grunt.posicao, config=DashConfig(velocidade=600, duracao_ms=100, ate_o_alvo=True))
    assert dash.atualizar(DT) is True
    assert tuple(grunt.posicao) == pytest.approx((1000, 1000))


# ── ao_explodir ──────────────────────────────────────────────────────────────
def _avancar_com_update(sprite, segundos):
    for _ in range(round(segundos / DT)):
        relogio.avancar(DT)
        if sprite.alive():
            sprite.update(DT)


def test_artilharia_chama_ao_explodir_uma_vez_na_explosao(novo_jogo):
    chamadas = []
    aviso = ArtilhariaAviso(V(5000, 5000), (entity_manager.all_sprites,), novo_jogo, preset='hunter_cannon',
                            ao_explodir=chamadas.append)
    _avancar_com_update(aviso, 0.5)
    assert chamadas == []                                # o preset demora 600 ms
    _avancar_com_update(aviso, 1)
    assert chamadas == [aviso]


# ── Ataque retangular ────────────────────────────────────────────────────────
CFG_RET = RectStrikeConfig(dano=40, largura=60, altura=300, duracao=500)


def _retangulo(game, posicao=V(1000, 1000), direcao=V(1, 0), **kwargs):
    return RectStrikeAviso(V(posicao), direcao, (entity_manager.all_sprites,), game,
                           **{'custom_config': CFG_RET, **kwargs})


@pytest.mark.parametrize('deslocamento, atinge', [
    (V(0, 0), True), (V(150, 0), True), (V(300, 0), True), (V(150, 29), True),
    (V(150, 31), False),       # esquiva lateral
    (V(301, 0), False), (V(-5, 0), False),
])
def test_retangulo_golpeia_so_quem_esta_dentro_no_fim_do_aviso(novo_jogo, deslocamento, atinge):
    p = novo_jogo.player
    boss = _grunt(novo_jogo)
    p.posicao.update(V(1000, 1000) + deslocamento)
    recebidos = []
    p.receber_dano = recebidos.append
    aviso = _retangulo(novo_jogo, dono='INIMIGO', fonte=boss)
    _avancar_com_update(aviso, 0.45)
    assert recebidos == []                                # só no fim do aviso
    _avancar_com_update(aviso, 0.1)
    esperado = [Dano(40, AREA, boss, ignora_iframes=True)] if atinge else []
    assert recebidos == esperado
    _avancar_com_update(aviso, 0.5)
    assert recebidos == esperado and not aviso.alive()    # 1 golpe só, e o clarão some


def test_retangulo_do_jogador_acerta_os_inimigos(novo_jogo):
    dentro, fora = _grunt(novo_jogo, V(1200, 1000)), _grunt(novo_jogo, V(1200, 1100))
    vidas = dentro.vida, fora.vida
    _avancar_com_update(_retangulo(novo_jogo, dono='PLAYER'), 0.6)
    assert dentro.vida == max(0, vidas[0] - 40) and fora.vida == vidas[1]


def test_retangulo_normaliza_a_direcao_e_nao_quebra_com_vetor_nulo(novo_jogo):
    assert _retangulo(novo_jogo, direcao=V(0, 50)).direcao == V(0, 1)
    assert _retangulo(novo_jogo, direcao=V(0, 0)).direcao == V(1, 0)
