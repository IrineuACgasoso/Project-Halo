"""Persistência entre fases (roteiro E5): na troca de fase sobrevivem exatamente os sprites
cuja classe declara `sobrevive_troca_de_fase = True` (jogador, companheiros, veículos, aura do MK2)."""
import pygame
from pygame.math import Vector2 as V

from source.enemies.standard.grunt import GruntRed
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


def test_sobrevivem_exatamente_jogador_companheiros_veiculos_e_aura(novo_jogo):
    _equipar_todas(novo_jogo)
    p = novo_jogo.player
    GruntRed(posicao=p.posicao + V(300, 0), game=novo_jogo)
    Items.spawn_drop(p.posicao + V(50, 0), (entity_manager.all_sprites, entity_manager.items_grupo),
                     exp_shard=(3, 100, 100))
    Portal(p.posicao + V(0, 200), entity_manager.all_sprites)
    marines = list(p.armas['marine'].companions)
    esperados = ({p} | set(marines) | _sprites_de_arma(novo_jogo, 'sprite_companion')
                 | _sprites_de_arma(novo_jogo, 'sprite_veiculo') | _sprites_de_arma(novo_jogo, 'area_de_dano'))
    assert len(esperados) == 1 + 4 + 2 + 1   # jogador, Árbitro/Cortana/Marine/Noble, Warthog/Pelican, MK2

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


def test_companheiro_tem_posicao_propria_depois_da_troca(novo_jogo):
    """O spawn do mapa é um Vector2 guardado: quem o recebe precisa de cópia, senão andar
    com o companheiro moveria o spawn (e o jogador da próxima troca)."""
    novo_jogo.event_manager._aplicar_escolha_de_upgrade('arbiter')
    _trocar_fase(novo_jogo)
    companheiro = novo_jogo.player.armas['arbiter'].sprite_companion
    spawn = V(novo_jogo.mapa.get_player_spawn_pos())
    companheiro.posicao.x += 100
    assert novo_jogo.mapa.get_player_spawn_pos() == spawn
    assert companheiro.posicao is not novo_jogo.player.posicao
