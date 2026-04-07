import pygame
import math
import os
from os.path import join
from source.windows.settings import largura_tela, altura_tela
from source.feats.assets import ASSETS

class MenuPrincipal:
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
        self.opcoes = ["START GAME", "RANKING", "CREATORS", "QUIT"]
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

    def draw_glow_text(self, tela, texto, x, y, selecionado, cor_glow=None, align="center", fonte_custom=None):
        """Função auxiliar para desenhar texto com estilo Halo (Sem marcadores)"""
        if cor_glow is None:
            cor_glow = self.COR_CIANO_NEON
        
        fonte_usada = fonte_custom if fonte_custom else self.font

        if selecionado:
            alpha_glow = int(120 + math.sin(self.timer * 8) * 50)
            rect_base = None
            
            # 1. Glow em 8 direções
            for offset in range(1, 4):
                glow_surf = fonte_usada.render(texto, True, cor_glow)
                glow_surf.set_alpha(max(0, alpha_glow // offset))
                
                if rect_base is None:
                    if align == "left":
                        rect_base = glow_surf.get_rect(midleft=(x, y))
                    else:
                        rect_base = glow_surf.get_rect(center=(x, y))
                
                direcoes = [
                    (-offset, 0), (offset, 0), (0, -offset), (0, offset),
                    (-offset, -offset), (offset, -offset), (-offset, offset), (offset, offset)
                ]
                
                for dx, dy in direcoes:
                    tela.blit(glow_surf, (rect_base.x + dx, rect_base.y + dy))

            # 2. Texto Branco por cima
            txt_surf = fonte_usada.render(texto, True, self.COR_BRANCO_SEL)
            
            if align == "left":
                rect = txt_surf.get_rect(midleft=(x, y))
            else:
                rect = txt_surf.get_rect(center=(x, y))
                
            tela.blit(txt_surf, rect)
                
        else:
            # Texto não selecionado
            txt_surf = fonte_usada.render(texto, True, self.COR_AZUL_MENU)
            if align == "left":
                rect = txt_surf.get_rect(midleft=(x, y))
            else:
                rect = txt_surf.get_rect(center=(x, y))
            tela.blit(txt_surf, rect)

    def draw(self, tela):
        self.timer += 0.008 
        tela.blit(self.camada_fundo, (0, 0))
        
        oscilacao = (math.sin(self.timer) * 0.7) + (math.sin(self.timer * 2) * 0.3)
        curva = (oscilacao + 1.0) / 2.0
        v_zoom = curva * 0.25
        
        p_z = 1.01 + (v_zoom * 0.2)
        img_p = pygame.transform.smoothscale(self.camada_planeta, (int(largura_tela*p_z), int(altura_tela*p_z)))
        tela.blit(img_p, img_p.get_rect(center=(largura_tela//2, altura_tela//2)))

        a_z = 1.02 + v_zoom
        img_a = pygame.transform.smoothscale(self.camada_anel, (int(largura_tela*a_z), int(altura_tela*a_z)))
        tela.blit(img_a, img_a.get_rect(center=(largura_tela//2, altura_tela//2)))

        brilho = int(200 + math.sin(self.timer * 3) * 55)
        self.logo.set_alpha(brilho)
        tela.blit(self.logo, self.logo.get_rect(center=(largura_tela//2, 120)))

        for i, texto in enumerate(self.opcoes):
            self.draw_glow_text(tela, texto, largura_tela//2, 300 + i * 65, i == self.selecionada)


class MenuPausa:
    def __init__(self, game):
        self.game = game
        if hasattr(game.menu_principal, 'font'):
            self.font = game.menu_principal.font
        else:
            self.font = pygame.font.SysFont(None, 48)
            
        self.opcoes = ["RESUME", "EXIT TO MENU"]
        self.selecionada = 0
        self.timer = 0 

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
        self.timer += 0.01
        s = pygame.Surface((largura_tela, altura_tela))
        s.set_alpha(180)
        s.fill((0, 10, 20))
        tela.blit(s, (0,0))
        
        titulo = self.font.render("SYSTEM PAUSED", True, (0, 255, 255))
        rect_t = titulo.get_rect(center=(largura_tela//2, altura_tela//2 - 100))
        tela.blit(titulo, rect_t)
        
        for i, texto in enumerate(self.opcoes):
            self.game.menu_principal.timer = self.timer
            self.game.menu_principal.draw_glow_text(tela, texto, largura_tela//2, altura_tela//2 + i * 65, i == self.selecionada)


class TelaGameOver:
    def __init__(self, game):
        self.game = game
        self.font_opcoes = game.menu_principal.font
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
        self.game.menu_principal.timer = self.timer
        self.game.menu_principal.draw_glow_text(
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
            self.game.menu_principal.draw_glow_text(
                tela, 
                texto, 
                pos_x_esquerda, 
                altura_tela//2 + 50 + i * 70, 
                i == self.selecionada,
                align="left"
            )