import pygame
import random

from source.enemies.base.enemy_base import BaseEnemy
from source.feats.projetil import PlasmaGun
from source.systems.entitymanager import entity_manager


class Grunt(BaseEnemy):
    def __init__(self, posicao, game):
        super().__init__(posicao, vida_base=4, dano_base=10, velocidade_base=50, game=game, sprite_key= 'grunt')
        
        self.setup_animation(
            estado_inicial='right',
            velocidade_animacao=200
            )
        
        # Plasma
        self.plasma_cooldown = self.novo_cooldown(8000, 12000)
        self.ultimo_tiro = pygame.time.get_ticks()

    def update(self, delta_time, paredes=None):
        super().update(delta_time, paredes)
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro >= self.plasma_cooldown:
            self.plasma_cooldown = self.novo_cooldown(8000, 12000)
            self.plasma()
            self.ultimo_tiro = agora

        direcao_x = self.jogador.posicao.x - self.posicao.x
        self.set_sprite_direction(direcao_x)
        self.animar()

    def plasma(self):
        direcao_tiro = self.calcular_direcao_tiro(0.1)

        PlasmaGun(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites,),
            jogador=self.jogador,
            game=self.game,
            dono = 'INIMIGO',
            tamanho=(36, 36),
            dano=5,
            velocidade=500,
            direcao_spread=direcao_tiro,
            vai_rotacionar = False
        )    