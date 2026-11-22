import pygame
from source.systems.gameclock import relogio
import random
from os.path import join
from source.enemies.base.enemy_base import BaseEnemy
from source.windows.settings import *
from source.feats.projetil import DizimatorBullet
from source.feats.items import *
from source.feats.assets import *
from source.systems.entitymanager import entity_manager
from source.data.enemy_data import INIMIGOS


class Brute(BaseEnemy):
    def __init__(self, posicao, game):
        perfil = INIMIGOS['brute']
        super().__init__(posicao, vida_base=perfil.vida, dano_base=perfil.dano,
                         velocidade_base=perfil.velocidade, game=game, sprite_key='brute')
        self.perfil = perfil
        self.tabela_drop = perfil.drops

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

        DizimatorBullet(
            posicao_inicial     = self.posicao,
            grupos              = (entity_manager.all_sprites,),
            jogador             = self.jogador,
            game                = self.game,
            dono                = 'INIMIGO', fonte=self,
            tamanho             = (48,48),
            dano                = 15,
            velocidade          = 800,
            direcao_spread      = direcao_tiro
            )
    
    def update(self, delta_time, paredes = None):
        super().update(delta_time, paredes)
        agora = relogio.agora()

        if agora - self.ultimo_shot >= self.cooldown_shot:
            self.ultimo_shot = agora
            self.cooldown_shot = self.novo_cooldown(*self.perfil.cooldowns['dizimadora'])
            self.dizim()
            
        if self.vida <= self.vida_base / 2 and self.rage == False:
            self.velocidade *= 3
            self.rage = True
            
        direcao_x = self.jogador.posicao.x - self.posicao.x
        self.set_sprite_direction(direcao_x)
        self.animar()