import pygame
import random
from enemies.enemies import InimigoBase
from os.path import join
from player import *
from settings import *
from feats.projetil import PlasmaGun
from feats.items import *
from entitymanager import entity_manager



class Grunt(InimigoBase):
    def __init__(self, posicao, game):
        super().__init__(posicao, vida_base=4, dano_base=15, velocidade_base=90, game=game)
        self.image = pygame.image.load(join('assets', 'img', 'grunt', 'grunt.png')).convert_alpha()
        self.image = pygame.transform.scale(self.image, (100, 80))
        self.rect = self.image.get_rect(center=self.posicao)
        self.velocidade = 70
        self.vida = 2
        self.dano = 15
        #arma
        self.plasma_cooldown = 8000
        self.ultimo_tiro = pygame.time.get_ticks()
        #pre animacao
        self.sprites = {}
        sprites_right = [
            pygame.image.load(join('assets', 'img', 'grunt', 'grunt.png')).convert_alpha(),
            pygame.image.load(join('assets', 'img', 'grunt', 'grunt2.png')).convert_alpha(),
            #pygame.image.load(join('assets', 'img', 'grunt', 'grunt3.png')).convert_alpha()
        ]
        #add esquerda no dict
        self.sprites['right'] = [pygame.transform.scale(sprite, (96, 96)) for sprite in sprites_right]
        #Carrega direita
        sprites_left = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites['right']
        ]
        #add direita no dict
        self.sprites['left'] = sprites_left
        #framagem da sprite
        self.frame_atual = 0  
        self.estado_animacao = 'right'
        self.indice_animacao = 0
        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center=self.posicao)
        self.velocidade_animacao = 200
        self.ultimo_update_animacao = pygame.time.get_ticks()

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.posicao)

    def update(self, delta_time):
        direcao = (self.jogador.posicao - self.posicao)
        if direcao.length() > 0:
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * delta_time
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro >= self.plasma_cooldown:
            novo_cooldown = [8000, 9000, 10000, 11000]
            self.plasma_cooldown = random.choice(novo_cooldown)
            self.plasma()
            self.ultimo_tiro = agora
        if direcao.x < 0:
            self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'
        self.animar()

    def plasma(self):
        # Cria uma instância do PlasmaGun
        PlasmaGun(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites, entity_manager.projeteis_inimigos_grupo),
            jogador=self.jogador,
            game=self.game,
            tamanho=(12,12),
            dano=5,
            velocidade=250
        )    