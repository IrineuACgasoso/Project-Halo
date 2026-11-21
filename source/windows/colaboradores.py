import pygame
from source.windows.settings import *
from source.feats.assets import ASSETS

class TelaColaboradores:
    def __init__(self, game):
        self.image = ASSETS['menu']['colaboradores']
        self.game = game
        self.imagem_rect = self.image.get_rect(center=self.game.tela.get_rect().center)

    def handle_event(self, evento):
        """Devolve 'sair' no ESC (quem troca o estado é o EventManager)."""
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            return 'sair'
        return None

    def draw(self, tela):
        tela.fill((0, 0, 0)) 
        tela.blit(self.image, self.imagem_rect)