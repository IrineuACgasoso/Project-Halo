import pygame
from settings import *

class Fundo(pygame.sprite.Sprite):
    def __init__(self, posicao, surface, grupos):
        super().__init__(grupos)
        self.image = surface
        self.rect = self.image.get_rect(topleft = posicao)

class AllSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.deslocamento = pygame.Vector2()
 
    def draw(self, alvo_posicao):
        self.deslocamento.x = -(alvo_posicao[0] - largura_tela / 2)
        self.deslocamento.y = -(alvo_posicao[1] - altura_tela / 2)
        for sprite in self:
            self.display_surface.blit(sprite.image, sprite.rect.topleft + self.deslocamento)
