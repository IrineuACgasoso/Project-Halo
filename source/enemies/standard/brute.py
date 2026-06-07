import pygame
import random
from os.path import join
from source.enemies.base.enemy_base import BaseEnemy
from source.windows.settings import *
from source.feats.projetil import Dizimator
from source.feats.items import *
from source.feats.assets import *
from source.systems.entitymanager import entity_manager


class Brute(BaseEnemy):
    def __init__(self, posicao, game):
        super().__init__(posicao, vida_base=30,dano_base=20, velocidade_base=75, game=game, sprite_key='brute')
        self.game

        #Animação
        self.setup_animation(
            velocidade_animacao=250
        )

        #Rage
        self.rage = False

        #Dizimadora
        self.cooldown_shot = 3000
        self.ultimo_shot= 0 

    def dizim(self):
        direcao_tiro = self.calcular_direcao_tiro(0.1)

        Dizimator(
            posicao_inicial     = self.posicao,
            grupos              = (entity_manager.all_sprites,),
            jogador             = self.jogador,
            game                = self.game,
            dono                = 'INIMIGO',
            tamanho             = (48,48),
            dano                = 15,
            velocidade          = 800,
            direcao_spread      = direcao_tiro
            )
    
    def morrer(self, grupos = None):
        Items.spawn_drop(self.posicao, grupos, 'exp_shard', 3, 100)
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 1, 2)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 1)
        self.kill()

    def update(self, delta_time, paredes = None):
        super().update(delta_time, paredes)
        agora = pygame.time.get_ticks()

        if agora - self.ultimo_shot >= self.cooldown_shot:
            self.ultimo_shot = agora
            self.cooldown_shot = self.novo_cooldown(5000, 8000)
            self.dizim()
            
        if self.vida <= self.vida_base / 2 and self.rage == False:
            self.velocidade *= 3
            self.rage = True
            
        direcao_x = self.jogador.posicao.x - self.posicao.x
        self.set_sprite_direction(direcao_x)
        self.animar()