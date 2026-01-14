import pygame
import random

class DustParticle(pygame.sprite.Sprite):
    def __init__(self, posicao, grupos):
        super().__init__(grupos)
        # Tamanho aleatório para variação visual
        tamanho = random.randint(4, 8)
        self.image = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
        
        # Cor de terra/lodo (marrom esverdeado)
        cor = random.choice([(70, 50, 30), (40, 60, 30), (100, 80, 50)])
        pygame.draw.circle(self.image, cor, (tamanho//2, tamanho//2), tamanho//2)
        
        self.rect = self.image.get_rect(center=posicao)
        
        # Velocidade: explode um pouco para os lados e para cima
        self.direcao = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-2, -0.5))
        self.velocidade = random.uniform(50, 150)
        self.vida = 255 # Usado para o Alpha (transparência)

    def update(self, delta_time):
        # Movimento
        self.rect.center += self.direcao * self.velocidade * delta_time
        
        # Fade out (sumir gradualmente)
        self.vida -= 400 * delta_time
        if self.vida <= 0:
            self.kill()
        else:
            self.image.set_alpha(int(self.vida))