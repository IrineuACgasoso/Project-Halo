import pygame
import random
from os.path import join
from enemies.enemies import InimigoBase
from player import *
from settings import *
from feats.items import *
from entitymanager import entity_manager



class Infection(InimigoBase):
    def __init__(self, posicao, game):
        # 1. A Base gerencia o cache e define self.posicao inicial
        super().__init__(posicao, vida_base=1, dano_base=5, velocidade_base=120, game=game, sprite_key='infection')
        
        # 2. Busca os sprites já processados (Cache Global)
        self.sprites = self.get_sprites('default')

        # 3. Configuração de animação
        self.frame_atual = 0  
        self.estado_animacao = 'left'
        self.image = self.sprites[self.estado_animacao][self.frame_atual]
        
        # Sincroniza o rect inicial com a posição arredondada
        self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))
        
        self.velocidade_animacao = 150
        self.ultimo_update_animacao = pygame.time.get_ticks()

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))

    def update(self, delta_time, paredes=None):
        super().update(delta_time, paredes)

        direcao_x = self.jogador.posicao.x - self.posicao.x
        
        if direcao_x < 0:
            self.estado_animacao = 'left'
        elif direcao_x > 0:
            self.estado_animacao = 'right'

        self.animar()