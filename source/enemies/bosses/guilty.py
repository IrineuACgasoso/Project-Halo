import pygame
import random
import math
from enemies.enemies import *
from feats.projetil import *
from game import *
from feats.items import *
from player import *
from feats.projetil import LaserBeam

class GuiltySpark(InimigoBase):
    def __init__(self, posicao, grupos, jogador, game):
        super().__init__(posicao, grupos, jogador, game, vida_base=5000, dano_base=80, velocidade_base= 280)
        self.game= game
        #sprites
        self.sprites = {}
        #left
        self.sprites['left'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'guilty', 'guilty.png')).convert_alpha(), (100, 100)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'guilty', 'guilty2.png')).convert_alpha(), (100, 100))
        ]

        #right
        self.sprites['right'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites['left']
        ]
        #image
        self.estado_animacao = 'left'
        self.indice_animacao = 0
        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center=self.posicao)

        #hitbox
        self.mask = pygame.mask.from_surface(self.image)

        #laserbeam
        self.cooldown_laser = 3000
        self.ultimo_laser = pygame.time.get_ticks()
        self.estado_ataque = 'movendo'

        self.velocidade_anterior = self.velocidade_base

    def laser_attack(self):
        # Calcula a direção para o jogador
        direcao = (self.jogador.posicao - self.posicao).normalize()
        """Cria uma instância do laser."""
        LaserBeam(
            posicao_inimigo=self.posicao,
            grupos=(self.game.all_sprites, self.game.projeteis_inimigos_grupo),
            jogador=self.jogador,
            game=self.game,
            dano=self.dano_base * 5,
            velocidade= 1500,  # Ajuste o dano do laser
            duracao=1500,  # Ajusta a duração em milissegundos
        )
    def teleporte(self):
        # Gera um ângulo aleatório (em radianos)
        angulo = random.uniform(0, 2 * math.pi)
        # Define a distância de teleporte entre 150 e 250 pixels do jogador
        distancia_teleporte = random.uniform(150, 250)
        # Calcula a nova posição
        nova_posicao_x = self.jogador.posicao.x + distancia_teleporte * math.cos(angulo)
        nova_posicao_y = self.jogador.posicao.y + distancia_teleporte * math.sin(angulo)
        Teleport((round(nova_posicao_x), round(nova_posicao_y)), self.game.all_sprites, self.game)
        self.posicao.x = nova_posicao_x
        self.posicao.y = nova_posicao_y
        # Atualiza a posição do retângulo
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        self.velocidade *= 1.1

    def morrer(self, grupos):
        chance= randint(1,1000)
        if chance >= 950:
            Items(posicao=self.posicao, sheet_item=join('assets', 'img', 'cafe.png'), tipo='cafe', grupos=grupos)
            for _ in range(5):
                posicao_drop = self.posicao + pygame.math.Vector2(randint(-30, 30), randint(-30, 30))
                Items(posicao=posicao_drop, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=grupos)
        elif 800 <= chance < 950:
            chance2 = randint(1,4)
            if chance2 == 4:
                Items(posicao=self.posicao, sheet_item=join('assets', 'img', 'cafe.png'), tipo='cafe', grupos=grupos)
            for _ in range(4):
                posicao_drop = self.posicao + pygame.math.Vector2(randint(-30, 30), randint(-30, 30))
                Items(posicao=posicao_drop, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=grupos)
        elif 500 <= chance < 800:
            for _ in range(3):
                posicao_drop = self.posicao + pygame.math.Vector2(randint(-30, 30), randint(-30, 30))
                Items(posicao=posicao_drop, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=grupos)
        else:
            for _ in range(2):
                posicao_drop = self.posicao + pygame.math.Vector2(randint(-30, 30), randint(-30, 30))
                Items(posicao=posicao_drop, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=grupos)
        self.kill()

    def animar(self):
        """Atualiza a sprite do GuiltySpark com base na sua direção."""
        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center=self.posicao)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        direcao = (self.jogador.posicao - self.posicao)
        if direcao.length() > 0:
            direcao.normalize_ip()

        # Lógica de estados
        if self.estado_ataque == 'movendo':
            self.posicao += direcao * self.velocidade * delta_time
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))
            if (self.jogador.posicao - self.posicao).length() > 1000:
                self.teleporte()
            
            # Checa se é hora de mudar para o estado 'preparando'
            if agora - self.ultimo_laser >= self.cooldown_laser:
                self.ultimo_laser = agora
                self.estado_ataque = 'preparando'
                self.tempo_preparacao_ataque = agora
                self.velocidade_anterior = self.velocidade
                self.velocidade = 0 # Para o movimento

        elif self.estado_ataque == 'preparando':
            # Fica parado, esperando o tempo de preparação
            if agora - self.tempo_preparacao_ataque >= 1250: 
                self.laser_attack() # Dispara o laser
                self.estado_ataque = 'movendo' # Volta para o estado de movimento
                self.velocidade = self.velocidade_anterior
                self.velocidade_anterior = self # Restaura a velocidade
                novo_cooldown = [2000, 3000, 3500, 4000]
                self.cooldown_laser = random.choice(novo_cooldown)
        if self.estado_ataque == 'preparando':
            self.image = self.sprites[self.estado_animacao][1]
        # Lógica de animação
        else:
            if direcao.x < 0:
                self.estado_animacao = 'left'
            elif direcao.x > 0:
                self.estado_animacao = 'right'
            self.animar()


class Teleport(pygame.sprite.Sprite):
    def __init__(self, posicao, grupos, game):
        super().__init__(grupos)
        self.game = game

        self.image = pygame.transform.scale(pygame.image.load(join('assets', 'img', 'guilty', 'tp.png')).convert_alpha(), (200,200))
        self.rect = self.image.get_rect(center=posicao)
        self.tempo_criacao = pygame.time.get_ticks()
        self.duracao_aviso = 250  # Duração do aviso em milissegundos
    
    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        if agora - self.tempo_criacao >= self.duracao_aviso:
            self.kill()