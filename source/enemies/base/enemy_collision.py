import pygame
from source.utils.collision_utils import projetar_fora_da_linha


class EnemyCollision:
    @property
    def collision_rect(self):
        """Retorna o retângulo de colisão para este inimigo."""
        return self.rect
    
    def aplicar_colisao_mapa(self, paredes_ativas):
        # A mesma lógica de iteração que usamos no Player
        for _ in range(self.iteracoes_colisao_mapa): # Inimigos podem usar 2 iterações para poupar processamento
            for parede in paredes_ativas:
                pontos = parede['pontos']
                for i in range(len(pontos) - 1):
                    p1 = pontos[i]
                    p2 = pontos[i+1]
                    
                    push = projetar_fora_da_linha(self.posicao, p1, p2, self.raio_colisao_mapa)
                    if push:
                        self.posicao += push

            