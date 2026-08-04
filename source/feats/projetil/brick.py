import pygame
from .projetil import ProjetilUniversal
from source.windows.settings import largura_tela, altura_tela

class Brick(ProjetilUniversal):
    def __init__(self, posicao_inicial, grupos, jogador, game, direcao, dano, velocidade, rebatidas):
        super().__init__(
            posicao_inicial=posicao_inicial, 
            grupos=grupos, 
            game=game, 
            dono='PLAYER', 
            sprite_key='pingpong', 
            tamanho=(48, 32), 
            dano=dano, 
            velocidade=velocidade, 
            direcao_custom=direcao, 
            piercing=float('inf'),
            rotacionar=True # Bola não precisa girar imagem
        ) 
        self.jogador = jogador
        self.rebatidas = rebatidas
        self.inimigos_atingidos = set()

    def obter_imagem_base(self, sprite_key, tamanho):
        """"""
        base_key = f"base_{sprite_key}_{tamanho[0]}x{tamanho[1]}"
        base = pygame.Surface(tamanho, pygame.SRCALPHA)
    
        rect_corpo = pygame.Rect(0, 0, tamanho[0], tamanho[1])
    
        cor_corpo = (255, 110, 110)
        pygame.draw.rect(base, cor_corpo, rect_corpo, border_radius=3)
        pygame.draw.rect(base, (35, 37, 41), rect_corpo, 1, border_radius=3)
    
        # Pinos de contato laterais (silhueta de matriz de dados)
        cor_pino = (255, 220, 220)
        for i in range(3):
            y = rect_corpo.y + 4 + i * max(1, (tamanho[1] - 12) // 2)
            x = rect_corpo.x + 2 + i * max(2, (tamanho[0] - 6) // 2)
            pygame.draw.line(base, cor_pino, (rect_corpo.x + tamanho[0], y), (rect_corpo.x, y))
            pygame.draw.line(base, cor_pino, (x, rect_corpo.y + tamanho[1]), (x, rect_corpo.y))
    
            ProjetilUniversal.GLOBAL_CACHE[base_key] = base
        return ProjetilUniversal.GLOBAL_CACHE[base_key]

    def update(self, delta_time):
        super().update(delta_time)

        # Definimos as bordas
        margem = 24 # Pequena margem de segurança baseada no tamanho da sprite
        borda_esq = self.jogador.posicao.x - (largura_tela / 2) + margem
        borda_dir = self.jogador.posicao.x + (largura_tela / 2) - margem
        borda_topo = self.jogador.posicao.y - (altura_tela / 2) + margem
        borda_baixo = self.jogador.posicao.y + (altura_tela / 2) - margem

        # Checa colisão Eixo X
        if self.posicao.x <= borda_esq:
            self.posicao.x = borda_esq # FORÇA POSIÇÃO
            self.direcao.x *= -1
            self.rebatidas -= 1
            self.inimigos_atingidos.clear()

        elif self.posicao.x >= borda_dir:
            self.posicao.x = borda_dir # FORÇA POSIÇÃO
            self.direcao.x *= -1
            self.rebatidas -= 1
            self.inimigos_atingidos.clear()

        # Checa colisão Eixo Y
        if self.posicao.y <= borda_topo:
            self.posicao.y = borda_topo # FORÇA POSIÇÃO
            self.direcao.y *= -1
            self.rebatidas -= 1
            self.inimigos_atingidos.clear()

        elif self.posicao.y >= borda_baixo:
            self.posicao.y = borda_baixo # FORÇA POSIÇÃO
            self.direcao.y *= -1
            self.rebatidas -= 1
            self.inimigos_atingidos.clear()

        if self.rebatidas < 0: # < 0 para garantir que a última rebatida ainda viaje
            self.kill()

    def ao_atingir_alvo(self, alvo):
        if alvo and not getattr(alvo, 'invulneravel', False) and alvo not in self.inimigos_atingidos:
            if hasattr(alvo, 'receber_dano'):
                alvo.receber_dano(self.dano)
                self.inimigos_atingidos.add(alvo)

        



