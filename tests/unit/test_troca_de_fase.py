"""Persistência entre fases (roteiro E5): na troca de fase sobrevivem exatamente os sprites
cuja classe declara `sobrevive_troca_de_fase = True` (jogador, companheiros, aura do MK2)."""
import pygame
import pytest
from pygame.math import Vector2 as V

from source.enemies.standard.grunt import GruntRed
from source.feats.buddies import Companheiro
from source.feats.effects import Portal
from source.feats.items import Items
from source.systems.entitymanager import entity_manager
from source.systems.levelup.constants import ARMAS_REGISTRO


def _equipar_todas(game):
    """Todas as armas, companheiros e veículos, pelo mesmo caminho da escolha no level-up."""
    for id_arma in ARMAS_REGISTRO:
        game.event_manager._aplicar_escolha_de_upgrade(id_arma)


def _trocar_fase(game):
    game.stage_manager._trocar_dados_fase()


def _sprites_de_arma(game, atributo):
    return {getattr(arma, atributo) for arma in game.player.armas.values()
            if getattr(arma, atributo, None) is not None}


def test_sobrevivem_exatamente_jogador_companheiros_e_aura(novo_jogo):
    _equipar_todas(novo_jogo)
    p = novo_jogo.player
    GruntRed(posicao=p.posicao + V(300, 0), game=novo_jogo)
    Items.spawn_drop(p.posicao + V(50, 0), (entity_manager.all_sprites, entity_manager.items_grupo),
                     exp_shard=(3, 100, 100))
    Portal(p.posicao + V(0, 200), entity_manager.all_sprites)
    marines = list(p.armas['marine'].companions)
    esperados = ({p} | set(marines) | _sprites_de_arma(novo_jogo, 'sprite_companion')
                 | _sprites_de_arma(novo_jogo, 'area_de_dano'))
    assert len(esperados) == 1 + 4 + 1   # jogador, Árbitro/Cortana/Marine/Noble, aura do MK2

    _trocar_fase(novo_jogo)

    assert set(entity_manager.all_sprites) == esperados
    assert all(s.sobrevive_troca_de_fase for s in esperados)
    assert not entity_manager.inimigos_grupo and not entity_manager.items_grupo
    assert set(entity_manager.auras_grupo) == _sprites_de_arma(novo_jogo, 'area_de_dano')


def test_todos_os_marines_sobrevivem(novo_jogo):
    novo_jogo.event_manager._aplicar_escolha_de_upgrade('marine')
    arma = novo_jogo.player.armas['marine']
    while len(arma.companions) < 3:
        arma.upgrade()
    _trocar_fase(novo_jogo)
    assert all(m.alive() for m in arma.companions)


def test_a_flag_decide_sozinha_quem_fica(novo_jogo):
    """O StageManager não conhece arma nem dono: só a flag da classe (ou da instância)."""
    class Marcado(pygame.sprite.Sprite):
        sobrevive_troca_de_fase = True

    solto = Marcado(entity_manager.all_sprites)                  # não pertence a arma nenhuma
    sem_flag = pygame.sprite.Sprite(entity_manager.all_sprites)
    desmarcado = Marcado(entity_manager.all_sprites)
    desmarcado.sobrevive_troca_de_fase = False                   # a instância pode recusar

    _trocar_fase(novo_jogo)

    assert solto.alive() and not sem_flag.alive() and not desmarcado.alive()


def test_quem_sobrevive_continua_nos_outros_grupos(novo_jogo):
    """Sobreviver não é só ficar no all_sprites: a aura continua causando dano (auras_grupo)."""
    novo_jogo.event_manager._aplicar_escolha_de_upgrade('mk2_shield')
    aura = novo_jogo.player.armas['mk2_shield'].area_de_dano
    _trocar_fase(novo_jogo)
    assert aura.groups() and set(aura.groups()) == {entity_manager.all_sprites, entity_manager.auras_grupo}


@pytest.mark.parametrize('id_veiculo', ['warhog', 'pelican'])
@pytest.mark.xfail(strict=True, reason='bug conhecido (docs/log.md, E5): o veículo sai dos grupos na '
                                       'troca de fase, mas a arma continua atualizando o sprite invisível')
def test_veiculo_sobrevive_a_troca_de_fase(novo_jogo, id_veiculo):
    novo_jogo.event_manager._aplicar_escolha_de_upgrade(id_veiculo)
    veiculo = novo_jogo.player.armas[id_veiculo].sprite_veiculo
    _trocar_fase(novo_jogo)
    assert veiculo.alive()


@pytest.mark.xfail(strict=True, reason='bug conhecido (docs/log.md, E5): os companheiros vão para o '
                                       'spawn do mapa ANTIGO (lido antes de trocar o mapa)')
def test_companheiros_vao_para_o_spawn_do_mapa_novo(novo_jogo):
    _equipar_todas(novo_jogo)
    _trocar_fase(novo_jogo)
    spawn = V(novo_jogo.mapa.get_player_spawn_pos())
    companheiros = [s for s in entity_manager.all_sprites if isinstance(s, Companheiro)]
    assert companheiros and all(c.posicao == spawn for c in companheiros)
