import pygame
import math

class ContinuousBeam:
    def __init__(self, owner, color=(255, 0, 0), largura_base=4, dano_por_segundo=50, suavizacao=0.1):
        self.owner = owner  # O inimigo que disparou
        self.game = owner.game
        self.color = color
        self.largura_base = largura_base
        self.dano_por_segundo = dano_por_segundo
        self.mira_atual = pygame.math.Vector2(owner.posicao)
        # Agora o parâmetro é definido na criação da instância
        # 0.01 = Muito lento (estilo "mira pesada")
        # 0.1  = Padrão
        # 1.0  = Instantâneo (colado no jogador)
        self.suavizacao = suavizacao

    def update(self, delta_time, alvo_pos):
        # Persegue a posição do jogador suavemente
        self.mira_atual = self.mira_atual.lerp(alvo_pos, self.suavizacao)
        
        # Lógica de Dano (Área de impacto na ponta do laser)
        distancia_ponta = (self.mira_atual - self.game.player.posicao).length()
        if distancia_ponta < 50: # Raio de dano da ponta do feixe
            self.game.player.tomar_dano_direto(self.dano_por_segundo * delta_time)

    def draw(self, superficie, deslocamento, origem_offset=None):
        # Define o ponto de partida (se o inimigo tiver um canhão específico)
        p1 = (self.owner.posicao + origem_offset if origem_offset else self.owner.posicao) - deslocamento
        p2 = self.mira_atual - deslocamento
        
        # Efeito visual de "pulsação"
        oscilacao = math.sin(pygame.time.get_ticks() * 0.02) * 2
        largura_final = max(1, int(self.largura_base + oscilacao))
        
        # Desenha o rastro (brilho externo e centro branco)
        pygame.draw.line(superficie, self.color, p1, p2, largura_final + 4)
        pygame.draw.line(superficie, (255, 255, 255), p1, p2, max(1, largura_final // 2))
        
        # Brilho na ponta (impacto)
        pygame.draw.circle(superficie, self.color, p2, 8 + oscilacao)

