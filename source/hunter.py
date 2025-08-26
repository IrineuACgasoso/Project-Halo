import pygame
from game import *
from enemies import *
from player import *

class Hunter(InimigoBase):
    def __init__(self, posicao, grupos, jogador, game):
        super().__init__(posicao, grupos, jogador, game, vida_base=250, dano_base=40, velocidade_base=75)
        self.game = game

        #sprites
        self.sprites = {}
        #left
        self.sprites['left'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'hunter','hunter.png')).convert_alpha(), (250, 250)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'hunter','hunter2.png')).convert_alpha(), (270, 270))
            ]
        #right
        self.sprites['right'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites['left']
            ]

        #framagem da sprite
        self.frame_atual = 0  
        self.estado_animacao = 'right'
        self.indice_animacao = 0
        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center=self.posicao)
        self.velocidade_animacao = 250
        self.ultimo_update_animacao = pygame.time.get_ticks()

        #rage run ability
        self.velocidade = self.velocidade_base
        self.run_ativo = False
        self.cooldown_run = 6000
        self.tempo_ultima_run = pygame.time.get_ticks()
        self.duracao_run = 3000
        self.tempo_inicio_run = 0

        #cannon beam
        self.cooldown_cannon = 5000
        self.tempo_ultimo_cannon = pygame.time.get_ticks()

        self.estado_habilidade = 'nada'

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.posicao)
    
    def run(self):
        if not self.run_ativo:
            self.run_ativo = True
            self.velocidade_base = self.velocidade * 3
            self.tempo_inicio_run = pygame.time.get_ticks()


    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        # Lógica de controle do estado de corrida
        if self.run_ativo:
            if agora - self.tempo_inicio_run >= self.duracao_run:
                self.run_ativo = False
                self.velocidade_base = self.velocidade
        # Lógica para ativar a corrida
        if agora - self.tempo_ultima_run >= self.cooldown_run:
            self.estado_habilidade = 'run'
            self.tempo_ultima_run = agora
            self.run()
        
        # O resto da sua lógica de movimento e habilidades
        direcao = (self.jogador.posicao - self.posicao).normalize()
        self.posicao += direcao * self.velocidade_base * delta_time
        self.rect.center = self.posicao

        if direcao.x < 0:
            self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'

        self.animar()

