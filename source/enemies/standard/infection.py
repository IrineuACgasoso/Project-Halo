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
        super().__init__(posicao, vida_base=1, dano_base=5, velocidade_base=120, game=game)
        #sprites
        self.sprites = {}

        # Carrega e redimensione as sprites da esquerda
        sprites_left = [
            pygame.image.load(join('assets', 'img', 'enemies', 'infection', 'infection1.png')).convert_alpha(),
            pygame.image.load(join('assets', 'img', 'enemies', 'infection', 'infection2.png')).convert_alpha()
        ]
        #add esquerda no dict
        self.sprites['left'] = [pygame.transform.scale(sprite, (75, 75)) for sprite in sprites_left]
        #Carrega direita
        sprites_right = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites['left']
        ]
        #add direita no dict
        self.sprites['right'] = sprites_right
        #framagem da sprite
        self.frame_atual = 0  
        self.estado_animacao = 'left'
        self.indice_animacao = 0
        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center=self.posicao)
        self.velocidade_animacao = 150
        self.ultimo_update_animacao = pygame.time.get_ticks()
    
    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.posicao) # Mantém o centro na mesma posição

    def update(self, delta_time):
        direcao = (self.jogador.posicao - self.posicao)
        if direcao.length() > 0:
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * delta_time
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        if direcao.x < 0:
            self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'
        self.animar()