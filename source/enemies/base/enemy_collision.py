import pygame
from source.utils.collision_utils import sair_das_paredes


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
    
    def aplicar_colisao_mapa(self, grade_paredes):
        """Empurra o inimigo para fora das paredes perto DELE (até a C1 eram as perto do jogador,
        e um inimigo longe dele atravessava paredes)."""
        sair_das_paredes(self.posicao, self.raio_colisao_mapa, grade_paredes,
                         self.iteracoes_colisao_mapa)   # 2 iterações para poupar processamento
