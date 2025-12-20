import pygame
import random
from os.path import join
from enemies.enemies import InimigoBase
from player import *
from settings import *
from feats.projetil import Dizimator
from feats.items import *
from entitymanager import entity_manager


class Brute(InimigoBase):
    def __init__(self, posicao, game):
        super().__init__(posicao, vida_base=30,dano_base=20, velocidade_base=75, game=game)
        self.game

        #sprites
        self.sprites = {}
        # Carrega e redimensione as sprites da esquerda
        self.sprites['left'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'brute', 'brute.png')).convert_alpha(),(200,200)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'brute', 'brute2.png')).convert_alpha(),(200,200))
            #pygame.transform.scale(pygame.image.load(join('assets', 'img', 'brute', 'brute3.png')).convert_alpha(),(150,150))

        ]
        #Carrega direita
        self.sprites['right'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites['left']
        ]
        #Animação
        self.estado_animacao = 'right'
        self.frame_atual = 0
        self.velocidade_animacao = 250
        self.ultimo_update_animacao = pygame.time.get_ticks()
        self.image = self.sprites[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center=posicao)

        #Rage
        self.rage = False

        #Dizimadora
        self.cooldown_shot = 3000
        self.ultimo_shot= 0 

    def dizim(self):
        Dizimator(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites, entity_manager.projeteis_inimigos_grupo),
            jogador=self.jogador,
            game=self.game,
            tamanho=(48,48),
            dano=15,
            velocidade=800)
    
    def morrer(self, grupos):
        alvo_grupos = (entity_manager.all_sprites, entity_manager.item_group)
        for _ in range(3):
            posicao_drop = self.posicao + pygame.math.Vector2(randint(-30, 30), randint(-30, 30))
            Items(posicao=posicao_drop, sheet_item=join('assets', 'img', 'expShard.png'), tipo='exp_shard', grupos=alvo_grupos)
        self.kill()

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.posicao)

    def update(self, delta_time):
        direcao = (self.jogador.posicao - self.posicao)
        agora = pygame.time.get_ticks()
        if direcao.length() > 0:
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * delta_time
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        if agora - self.ultimo_shot >= self.cooldown_shot:
            self.ultimo_shot = agora
            novo_cooldown = [5000, 6000, 7000, 8000]
            self.cooldown_shot = random.choice(novo_cooldown)
            self.dizim()
        if self.vida <= self.vida_base / 2 and self.rage == False:
            self.velocidade *= 3
            self.rage = True
        if direcao.x < 0:
            self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'
        self.animar()