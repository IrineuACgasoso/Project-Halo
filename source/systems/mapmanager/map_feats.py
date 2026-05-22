import pygame


class MapFeats:
    def calcular_puxo_void(self, player_pos):
        for i, zona in enumerate(self.zonas_void):
            if zona.collidepoint(player_pos):
                # Define o alvo (ponto de atração)
                ponto_alvo = self.void_points[i] if i < len(self.void_points) else self.void_points[0]
                
                direcao = (ponto_alvo - player_pos)
                distancia = direcao.length()
                
                if distancia > 0:
                    # Retorna (Vetor de Força, Ponto Alvo, Distância)
                    return direcao.normalize() * 2.5, ponto_alvo, distancia
                    
        # Se não estiver no vácuo, retorna valores nulos
        return pygame.math.Vector2(0, 0), None, 9999