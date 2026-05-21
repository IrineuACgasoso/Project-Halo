import pygame
import os
from os.path import join

from .menu_draw import MenuDraw
from source.windows.settings import largura_tela, altura_tela
from source.feats.assets import ASSETS




class TelaGameOver(MenuDraw):
    def __init__(self, game):
        self.game = game
        self.font = game.menu_principal.font
        self.font_path = join('assets', 'fonts', 'orbitron', 'Orbitron-Bold.ttf')
        try:
            if os.path.exists(self.font_path):
                self.font_titulo = pygame.font.Font(self.font_path, 80)
            else:
                self.font_titulo = pygame.font.SysFont('Consolas', 80, bold=True)
        except:
            self.font_titulo = pygame.font.SysFont('Consolas', 80, bold=True)
        
        self.bg = None
        self.fase_carregada = -1 # Para rastrear qual fase está carregada
        self.som = None
        try:
            self.som = pygame.mixer.Sound(join('assets', 'sounds', 'game_over.wav'))
            pygame.mixer.music.set_volume(0.3)
        except:
            pass
            
        self.som_tocado = False
        self.opcoes = ["RESTART MISSION", "EXIT TO MENU"]
        self.selecionada = 0
        self.timer = 0

    def carregar_bg_fase(self):
        # Só recarrega se a fase mudou desde a última vez
        if self.fase_carregada != self.game.fase_atual:
            try:
                chave_fase = f'{self.game.fase_atual}'
                if 'gameover' in ASSETS and chave_fase in ASSETS['gameover']:
                    bg_original = ASSETS['gameover'][chave_fase]
                    self.bg = pygame.transform.scale(bg_original, (largura_tela, altura_tela))
                else:
                    self.bg = pygame.Surface((largura_tela, altura_tela))
                    self.bg.fill((0, 0, 0))
                
                self.fase_carregada = self.game.fase_atual
                
            except Exception as e:
                print(f"Erro BG: {e}")
                self.bg = pygame.Surface((largura_tela, altura_tela))
                self.bg.fill((0, 0, 0))

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
        # Verifica e atualiza o BG se necessário
        self.carregar_bg_fase()

        if not self.som_tocado and self.som:
            self.som.play()
            self.som_tocado = True
            
        self.timer += 0.01
        
        if self.bg:
            tela.blit(self.bg, (0, 0))

        pos_x_esquerda = 100 
        
        # Título Gigante
        self.draw_glow_text(
            tela, 
            "MISSION FAILED", 
            pos_x_esquerda, 
            altura_tela//2 - 80, 
            True, 
            cor_glow=(255, 0, 0),
            align="left",
            fonte_custom=self.font_titulo
        )

        # Opções
        for i, texto in enumerate(self.opcoes):
            self.draw_glow_text(
                tela, 
                texto, 
                pos_x_esquerda, 
                altura_tela//2 + 50 + i * 70, 
                i == self.selecionada,
                align="left"
            )