"""Blocos de habilidade reutilizáveis (`source/feats/skills/`): dash e o gancho `ao_explodir`."""
import pygame
import pytest

from helpers import DT
from source.enemies.standard.grunt import GruntRed
from source.feats.skills.artilharia import ArtilhariaAviso
from source.feats.skills.cone_strike import ConeStrikeAviso
from source.feats.skills.dash import DASH_PRESETS, Dash, DashConfig
from source.feats.skills.mortar import CanhaoParabolico
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.systems.mapmanager.grade_paredes import GradeParedes
from source.systems.status import BuffVelocidade, aplicar

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
def test_dash_sem_parar_no_alvo_corre_o_tempo_todo_na_direcao_travada(novo_jogo):
    grunt = _grunt(novo_jogo)
    alvo = V(1100, 1000)
    dash = Dash(grunt, alvo, config=DashConfig(velocidade=600, duracao_ms=500))
    alvo.update(0, 0)                                    # mexer no original não muda o dash
    passos = _correr(dash, 2)
    assert passos == 30                                  # 0,5 s
    assert grunt.posicao.x == pytest.approx(1300) and grunt.posicao.y == pytest.approx(1000)
    assert grunt.rect.center == (1300, 1000)


def test_dash_ate_o_alvo_para_no_ponto_travado(novo_jogo):
    grunt = _grunt(novo_jogo)
    dash = Dash(grunt, V(1000, 1200), config=DashConfig(velocidade=600, duracao_ms=5000, ate_o_alvo=True))
    passos = _correr(dash, 5)
    assert passos == 20                                  # 200 px a 600 px/s = 1/3 s
    assert tuple(grunt.posicao) == pytest.approx((1000, 1200))


def test_dash_ate_o_alvo_longe_para_no_fim_do_tempo(novo_jogo):
    grunt = _grunt(novo_jogo)
    dash = Dash(grunt, V(5000, 1000), config=DashConfig(velocidade=600, duracao_ms=500, ate_o_alvo=True))
    assert _correr(dash, 2) == 30
    assert grunt.posicao.x == pytest.approx(1300)


def test_dash_acabado_nao_anda_mais(novo_jogo):
    grunt = _grunt(novo_jogo)
    dash = Dash(grunt, V(1100, 1000), config=DashConfig(velocidade=600, duracao_ms=100))
    _correr(dash, 1)
    antes = V(grunt.posicao)
    assert dash.atualizar(DT) is True and grunt.posicao == antes


def test_dash_respeita_o_multiplicador_de_velocidade(novo_jogo):
    grunt = _grunt(novo_jogo)
    aplicar(grunt, BuffVelocidade(0.5))
    dash = Dash(grunt, V(2000, 1000), config=DashConfig(velocidade=400, duracao_ms=500))
    _correr(dash, 1)
    assert grunt.posicao.x == pytest.approx(1000 + 400 * 1.5 * 0.5)


def test_dash_nao_atravessa_parede(novo_jogo):
    grunt = _grunt(novo_jogo)
    paredes = GradeParedes([{'tipo': 'linha', 'pontos': [V(1150, 800), V(1150, 1200)]}])
    dash = Dash(grunt, V(2000, 1000), preset='hunter')
    _correr(dash, 3, paredes)
    assert grunt.posicao.x <= 1150 - grunt.raio_colisao_mapa + 1e-6


def test_dash_com_alvo_na_propria_posicao_nao_quebra(novo_jogo):
    grunt = _grunt(novo_jogo)
    dash = Dash(grunt, grunt.posicao, config=DashConfig(velocidade=600, duracao_ms=100, ate_o_alvo=True))
    assert dash.atualizar(DT) is True
    assert tuple(grunt.posicao) == pytest.approx((1000, 1000))


def test_dash_preset_desconhecido_e_config_invalida():
    with pytest.raises(KeyError):
        Dash(None, (0, 0), preset='nao_existe')
    for kwargs in ({'velocidade': 0, 'duracao_ms': 100}, {'velocidade': 100, 'duracao_ms': -1},
                   {'velocidade': float('nan'), 'duracao_ms': 100}, {'velocidade': 1, 'duracao_ms': float('inf')}):
        with pytest.raises(ValueError):
            DashConfig(**kwargs)


def test_presets_de_dash_sao_validos_e_imutaveis():
    assert 'padrao' in DASH_PRESETS and 'hunter' in DASH_PRESETS
    with pytest.raises(AttributeError):
        DASH_PRESETS['padrao'].velocidade = 1


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


def test_cone_chama_ao_explodir_uma_vez_quando_o_golpe_sai(novo_jogo):
    chamadas = []
    cone = ConeStrikeAviso(V(5000, 5000), V(1, 0), (entity_manager.all_sprites,), novo_jogo,
                           preset='padrao', ao_explodir=chamadas.append)
    _avancar_com_update(cone, 1.1)
    assert chamadas == []                                # o preset demora 1200 ms
    _avancar_com_update(cone, 1)
    assert chamadas == [cone]


def test_canhao_repassa_ao_explodir_para_a_artilharia_do_impacto(novo_jogo):
    chamadas = []
    canhao = CanhaoParabolico(V(5000, 5000), V(5200, 5000), novo_jogo, dono='INIMIGO',
                              preset_artilharia='hunter_cannon', ao_explodir=chamadas.append)
    _avancar_com_update(canhao, 0.6)                     # 200 px a 400 px/s: pousou
    avisos = [s for s in entity_manager.all_sprites if isinstance(s, ArtilhariaAviso)]
    assert len(avisos) == 1 and chamadas == []
    _avancar_com_update(avisos[0], 1)
    assert chamadas == avisos


def test_sem_ao_explodir_nada_muda(novo_jogo):
    aviso = ArtilhariaAviso(V(5000, 5000), (entity_manager.all_sprites,), novo_jogo)
    cone = ConeStrikeAviso(V(5000, 5000), V(1, 0), (entity_manager.all_sprites,), novo_jogo)
    _avancar_com_update(aviso, 2)
    _avancar_com_update(cone, 2)
    assert aviso.explodiu and cone.explodiu
