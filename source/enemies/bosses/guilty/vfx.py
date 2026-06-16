import pygame
from source.feats.assets import ASSETS
from source.systems.entitymanager import entity_manager

class GuiltyTeleport(pygame.sprite.Sprite):
    def __init__(self, posicao):
        super().__init__(entity_manager.all_sprites)
        self.posicao = pygame.math.Vector2(posicao) 
        self.sprites = ASSETS['enemies']['guilty']['teleport']

        self.frame_atual = 0
        self.image = self.sprites[self.frame_atual]
        self.rect = self.image.get_rect(center=self.posicao)
        
        self.tempo_criacao = pygame.time.get_ticks()
        self.ultimo_update_animacao = pygame.time.get_ticks()
        self.velocidade_animacao = 30
        self.duracao_aviso = 330
    
    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        if agora - self.tempo_criacao >= self.duracao_aviso:
            self.kill()
        self.animar()

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites)
            self.image = self.sprites[self.frame_atual]
            self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))


