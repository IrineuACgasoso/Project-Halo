import pygame
import random
import math
from enemies.enemies import *
from game import *
from player import *
from feats.items import *
from feats.projetil import Carabin



class Harbinger(InimigoBase):
    def __init__(self, posicao, game):
        super().__init__(posicao, vida_base=7500, dano_base=40, velocidade_base=50, game=game)

        #sprites
        self.sprites = {}
        self.sprites['left'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'harbinger', 'harb1.png')).convert_alpha(), (200,300)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'harbinger', 'harb2.png')).convert_alpha(), (200,300)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'harbinger', 'harb3.png')).convert_alpha(), (200,300)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'harbinger', 'harb4.png')).convert_alpha(), (200,300)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'harbinger', 'harb5.png')).convert_alpha(), (200,300))
            ]
        self.sprites['right'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites['left']
        ]
        
        #framagem da sprite
        self.frame_atual = 0  
        self.estado_animacao = 'right'
        self.indice_animacao = 0
        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center=self.posicao)
        self.velocidade_animacao = 200
        self.ultimo_update_animacao = pygame.time.get_ticks()

        # Habilidades
        self.cooldown_carabin = 5000
        self.intervalo_carabina = 250
        self.cronometro_carabina = 0
        self.ultima_carabina = 0
        self.carabina_restante = 0
        self.contagem_carabina = 3

        #hitbox
        nova_largura = self.rect.width / 2
        self.hitbox = pygame.Rect(0, 0, nova_largura, self.rect.height)
        self.hitbox.center = self.rect.center

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.posicao)

    def teleporte(self, a, b):
        # Gera um ângulo aleatório (em radianos)
        angulo = random.uniform(0, 2 * math.pi)
        # Define a distância de teleporte entre a e b pixels do jogador
        distancia_teleporte = random.uniform(a, b)
        # Calcula a nova posição
        nova_posicao_x = self.jogador.posicao.x + distancia_teleporte * math.cos(angulo)
        nova_posicao_y = self.jogador.posicao.y + distancia_teleporte * math.sin(angulo)

        self.posicao.x = nova_posicao_x
        self.posicao.y = nova_posicao_y
        # Atualiza a posição do retângulo
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        self.carabin()
    
    def update(self, delta_time):
        direcao = (self.jogador.posicao - self.posicao)
        # Teleporta para muito perto se estiver longe
        if direcao.length() > 1170:
            self.teleporte(350, 400)

        elif direcao.length() > 300:
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * delta_time
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        
        else:
            # Teleporta para longe se chegar muito próximo
            self.teleporte(600, 750)

        agora = pygame.time.get_ticks()
        #Ativa carabina
        if agora - self.ultima_carabina >= self.cooldown_carabin:
            self.carabina_restante = self.contagem_carabina
            novo_cooldown_carabina = [6000, 8000, 10000, 11000]
            self.cooldown_carabin = random.choice(novo_cooldown_carabina)
            self.ultima_carabina = agora
        #Atira carabina
        if self.carabina_restante > 0:
            self.cronometro_carabina += delta_time * 1000
            if self.cronometro_carabina >= self.intervalo_carabina:
                self.cronometro_carabina = 0
                self.carabina_restante -= 1
                self.carabin()

        if direcao.x < 0:
            self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'
        self.animar()

    
    def carabin(self):
        Carabin(
            posicao_inicial=self.posicao,
            grupos=(self.game.all_sprites, self.game.projeteis_inimigos_grupo),
            jogador=self.jogador,
            game=self.game,
            dano=75,
            velocidade=400,
            tamanho=(28, 28)
        )