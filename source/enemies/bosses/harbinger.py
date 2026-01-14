import pygame
import random
import math
from enemies.enemies import *
from game import *
from player import *
from feats.items import *
from feats.projetil import Carabin
from entitymanager import entity_manager




class Harbinger(InimigoBase):
    def __init__(self, posicao, game, grupos):
        valor_vida = 7500
        super().__init__(posicao, vida_base=valor_vida, dano_base=40, velocidade_base=50, game=game)
        self.titulo = "HARBINGER, A Rainha Endless"
        self.vida = valor_vida
        self.vida_base = valor_vida
        #sprites
        self.sprites = {}
        self.sprites['left'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'harbinger', 'harb1.png')).convert_alpha(), (200,300)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'harbinger', 'harb2.png')).convert_alpha(), (200,300)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'harbinger', 'harb3.png')).convert_alpha(), (200,300)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'harbinger', 'harb4.png')).convert_alpha(), (200,300)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'harbinger', 'harb5.png')).convert_alpha(), (200,300))
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

        # Teleporte
        self.ultimo_tp = 0
        self.tp_cooldown = 3000
        self.teleportando = False
        self.tempo_inicio_tp = 0
        self.duracao_invisivel = 400

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
        self.teleportando = True
        self.tempo_inicio_tp = pygame.time.get_ticks()
        # Gera um ângulo aleatório (em radianos)
        angulo = random.uniform(0, 2 * math.pi)
        # Define a distância de teleporte entre a e b pixels do jogador
        distancia_teleporte = random.uniform(a, b)

        # Teleporte saída
        Teleport(self.posicao, 1)

        # Calcula a nova posição
        nova_posicao_x = self.jogador.posicao.x + distancia_teleporte * math.cos(angulo)
        nova_posicao_y = self.jogador.posicao.y + distancia_teleporte * math.sin(angulo)

        self.posicao.x = nova_posicao_x
        self.posicao.y = nova_posicao_y
        # Atualiza a posição do retângulo
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        # Teleporte chegada
        Teleport(self.posicao, -1)

        self.carabin()
    
    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        direcao = (self.jogador.posicao - self.posicao)

        if self.teleportando:
            if agora - self.tempo_inicio_tp < self.duracao_invisivel:
                self.image.set_alpha(0) # Fica invisível
                return 
            else:
                self.teleportando = False
                self.image.set_alpha(255) # Volta a ser visível
                self.hitbox.center = self.rect.center

        # Teleporta para muito perto se estiver longe e para longe se estiver muito perto
        if agora - self.ultimo_tp > self.tp_cooldown:
            if direcao.length() > 1170:
                self.teleporte(200, 250)
                self.ultimo_tp = agora
                return
            elif direcao.length() < 300:
                self.teleporte(500, 550)
                self.ultimo_tp = agora
                return

        if direcao.length() > 0:
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * delta_time
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))

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
            grupos=(entity_manager.all_sprites, entity_manager.projeteis_inimigos_grupo),
            jogador=self.jogador,
            game=self.game,
            dano=75,
            velocidade=400,
            tamanho=(28, 28)
        )

class Teleport(pygame.sprite.Sprite):
    def __init__(self, posicao, ordem):
        super().__init__(entity_manager.all_sprites)
        self.posicao = pygame.math.Vector2(posicao) 
        self.ordem = ordem
        self.sprites = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'harbinger', 'teleport', 'tp1.png')).convert_alpha(), (100,100)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'harbinger', 'teleport', 'tp2.png')).convert_alpha(), (100,100)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'harbinger', 'teleport', 'tp3.png')).convert_alpha(), (100,100)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'harbinger', 'teleport', 'tp4.png')).convert_alpha(), (100,100)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'harbinger', 'teleport', 'tp5.png')).convert_alpha(), (100,100)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'harbinger', 'teleport', 'tp6.png')).convert_alpha(), (100,100)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'harbinger', 'teleport', 'tp7.png')).convert_alpha(), (100,100)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'harbinger', 'teleport', 'tp8.png')).convert_alpha(), (100,100)),
        ]

        # Animação
        if self.ordem == 1:
            self.frame_atual = 0
        else:
            # Começa no último frame se for -1
            self.frame_atual = len(self.sprites) - 1
        self.image = self.sprites[self.frame_atual]
        self.rect = self.image.get_rect(center=self.posicao)
        
        self.tempo_criacao = pygame.time.get_ticks()
        self.ultimo_update_animacao = pygame.time.get_ticks()
        self.velocidade_animacao = 50
        self.duracao_aviso = 400
    
    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        if agora - self.tempo_criacao >= self.duracao_aviso:
            self.kill()
        self.animar()

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + self.ordem) % len(self.sprites)
            self.image = self.sprites[self.frame_atual]
            self.rect = self.image.get_rect(center=self.posicao)  