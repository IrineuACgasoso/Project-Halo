"""Smoke tests: rodam o loop REAL (update + draw no driver dummy) e falham em qualquer exceção
ou erro engolido pelo Renderer. Pegam regressões de integração que testes unitários não veem."""
import random

import pytest

from helpers import simular, blindar_jogador, ir_para_fase
from source.feats.assets import ASSETS
from source.systems.entitymanager import entity_manager
from source.systems.levelup import ARMAS_REGISTRO
from source.systems.spawner.spawner_bosses import PHASE_BOSSES
from source.systems.spawner.spawner_pools import PHASE_POOLS

pytestmark = pytest.mark.integration

FASES_COM_MAPA = sorted(int(k) for k in ASSETS['maps'])


def _sem_erros_de_render(game):
    assert game.renderer._erros_logados == set()


@pytest.mark.parametrize('fase', FASES_COM_MAPA)
def test_mapas_reais_carregam_e_sao_jogaveis(novo_jogo, fase):
    ir_para_fase(novo_jogo, fase)
    mapa = novo_jogo.mapa
    assert mapa.paredes, 'mapa sem camada Colisoes'
    assert mapa.pontos_de_spawn, 'mapa sem SpawnPoints'
    spawn = mapa.get_player_spawn_pos()
    assert 0 <= spawn.x <= mapa.largura_mapa_pixels and 0 <= spawn.y <= mapa.altura_mapa_pixels


def test_partida_normal_dez_segundos(novo_jogo):
    blindar_jogador(novo_jogo.player)
    simular(novo_jogo, 10, desenhar_a_cada=30)
    assert novo_jogo.estado_do_jogo in ('jogando', 'level_up')
    assert len(entity_manager.inimigos_grupo) > 0
    _sem_erros_de_render(novo_jogo)


def _casos_inimigos():
    vistos = {}
    for fase, pool in sorted(PHASE_POOLS.items()):
        for classe in pool['classes']:
            vistos.setdefault(classe.__name__, (classe, fase))
    for nome, (classe, fase) in sorted(vistos.items()):
        yield pytest.param(classe, fase, id=nome)


@pytest.mark.parametrize('classe, fase', list(_casos_inimigos()))
def test_inimigo_comum_luta_por_oito_segundos(novo_jogo, classe, fase):
    ir_para_fase(novo_jogo, fase)
    blindar_jogador(novo_jogo.player)
    novo_jogo.spawner.update = lambda dt: None          # só o inimigo testado
    for i in range(3):
        classe(posicao=novo_jogo.mapa.pontos_de_spawn[i % len(novo_jogo.mapa.pontos_de_spawn)], game=novo_jogo)
    simular(novo_jogo, 8, desenhar_a_cada=30)
    _sem_erros_de_render(novo_jogo)


def _casos_bosses():
    for fase, bosses in sorted(PHASE_BOSSES.items()):
        for nome in bosses:
            yield pytest.param(nome, fase, id=nome)


@pytest.mark.parametrize('nome, fase', list(_casos_bosses()))
def test_boss_luta_por_quinze_segundos(novo_jogo, nome, fase):
    random.seed(fase)
    ir_para_fase(novo_jogo, fase)
    blindar_jogador(novo_jogo.player)
    novo_jogo.spawner.spawnar(nome)
    assert novo_jogo.sessao.boss_atual is not None
    simular(novo_jogo, 15, desenhar_a_cada=30)
    assert novo_jogo.estado_do_jogo == 'jogando'
    _sem_erros_de_render(novo_jogo)


@pytest.mark.parametrize('id_arma', sorted(ARMAS_REGISTRO))
def test_arma_no_nivel_maximo_em_combate(novo_jogo, id_arma):
    # Antes da E6: nível 10 para todas. Agora o máximo da raridade (5 a 25).
    blindar_jogador(novo_jogo.player)
    em = novo_jogo.event_manager
    maximo = ARMAS_REGISTRO[id_arma].nivel_maximo
    for _ in range(maximo):   # 1ª escolha equipa (nível 1), as demais sobem; laço com fim
        em._aplicar_escolha_de_upgrade(id_arma)
    simular(novo_jogo, 8, desenhar_a_cada=30)
    assert novo_jogo.player.armas[id_arma].nivel == maximo
    _sem_erros_de_render(novo_jogo)
