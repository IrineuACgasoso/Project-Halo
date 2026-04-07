import pygame
import random
from source.feats.assets import ASSETS 

class Items(pygame.sprite.Sprite):
    def __init__(self, posicao, tipo, grupos):
        super().__init__(grupos)
        
        # Busca a imagem no ASSETS (agora centralizado)
        self.image = ASSETS['items'].get(tipo)
        if not self.image: # Fallback caso o tipo não exista
             self.image = ASSETS['items']['shard']
             
        self.rect = self.image.get_rect(center=posicao)
        self.posicao = pygame.math.Vector2(posicao)
        self.posicao_final_y = self.posicao.y
        
        self.velocidade = 180 
        self.gravidade = 500
        self.dropping = True
        self.tipo = tipo

    @classmethod
    def spawn_drop(cls, posicao, grupos, tipo, qtd, probabilidade):
        """
        Método estático para gerenciar a criação de drops.
        Inimigo chama: Items.spawn_drop(pos, grupos, 'item', qtd, %)
        """
        if random.randint(1, 100) <= probabilidade:
            for _ in range(qtd):
                # Desvio aleatório para os itens não ficarem colados
                offset = pygame.math.Vector2(random.randint(-30, 30), random.randint(-30, 30))
                cls(posicao + offset, tipo, grupos)

    def update(self, delta_time):
        if self.dropping:
            self.velocidade -= self.gravidade * delta_time
            self.posicao.y -= self.velocidade * delta_time
            
            if self.posicao.y >= self.posicao_final_y:
                self.posicao.y = self.posicao_final_y
                self.dropping = False
            
            self.rect.centery = round(self.posicao.y)