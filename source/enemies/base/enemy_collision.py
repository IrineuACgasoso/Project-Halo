import pygame
from source.utils.collision_utils import projetar_fora_da_linha


class EnemyCollision:
    @property
    def collision_rect(self):
        """Retorna o retângulo de colisão para este inimigo."""
        return self.rect
    
    def verificar_posicao_valida(self, posicao_alvo):
        """
        Verifica se a posição escolhida para teleporte, invocação ou spawn
        é válida (está dentro da zona de navegação do chão).
        """
        # Se você passar uma tupla ou lista (ex: (x, y)), ele converte sozinho
        if isinstance(posicao_alvo, (tuple, list)):
            vetor_posicao = pygame.math.Vector2(posicao_alvo[0], posicao_alvo[1])
        else:
            vetor_posicao = posicao_alvo
            
        # Checa por segurança se o jogo e o mapa já estão instanciados
        if hasattr(self, 'game') and hasattr(self.game, 'mapa'):
            return self.game.mapa.posicao_e_valida(vetor_posicao)
            
        return False
    
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

            