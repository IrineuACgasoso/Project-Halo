import pygame
import os
from os.path import join

from .menu_draw import MenuDraw
from source.windows.settings import largura_tela, altura_tela
from source.feats.assets import ASSETS

class MenuPrincipal(MenuDraw):
    def __init__(self, game):
        self.game = game
        
        # --- CARREGAMENTO DA FONTE ---
        self.font_path = join('assets', 'fonts', 'orbitron', 'Orbitron-Bold.ttf')
        try:
            if os.path.exists(self.font_path):
                self.font = pygame.font.Font(self.font_path, 40)
            else:
                self.font = pygame.font.SysFont('Consolas', 36, bold=True)
        except:
            self.font = pygame.font.SysFont('Consolas', 36, bold=True)
        
        # --- IMAGENS ---
        self.camada_fundo = ASSETS['menu']['menuback']
        self.camada_planeta = ASSETS['menu']['menuback2']
        self.camada_anel = ASSETS['menu']['haloring']
        self.logo = ASSETS['menu']['logo']
        
        self.timer = 0
        self.opcoes = ["START GAME", "RANKING", "SETTINGS", "CREATORS", "QUIT"]
        self.selecionada = 0

        # Cores Halo
        self.COR_BRANCO_SEL = (255, 255, 255)
        self.COR_CIANO_NEON = (0, 255, 255)
        self.COR_AZUL_MENU = (70, 140, 210)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                self.selecionada = (self.selecionada - 1) % len(self.opcoes)
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                self.selecionada = (self.selecionada + 1) % len(self.opcoes)
            elif event.key == pygame.K_RETURN:
                return self.opcoes[self.selecionada]
        return None

   
    def draw(self, tela):
        
        self.draw_menu_background(tela)

        for i, texto in enumerate(self.opcoes):
            self.draw_glow_text(tela, texto, largura_tela//2, 300 + i * 65, i == self.selecionada)
