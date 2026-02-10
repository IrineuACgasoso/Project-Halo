import pygame
import math
import os
from os.path import join
from colaboradores import TelaColaboradores
from feats.assets import ASSETS
from settings import *  # largura_tela, altura_tela, fps
# ------------------- MENUS -------------------


class MenuPrincipal:
    def __init__(self, game):
        self.game = game
        
        # Tentativa de carregar a fonte Orbitron enviada (Bold para o menu)
        # Se preferir a VariableFont ou outro peso, mude o caminho abaixo
        try:
            self.font_path = "assets/fonts/orbitron/Orbitron-Bold.ttf" # Ajuste o caminho conforme sua pasta
            self.font = pygame.font.Font(self.font_path, 40)
        except:
            self.font = pygame.font.SysFont('Consolas', 36, bold=True)
        
        # --- CARREGAMENTO DAS CAMADAS ---
        self.camada_fundo = ASSETS['menu']['menuback']
        self.camada_planeta = ASSETS['menu']['menuback2']
        self.camada_anel = ASSETS['menu']['haloring']
        self.logo = ASSETS['menu']['logo']
        
        # --- VARIÁVEIS DE ANIMAÇÃO ---
        self.timer = 0
        self.opcoes = ["START GAME", "RANKING", "CREATORS", "QUIT"]
        self.selecionada = 0

        # Cores Estilo Halo
        self.COR_BRANCO_SEL = (250, 250, 255)
        self.COR_CIANO_NEON = (0, 255, 255)
        self.COR_AZUL_MENU = (70, 140, 210) # Azul mais sóbrio para itens não focados

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
        self.timer += 0.008 
        tela.blit(self.camada_fundo, (0, 0))
        
        # --- LÓGICA DE ZOOM (Mantida conforme original) ---
        oscilacao = (math.sin(self.timer) * 0.7) + (math.sin(self.timer * 2) * 0.3)
        curva_respiracao = (oscilacao + 1.0) / 2.0
        variacao_zoom = curva_respiracao * 0.25
        
        # Camada Planeta
        p_z = 1.01 + (variacao_zoom * 0.2)
        img_p = pygame.transform.smoothscale(self.camada_planeta, (int(largura_tela*p_z), int(altura_tela*p_z)))
        tela.blit(img_p, img_p.get_rect(center=(largura_tela//2, altura_tela//2)))

        # Camada Anel
        a_z = 1.02 + variacao_zoom
        img_a = pygame.transform.smoothscale(self.camada_anel, (int(largura_tela*a_z), int(altura_tela*a_z)))
        tela.blit(img_a, img_a.get_rect(center=(largura_tela//2, altura_tela//2)))

        # Logo
        brilho_logo = int(200 + math.sin(self.timer * 3) * 55)
        self.logo.set_alpha(brilho_logo)
        tela.blit(self.logo, self.logo.get_rect(center=(largura_tela//2, 120)))

        # --- OPÇÕES ESTILO HALO ---
        # --- OPÇÕES ---
        for i, texto in enumerate(self.opcoes):
            sel = (i == self.selecionada)
            
            if sel:
                # 1. Desenha o Glow em 8 direções para cobrir as diagonais
                alpha_glow = int(120 + math.sin(self.timer * 8) * 50)
                
                rect_base = None # Será definido abaixo
                
                # Desenhamos o glow ANTES do texto principal
                # Usamos um range maior de offsets para um brilho mais espesso
                for offset in range(1, 5):
                    glow_surf = self.font.render(texto, True, self.COR_CIANO_NEON)
                    glow_surf.set_alpha(max(0, alpha_glow // offset))
                    
                    if rect_base is None:
                        rect_base = glow_surf.get_rect(center=(largura_tela // 2, 300 + i * 65))
                    
                    # Lista de direções (x, y): Cardeais + Diagonais
                    direcoes = [
                        (-offset, 0), (offset, 0), (0, -offset), (0, offset), # Cardeais
                        (-offset, -offset), (offset, -offset), (-offset, offset), (offset, offset) # Diagonais
                    ]
                    
                    for dx, dy in direcoes:
                        tela.blit(glow_surf, (rect_base.x + dx, rect_base.y + dy))

                # 2. Desenha o Texto Principal em BRANCO por cima do glow
                txt_surf = self.font.render(texto, True, self.COR_BRANCO_SEL)
                rect = txt_surf.get_rect(center=(largura_tela // 2, 300 + i * 65))
                tela.blit(txt_surf, rect)

            else:
                # Texto Azul normal (não selecionado)
                txt_surf = self.font.render(texto, True, self.COR_AZUL_MENU)
                rect = txt_surf.get_rect(center=(largura_tela // 2, 300 + i * 65))
                tela.blit(txt_surf, rect)

class MenuPausa:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont(None, 48)
        self.opcoes = ["Continuar", "Sair para Menu"]
        self.selecionada = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                self.selecionada = (self.selecionada - 1) % len(self.opcoes)
            elif event.key == pygame.K_s:
                self.selecionada = (self.selecionada + 1) % len(self.opcoes)
            elif event.key == pygame.K_RETURN:
                return self.opcoes[self.selecionada]
        return None

    def draw(self, tela):
        tela.fill((10, 10, 10))
        for i, texto in enumerate(self.opcoes):
            cor = (0, 200, 200) if i == self.selecionada else (200, 200, 200)
            txt = self.font.render(texto, True, cor)
            tela.blit(txt, (120, 120 + i * 50))


class TelaGameOver:
    def __init__(self, game):
        self.game = game
        self.bg = pygame.image.load(join('assets', 'img', 'game_over.png')).convert_alpha()
        self.bg = pygame.transform.scale(self.bg, (largura_tela, altura_tela))
        self.som = pygame.mixer.Sound(join('assets', 'sounds', 'game_over.wav'))
        pygame.mixer.music.set_volume(0.3)
        self.som_tocado = False

    def draw(self, tela):
        if not self.som_tocado:
            self.som.play()
            self.som_tocado = True
        tela.blit(self.bg, (0, 0))
        
