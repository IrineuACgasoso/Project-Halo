"""Registro de armas, sorteio da tela de upgrade, regras de upgrade e integridade de weapon_data."""
import random

import pygame
import pytest

from source.data.weapon_data import COMPANION_DATA, VEHICLES_DATA, WEAPON_DATA, WeaponStats
from source.feats.weapons.baseweapon import ALL_DATA, Arma
from source.systems.entitymanager import entity_manager
from source.systems.levelup import ARMAS_REGISTRO, MAX_ARMAS, PALETA_RARIDADE, TelaDeUpgrade

IDS = sorted(ARMAS_REGISTRO)


# ── Integridade do registro ──────────────────────────────────────────────────
@pytest.mark.parametrize('id_arma', IDS)
def test_registro_consistente(id_arma):
    info = ARMAS_REGISTRO[id_arma]
    assert info.id == id_arma
    assert info.raridade in PALETA_RARIDADE
    for nome in info.grupos:                       # EventManager faz getattr(entity_manager, nome)
        assert isinstance(getattr(entity_manager, nome), pygame.sprite.AbstractGroup)


@pytest.mark.parametrize('id_arma', IDS)
def test_classe_registrada_tem_perfil_de_dados(id_arma):
    classe = ARMAS_REGISTRO[id_arma].classe
    assert classe.NOME_ASSET in ALL_DATA


def test_nomes_de_dados_nao_colidem_entre_categorias():
    assert not (set(WEAPON_DATA) & set(COMPANION_DATA))
    assert not (set(WEAPON_DATA) & set(VEHICLES_DATA))
    assert not (set(COMPANION_DATA) & set(VEHICLES_DATA))


# ── WeaponStats / _deve_melhorar ─────────────────────────────────────────────
def test_weaponstats_aliases_legados():
    s = WeaponStats(value=1, range_val=3, min_val=50)
    assert s['range'] == 3 and s['min'] == 50 and s['value'] == 1


@pytest.mark.parametrize('range_val, nivel, esperado', [
    (0, 2, False), (None, 2, False),
    (2, 4, True), (2, 3, False), (1, 7, True),
    ([3, 5], 5, True), ([3, 5], 4, False),
])
def test_deve_melhorar(range_val, nivel, esperado):
    assert Arma._deve_melhorar(range_val, nivel) is esperado


def test_aplicar_upgrades_respeita_minimo(player):
    rifle = player.armas['assault_rifle']
    meta = WEAPON_DATA['assault_rifle'].stats['cooldown']
    for _ in range(200):
        rifle.upgrade()
    if meta.min_val is not None:
        assert rifle.cooldown >= meta.min_val


def test_stats_com_increase_negativo_tem_minimo():
    """Não há teto de nível: sem min_val um cooldown chega a 0/negativo (brick, nível 21)."""
    sem_piso = [
        f'{nome}.{attr}'
        for dados in (WEAPON_DATA, COMPANION_DATA, VEHICLES_DATA)
        for nome, perfil in dados.items()
        for attr, meta in perfil.stats.items()
        if meta.increase and meta.increase < 0 and meta.label and meta.min_val is None
    ]
    assert sem_piso == []


# ── TelaDeUpgrade ────────────────────────────────────────────────────────────
@pytest.mark.parametrize('semente', range(10))
def test_opcoes_aleatorias_validas(player, semente):
    random.seed(semente)
    tela = TelaDeUpgrade(player.game.tela, player, player.game)
    ids = tela.ids_das_opcoes
    assert 1 <= len(ids) <= 3
    assert len(set(ids)) == len(ids)
    assert all(i in ARMAS_REGISTRO for i in ids)


def test_com_arsenal_cheio_so_oferece_upgrades(player):
    for id_arma in IDS[:MAX_ARMAS]:
        player.armas[id_arma] = object()
    for semente in range(10):
        random.seed(semente)
        tela = TelaDeUpgrade(player.game.tela, player, player.game)
        assert set(tela.ids_das_opcoes) <= set(player.armas)


def _tecla(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key, mod=0)


def test_navegacao_e_confirmacao(player):
    random.seed(0)
    tela = TelaDeUpgrade(player.game.tela, player, player.game)
    assert len(tela.opcoes) == 3
    assert tela.handle_event(_tecla(pygame.K_a)) is None
    assert tela.opcao_selecionada == 2                     # volta circular
    assert tela.handle_event(_tecla(pygame.K_RETURN)) == tela.ids_das_opcoes[2]


def test_modo_unico_ignora_navegacao(player):
    tela = TelaDeUpgrade(player.game.tela, player, player.game, id_arma_forcada='assault_rifle')
    tela.handle_event(_tecla(pygame.K_d))
    assert tela.opcao_selecionada == 0
    assert tela.handle_event(_tecla(pygame.K_SPACE)) == 'assault_rifle'


def test_desenho_da_tela_nao_falha(player):
    random.seed(0)
    TelaDeUpgrade(player.game.tela, player, player.game).draw(player.game.tela)


# ── EventManager: aplicar escolha ────────────────────────────────────────────
def test_escolher_arma_possuida_faz_upgrade(novo_jogo):
    rifle = novo_jogo.player.armas['assault_rifle']
    novo_jogo.event_manager._aplicar_escolha_de_upgrade('assault_rifle')
    assert rifle.nivel == 2


@pytest.mark.parametrize('id_arma', [i for i in IDS if i != 'assault_rifle'])
def test_escolher_arma_nova_equipa_e_sobe_de_nivel(novo_jogo, id_arma):
    em = novo_jogo.event_manager
    em._aplicar_escolha_de_upgrade(id_arma)
    arma = novo_jogo.player.armas[id_arma]
    assert isinstance(arma, ARMAS_REGISTRO[id_arma].classe)
    for _ in range(20):
        em._aplicar_escolha_de_upgrade(id_arma)
    assert arma.nivel == 21
    # a tela de upgrade (preview de stats do próximo nível) não pode quebrar em nível alto
    TelaDeUpgrade(novo_jogo.tela, novo_jogo.player, novo_jogo, id_arma_forcada=id_arma).draw(novo_jogo.tela)
