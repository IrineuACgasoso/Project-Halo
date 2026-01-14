import pygame
import random
from os.path import join
from enemies.enemies import InimigoBase
from player import *
from settings import *
from feats.projetil import Carabin
from feats.items import *
from entitymanager import entity_manager


class Elite(InimigoBase):
    def __init__(self, posicao, game):
        super().__init__(posicao, vida_base=30,dano_base=20, velocidade_base=90, game=game)
        self.game

        #sprites
        self.sprites = {}
        # Carrega e redimensione as sprites da esquerda
        self.sprites['left'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'elite', 'elite1.png')).convert_alpha(),(120,180)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'elite', 'elite2.png')).convert_alpha(),(120,180)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'elite', 'elite3.png')).convert_alpha(),(120,180)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'elite', 'elite4.png')).convert_alpha(),(120,180))
        ]
        #Carrega direita
        self.sprites['right'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites['left']
        ]
        #Animação
        self.estado_animacao = 'right'
        self.frame_atual = 0
        self.velocidade_animacao = 150
        self.ultimo_update_animacao = pygame.time.get_ticks()
        self.image = self.sprites[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center=posicao)

        #Carabin
        self.cooldown_carabin = 4000
        self.intervalo_carabina = 75
        self.cronometro_carabina = 0
        self.ultima_carabina = 0
        self.carabina_restante = 0
        self.contagem_carabina = 5

        #Invisibilidade
        self.vida_critica = False

    def carabin(self):
        Carabin(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites, entity_manager.projeteis_inimigos_grupo),
            jogador=self.jogador,
            game=self.game,
            dano=10,
            velocidade=500,
            tamanho=(12, 12)
        )

    def morrer(self, grupos):
        alvo_grupos = (entity_manager.all_sprites, entity_manager.item_group)
        for _ in range(3):
            posicao_drop = self.posicao + pygame.math.Vector2(randint(-30, 30), randint(-30, 30))
            Items(posicao=posicao_drop, sheet_item=join('assets', 'img', 'expShard.png'), tipo='exp_shard', grupos=alvo_grupos)
        self.kill()

    def animar(self):
        if self.velocidade > 0:
            agora = pygame.time.get_ticks()
            if agora - self.ultimo_update_animacao > self.velocidade_animacao:
                self.ultimo_update_animacao = agora
                self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
                self.image = self.sprites[self.estado_animacao][self.frame_atual]
                self.rect = self.image.get_rect(center=self.posicao)

    def update(self, delta_time):
        direcao = (self.jogador.posicao - self.posicao)
        agora = pygame.time.get_ticks()
        #Ativa invisibi
        if self.vida <= self.vida_base / 2 and self.vida_critica == False:
            self.vida_critica = True
            self.velocidade *= 2
            self.image.set_alpha(0)
        #Ativa carabina
        if agora - self.ultima_carabina >= self.cooldown_carabin:
            self.carabina_restante = self.contagem_carabina
            novo_cooldown_carabina = [3000, 4000, 5000, 6000]
            self.cooldown_carabin = random.choice(novo_cooldown_carabina)
            self.ultima_carabina = agora
        #Atira carabina
        if self.carabina_restante > 0:
            if self.vida_critica:
                self.image.set_alpha(100)
            self.cronometro_carabina += delta_time * 1000
            if self.cronometro_carabina >= self.intervalo_carabina:
                self.cronometro_carabina = 0
                self.carabina_restante -= 1
                self.carabin()
        else:
            if self.vida_critica:
                self.image.set_alpha(0)
        if direcao.length() < 350:
            self.velocidade = 0
        else:
            self.velocidade = self.velocidade_base
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * delta_time
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        if direcao.x < 0:
            self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'
        self.animar()
