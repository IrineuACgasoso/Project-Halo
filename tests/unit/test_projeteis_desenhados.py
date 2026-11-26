"""Tiros pintados em código: o acerto é sempre o círculo do `tamanho` (rect e máscara), em qualquer ângulo,
e o desenho não quebra."""
import pygame
import pytest

from source.feats.projetil import DizimatorBullet, M50, PlasmaGun
from source.systems.entitymanager import entity_manager

V = pygame.math.Vector2


@pytest.mark.parametrize('classe', [PlasmaGun, DizimatorBullet, M50], ids=lambda c: c.__name__)
@pytest.mark.parametrize('direcao', [V(1, 0), V(-1, 1).normalize()], ids=['reto', 'diagonal'])
def test_acerto_e_o_circulo_do_tamanho(novo_jogo, classe, direcao):
    tiro = classe(posicao_inicial=V(500, 500), grupos=(entity_manager.all_sprites,), jogador=novo_jogo.player,
                  game=novo_jogo, dono='INIMIGO', tamanho=(40, 40), dano=5, velocidade=100, direcao_spread=direcao)
    assert tiro.rect.size == (40, 40) and tiro.mask.get_size() == (40, 40)
    assert tiro.mask.get_at((20, 20)) and tiro.mask.get_at((2, 20)) and not tiro.mask.get_at((1, 1))
    tiro.draw(pygame.Surface((1000, 1000)), V(0, 0))
