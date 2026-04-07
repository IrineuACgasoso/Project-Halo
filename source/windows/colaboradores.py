import pygame
from source.windows.settings import *
from source.feats.assets import ASSETS

class TelaColaboradores:
    def __init__(self, game):
        self.image = ASSETS['menu']['colaboradores']
        self.game = game
        self.imagem_rect = self.image.get_rect(center=self.game.tela.get_rect().center)

    def handle_event(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                self.game.estado_do_jogo = 'menu_principal'

    def draw(self, tela):
        tela.fill((0, 0, 0)) 
        tela.blit(self.imagem, self.imagem_rect)