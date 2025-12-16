import pygame
from settings import *



class Items(pygame.sprite.Sprite):
    def __init__(self, sheet_item, posicao, tipo, grupos):
        super().__init__(grupos)
        #posicao
        self.posicao_original = pygame.math.Vector2(posicao)
        self.posicao = pygame.math.Vector2(posicao)

        #drop
        self.direcao = pygame.math.Vector2(0, 1)
        self.velocidade = -100
        self.gravidade = 8
        self.dropping = True

        #imagem
        self.frame = pygame.image.load(sheet_item).convert_alpha()
        self.image = self.frame
        self.rect = self.image.get_rect(center = self.posicao)

        self.tipo = tipo

    def update(self, delta_time):
        if self.dropping:
            #movimento de drop
            self.velocidade += self.gravidade
            self.posicao += self.direcao * self.velocidade * delta_time
            self.rect.centery = self.posicao.y
            
            if self.velocidade > 0 and self.posicao.y >= self.posicao_original.y:
                self.posicao.y = self.posicao_original.y
                self.rect.centery = self.posicao.y
                self.velocidade = 0
                self.dropping = False
    
        


        

