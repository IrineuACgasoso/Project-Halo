"""Blocos de habilidade reutilizáveis (`source/feats/skills/`): dash, ataque retangular e o gancho `ao_explodir`."""
import math

import pygame
import pytest

from helpers import DT, contar_alocacoes
from source.enemies.standard.grunt import GruntRed
from source.feats.skills.artilharia import ArtilhariaAviso
from source.feats.skills.cone_strike import ConeStrikeAviso
from source.feats.skills.dash import DASH_PRESETS, Dash, DashConfig
from source.feats.skills.mortar import CanhaoParabolico
from source.feats.skills.rect_strike import RECT_STRIKE_PRESETS, RectStrikeAviso, RectStrikeConfig
from source.systems.dano import AREA, Dano
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.systems.mapmanager.grade_paredes import GradeParedes
from source.systems.status import BuffVelocidade, aplicar
from source.utils.vetores import no_retangulo

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


@pytest.mark.parametrize('velocidade', [900, 1500, 3000])
def test_dash_rapido_nao_pula_a_parede(novo_jogo, velocidade):
    """Um passo maior que o raio de colisão (15 px) jogava o centro para o outro lado da linha."""
    grunt = _grunt(novo_jogo)
    paredes = GradeParedes([{'tipo': 'linha', 'pontos': [V(1150, 800), V(1150, 1200)]}])
    dash = Dash(grunt, V(2000, 1000), config=DashConfig(velocidade=velocidade, duracao_ms=1000))
    _correr(dash, 2, paredes)
    assert grunt.posicao.x < 1150


def test_dash_rapido_sem_parede_no_caminho_anda_o_mesmo(novo_jogo):
    """Os subpassos não mudam a distância."""
    grunt = _grunt(novo_jogo)
    paredes = GradeParedes([{'tipo': 'linha', 'pontos': [V(9000, 800), V(9000, 1200)]}])
    dash = Dash(grunt, V(5000, 1000), config=DashConfig(velocidade=1500, duracao_ms=500))
    _correr(dash, 1, paredes)
    assert grunt.posicao.x == pytest.approx(1750)


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


# ── Ataque retangular ────────────────────────────────────────────────────────
CFG_RET = RectStrikeConfig(dano=40, largura=60, altura=300, duracao=500)


def _retangulo(game, posicao=V(1000, 1000), direcao=V(1, 0), **kwargs):
    return RectStrikeAviso(V(posicao), direcao, (entity_manager.all_sprites,), game,
                           **{'custom_config': CFG_RET, **kwargs})


@pytest.mark.parametrize('graus', [0, 30, 90, 135, 210, 300])
def test_no_retangulo_bate_com_a_rotacao_calculada(graus):
    """Equivalência com desfazer a rotação por trigonometria."""
    eixo = V(1, 0).rotate(graus)
    origem = V(50, -20)
    for x in range(-400, 401, 23):
        for y in range(-400, 401, 29):
            local = (V(x, y) - origem).rotate(-graus)
            if min(abs(local.x), abs(local.x - 300), abs(abs(local.y) - 30)) < 1e-6:
                continue                                  # em cima da borda: arredondamento
            esperado = 0 <= local.x <= 300 and abs(local.y) <= 30
            assert no_retangulo(origem, eixo, (x, y), 300, 30) is esperado


def test_bordas_do_retangulo_contam():
    for ponto in [(0, 0), (300, 0), (0, 30), (300, -30)]:
        assert no_retangulo((0, 0), (1, 0), ponto, 300, 30)
    for ponto in [(-0.1, 0), (300.1, 0), (10, 30.1), (10, -30.1)]:
        assert not no_retangulo((0, 0), (1, 0), ponto, 300, 30)


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


def test_retangulo_chama_ao_explodir_uma_vez(novo_jogo):
    chamadas = []
    aviso = _retangulo(novo_jogo, ao_explodir=chamadas.append)
    _avancar_com_update(aviso, 0.4)
    assert chamadas == []
    _avancar_com_update(aviso, 1)
    assert chamadas == [aviso]


def _pintar(aviso, offset=V(850, 850)):
    tela = pygame.Surface((800, 800))
    tela.fill((128, 128, 128))
    aviso.draw(tela, offset)
    return tela


@pytest.mark.parametrize('direcao', [V(1, 0), V(-1, 0), V(0, 1), V(0, -1), V(1, 1), V(-2, 1)])
def test_retangulo_enche_do_dono_para_a_ponta(novo_jogo, direcao):
    """Na metade do aviso: escuro do lado do dono, claro do lado da ponta; a borda é a mais escura."""
    aviso = _retangulo(novo_jogo, posicao=V(1250, 1250), direcao=direcao)
    relogio.avancar(0.25)
    tela = _pintar(aviso)
    centro, eixo = V(400, 400), direcao.normalize()

    def brilho(avanco, lado=0.0):
        ponto = centro + eixo * avanco + V(-eixo.y, eixo.x) * lado
        return sum(tela.get_at((round(ponto.x), round(ponto.y)))[:3])

    perto, longe, fora, borda = brilho(75), brilho(225), brilho(75, 60), brilho(225, 30)
    assert perto < longe                                  # preenchido é mais escuro
    assert longe > fora                                   # o fundo é mais claro que o chão
    assert borda < longe                                  # contorno escuro
    assert brilho(140) < brilho(160)                      # a frente está na metade (150 px)


def test_retangulo_enche_por_completo_e_brilha_no_golpe(novo_jogo):
    aviso = _retangulo(novo_jogo, posicao=V(1250, 1250))
    relogio.avancar(0.499)
    assert aviso.progresso == pytest.approx(0.998, abs=1e-3)
    cheio = _pintar(aviso).get_at((690, 400))[:3]
    relogio.avancar(0.01)
    aviso.update(DT)
    assert aviso.explodiu and aviso.progresso == 1
    assert sum(_pintar(aviso).get_at((690, 400))[:3]) > sum(cheio)


@pytest.mark.parametrize('offset', [V(850, 850), V(1240, 1240), V(1600, 1250), V(9000, 9000)])
def test_retangulo_desenha_na_borda_e_fora_da_tela_sem_alocar(novo_jogo, offset):
    aviso = _retangulo(novo_jogo, posicao=V(1250, 1250), direcao=V(1, 1))
    tela = pygame.Surface((800, 800))
    aviso.draw(tela, offset)
    with contar_alocacoes() as c:
        for _ in range(10):
            aviso.draw(tela, offset)
    assert c.total == 0


@pytest.mark.parametrize('campos', [{'largura': 0}, {'altura': -1}, {'duracao': 0}, {'dano': -1},
                                    {'dano': math.nan}, {'altura': math.inf}, {'duracao': math.nan}])
def test_config_do_retangulo_invalida(campos):
    with pytest.raises(ValueError):
        RectStrikeConfig(**campos)


def test_preset_de_retangulo_desconhecido_e_imutavel(novo_jogo):
    with pytest.raises(KeyError):
        _retangulo(novo_jogo, custom_config=None, preset='nao_existe')
    with pytest.raises(AttributeError):
        RECT_STRIKE_PRESETS['padrao'].dano = 1
