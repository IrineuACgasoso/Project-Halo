import pygame
from settings import *

class TelaColaboradores:
    def __init__(self, game):
        
        self.game = game
        
        self.imagem = pygame.image.load(join('assets', 'img', 'colaboradores.png')).convert()
        self.imagem = pygame.transform.scale(self.imagem, (largura_tela, altura_tela))
        self.imagem_rect = self.imagem.get_rect(center=self.game.tela.get_rect().center)

    def handle_event(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                self.game.estado_do_jogo = 'menu_principal'

    def draw(self, tela):
        tela.fill((0, 0, 0)) 
        tela.blit(self.imagem, self.imagem_rect)