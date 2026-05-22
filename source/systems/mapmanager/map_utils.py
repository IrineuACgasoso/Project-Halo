import pygame

class MapUtils:
    def posicao_e_valida(self, pos_vetor):
        """Verifica se uma posição está dentro de alguma área de navegação (chão)."""
        # Se não houver zonas de navegação definidas, aceita qualquer lugar (segurança)
        if not self.navigation_zones:
            return True
        
        for zone in self.navigation_zones:
            if zone.collidepoint(pos_vetor.x, pos_vetor.y):
                return True
        return False
    

    # Função extra para testar se as linhas e pontos estão no lugar certo
    def draw_debug(self, surface, camera_offset):
        for p in self.paredes:
            pts = [p_vec - camera_offset for p_vec in p['pontos']]
            if len(pts) > 1:
                pygame.draw.lines(surface, "green", False, pts, 2)

        # Zonas de Navegação em Azul (Invisíveis no jogo, visíveis no debug)
        for zone in self.navigation_zones:
            debug_rect = zone.copy()
            debug_rect.x -= camera_offset.x
            debug_rect.y -= camera_offset.y
            pygame.draw.rect(surface, (0, 100, 255), debug_rect, 2)

        for sp in self.pontos_de_spawn:
            pos_tela = sp - camera_offset
            pygame.draw.circle(surface, "red", (int(pos_tela.x), int(pos_tela.y)), 5)