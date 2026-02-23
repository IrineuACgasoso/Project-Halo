import pygame
import random
from random import randint
from feats.assets import *

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



class PrometheanTeleport(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_pos, pixel_size, offset_xy, num_quad, grupos, game):
        super().__init__(grupos)
        self.game = game
        self.posicao = pygame.math.Vector2(start_pos)
        self.target_pos = pygame.math.Vector2(target_pos)
        self.pixel_size = pixel_size
        self.offset_xy = offset_xy
        self.num_quad = num_quad
        
        # Aparência "Digital" (Vários pixels laranjas)
        self.image = pygame.Surface((self.offset_xy, self.offset_xy), pygame.SRCALPHA)
        self.cor_promethean = (255, 120, 0) # Laranja
        self.rect = self.image.get_rect(center=self.posicao)
        
        # Velocidade do teleporte (A partícula viaja rápido)
        self.velocidade = 800 
        
        # Calcula direção
        self.direcao = (self.target_pos - self.posicao)
        if self.direcao.length() > 0:
            self.direcao = self.direcao.normalize()
        
        # Timer para animação interna
        self.last_sparkle = 0

    def update(self, delta_time):
        # Movimento
        move_amount = self.direcao * self.velocidade * delta_time
        
        # Verifica se passou do ponto (chegou no destino)
        distancia_total = self.posicao.distance_to(self.target_pos)
        passo_atual = move_amount.length()
        
        if passo_atual >= distancia_total:
            self.posicao = self.target_pos
            self.kill() # A partícula morre para avisar o Knight que chegou
        else:
            self.posicao += move_amount

        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        
        # Efeito Visual (Pixels piscando/mudando)
        self.animar_pixels()

    def animar_pixels(self):
        # Redesenha a superfície a cada frame para parecer "glitch/dados"
        self.image.fill((0,0,0,0)) # Limpa
        
        # Desenha 20 a 30 quadradinhos aleatórios (efeito digital)
        for _ in range(randint(self.num_quad[0], self.num_quad[1])):
            tamanho = randint(self.pixel_size[0], self.pixel_size[1])
            offset_x = randint(0, self.offset_xy - tamanho)
            offset_y = randint(0, self.offset_xy - tamanho)
            # Varia entre laranja e branco para brilho
            cor = self.cor_promethean if randint(0,10) > 2 else (255, 255, 255)
            
            pygame.draw.rect(self.image, cor, (offset_x, offset_y, tamanho, tamanho))

class Portal(pygame.sprite.Sprite):
    def __init__(self, pos, grupos):
        super().__init__(grupos)
        self.image = ASSETS['effects']['portal']
        # Cria a máscara baseada nos pixels não transparentes da imagem
        self.mask = pygame.mask.from_surface(self.image)
        # Desenha um círculo ciano para debug ou visualização
        self.rect = self.image.get_rect(center=pos)


class LaserWarning(pygame.sprite.Sprite):
    def __init__(self, start_pos, end_pos, grupos, game,
                 cor_laser=(250, 0, 0, 30), # Vermelho transparente padrão
                 largura=300):
        
        super().__init__(grupos)
        self.game = game
        self.start_pos = pygame.math.Vector2(start_pos)
        
        direcao = pygame.math.Vector2(end_pos) - self.start_pos
        if direcao.length() > 0:
            direcao.normalize_ip()
        else:
            direcao = pygame.math.Vector2(1, 0)
            
        self.end_pos = self.start_pos + direcao * 2000
        self.duracao = 1500
        self.largura = 300
        self.tempo_criacao = pygame.time.get_ticks()

        # --- Atributos Parametrizados ---
        self.cor_laser = cor_laser
        self.largura = largura

        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.start_pos)

    def draw(self, surface, offset):
        agora = pygame.time.get_ticks()
        if agora - self.tempo_criacao < self.duracao:
            start_pos_ajustada = self.start_pos - offset
            end_pos_ajustada = self.end_pos - offset
            
            # 1. Cria uma surface temporária com suporte a transparência
            temp_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            
            # 2. Desenha o laser muito transparente nela (Alpha = 30)
            pygame.draw.line(temp_surface, self.cor_laser, start_pos_ajustada, end_pos_ajustada, self.largura)
            
            # 3. Cola o resultado na tela principal
            surface.blit(temp_surface, (0, 0))

    def update(self, delta_time):
        if pygame.time.get_ticks() - self.tempo_criacao >= self.duracao:
            self.kill()


