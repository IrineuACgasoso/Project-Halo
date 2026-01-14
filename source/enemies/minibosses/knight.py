import pygame
import random
from game import *
from feats.items import *
from player import *
from settings import *
from feats.projetil import LaserBeam
from enemies.enemies import *



class Knight(InimigoBase):
    def __init__(self, posicao, grupos, jogador, game):
        super().__init__(posicao, grupos, jogador, game, vida_base=500, dano_base=60, velocidade_base=50)
        self.game = game

        #sprites
        self.sprites = {}
        #right
        self.sprites['right'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'prometheans', 'knight', 'command1.png')).convert_alpha(), (200,200)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'prometheans', 'knight', 'command2.png')).convert_alpha(), (200,200)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'prometheans', 'knight', 'command3.png')).convert_alpha(), (200,200)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'prometheans', 'knight', 'command4.png')).convert_alpha(), (200,200)),
        ]
        #left
        self.sprites['left'] = [pygame.transform.flip(sprite, True, False) for sprite in self.sprites['right']]
        # Inicia a animação
        self.frame_atual = 0
        self.estado_animacao = 'right' 
        self.velocidade_animacao = 300 # Milissegundos por frame
        self.ultimo_update_animacao = pygame.time.get_ticks()
        #rect
        self.image = self.sprites[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center=self.posicao)
        # Cria a hitbox do knight
        self.hitbox = pygame.Rect(0, 0, self.rect.width * 0.6, self.rect.height * 0.9)
        self.hitbox.center = self.rect.center

        #laser
        self.cooldown_laser = 7000
        self.ultimo_laser = 0

        #run
        self.running = False
        self.cooldown_run = 10000
        self.duracao_run = 2000
        self.ultima_run = 0
        self.inicio_run = 0
        self.velocidade = self.velocidade_base

    @property
    def collision_rect(self):
        return self.hitbox
    
    def laser(self):
        LaserBeam(
            posicao_inimigo=self.posicao,
            grupos=(self.game.all_sprites, self.game.projeteis_inimigos_grupo),
            jogador=self.jogador,
            game=self.game,
            dano=self.dano_base * 1.5,
            velocidade= 800,  # Ajuste o dano do laser
            duracao=2000,  # Ajusta a duração em milissegundos
        )

    def morrer(self, grupos):
        chance= randint(1,1000)
        if chance >= 990:
            Items(posicao=self.posicao, sheet_item=join('assets', 'img', 'cafe.png'), tipo='cafe', grupos=grupos)
            for _ in range(5):
                posicao_drop = self.posicao + pygame.math.Vector2(randint(-30, 30), randint(-30, 30))
                Items(posicao=posicao_drop, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=grupos)
        elif 960 <= chance < 990:
            chance2 = randint(1,4)
            if chance2 == 4:
                Items(posicao=self.posicao, sheet_item=join('assets', 'img', 'cafe.png'), tipo='cafe', grupos=grupos)
            for _ in range(4):
                posicao_drop = self.posicao + pygame.math.Vector2(randint(-30, 30), randint(-30, 30))
                Items(posicao=posicao_drop, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=grupos)
        elif 800 <= chance < 960:
            for _ in range(3):
                posicao_drop = self.posicao + pygame.math.Vector2(randint(-30, 30), randint(-30, 30))
                Items(posicao=posicao_drop, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=grupos)
        else:
            for _ in range(2):
                posicao_drop = self.posicao + pygame.math.Vector2(randint(-30, 30), randint(-30, 30))
                Items(posicao=posicao_drop, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=grupos)
        self.kill()

    def run(self):
        if not self.running:
            novo_cooldown = [10000, 15000, 20000, 25000]
            self.cooldown_run = random.choice(novo_cooldown)
            self.running = True
            self.velocidade = self.velocidade_base * 4.0
            self.inicio_run = pygame.time.get_ticks()
    
    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.posicao)
            self.hitbox.center = self.rect.center

    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        direcao = (self.jogador.posicao - self.posicao)
        if direcao.length() > 0:
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * delta_time
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        self.hitbox.center = self.rect.center
        #ativa laser
        if agora - self.ultimo_laser >= self.cooldown_laser:
            novo_cooldown = [5000, 7000, 9000, 11000]
            self.cooldown_laser = random.choice(novo_cooldown)
            self.ultimo_laser = agora
            self.laser()
        #ativa run
        if agora - self.ultima_run >= self.cooldown_run:
            self.ultima_run = agora
            self.run()
        #desativa run
        if self.running:
            if agora - self.inicio_run >= self.duracao_run:
                self.running = False
                self.velocidade = self.velocidade_base
        
        if direcao.x < 0:
            self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'
        self.animar()