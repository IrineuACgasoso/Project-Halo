import math
import pygame

from .menu_constants import *
from source.windows.settings import largura_tela, altura_tela


class MenuDraw:
    def draw_glow_text(self, tela, texto, x, y, selecionado, cor_glow=None, align="center", fonte_custom=None):
        """Função auxiliar para desenhar texto com estilo Halo (Sem marcadores)"""
        if cor_glow is None:
            cor_glow = COR_CIANO_NEON
        
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
            txt_surf = fonte_usada.render(texto, True, COR_BRANCO_SEL)
            
            if align == "left":
                rect = txt_surf.get_rect(midleft=(x, y))
            else:
                rect = txt_surf.get_rect(center=(x, y))
                
            tela.blit(txt_surf, rect)
                
        else:
            # Texto não selecionado
            txt_surf = fonte_usada.render(texto, True, COR_AZUL_MENU)
            if align == "left":
                rect = txt_surf.get_rect(midleft=(x, y))
            else:
                rect = txt_surf.get_rect(center=(x, y))
            tela.blit(txt_surf, rect)

    def draw_overlay(self, tela):
        s = pygame.Surface((largura_tela, altura_tela))
        s.set_alpha(180)
        s.fill((0, 10, 20))
        tela.blit(s, (0,0))

    def draw_menu_background(self, tela):
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