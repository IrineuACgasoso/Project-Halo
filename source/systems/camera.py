import pygame
import random

class Camera:
    def __init__(self, largura_tela, altura_tela, mapa):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        self.mapa = mapa
        self.offset = pygame.math.Vector2()
        
        # Atributos para o Shake
        self.shake_intensidade = 0
        self.shake_timer = 0
        self.shake_offset = pygame.math.Vector2()

    def shake(self, intensidade, duracao=200):
        self.shake_intensidade = intensidade
        self.shake_timer = pygame.time.get_ticks() + duracao

    def update(self, player_pos):
        # 1. Seguir o Jogador (centralizar)
        self.offset.x = player_pos.x - self.largura_tela / 2
        self.offset.y = player_pos.y - self.altura_tela / 2

        # 2. Limitar às bordas do mapa
        self.offset.x = max(0, min(self.offset.x, self.mapa.largura_mapa_pixels - self.largura_tela))
        self.offset.y = max(0, min(self.offset.y, self.mapa.altura_mapa_pixels - self.altura_tela))

        # 3. Aplicar o Shake se estiver ativo
        if pygame.time.get_ticks() < self.shake_timer:
            self.shake_offset.x = random.uniform(-self.shake_intensidade, self.shake_intensidade)
            self.shake_offset.y = random.uniform(-self.shake_intensidade, self.shake_intensidade)
        else:
            self.shake_offset = pygame.math.Vector2(0, 0)

    def apply(self, entidade):
        # Retorna o rect da entidade ajustado pela câmera + shake
        return entidade.rect.topleft - self.offset + self.shake_offset

    def apply_pos(self, posicao):
        # Retorna uma posição ajustada (para draw de linhas/partículas)
        return posicao - self.offset + self.shake_offset