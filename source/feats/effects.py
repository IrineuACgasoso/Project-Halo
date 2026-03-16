import pygame
import random
import math
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
    def __init__(self, owner, alvo, grupos, game, 
                 cor_laser=(250, 0, 0, 30), 
                 largura=300, duracao=1500):
        
        super().__init__(grupos)
        self.game = game
        self.owner = owner  # Inimigo que está mirando
        self.alvo = alvo    # Geralmente o jogador
        
        self.duracao = duracao
        self.largura = largura
        self.cor_laser = cor_laser
        self.tempo_criacao = pygame.time.get_ticks()

        # Posições iniciais
        self.start_pos = pygame.math.Vector2(owner.posicao)
        self.end_pos = pygame.math.Vector2(alvo.posicao)
        
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect()

    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        
        # Se o tempo acabou ou quem disparou morreu, remove o aviso
        if agora - self.tempo_criacao >= self.duracao or not self.owner.alive():
            self.kill()
            return

        # 1. Atualiza a posição de origem (caso o inimigo se mova)
        self.start_pos = pygame.math.Vector2(self.owner.posicao)

        # 2. Calcula a direção em direção ao alvo
        direcao = self.alvo.posicao - self.start_pos
        
        if direcao.length() > 0:
            direcao = direcao.normalize()
        else:
            direcao = pygame.math.Vector2(1, 0)

        # 3. Projeta o laser para bem longe na direção do alvo (ex: 3000 pixels)
        self.end_pos = self.start_pos + direcao * 3000

    def draw(self, surface, offset):
        # O desenho acontece em uma surface temporária para suportar o Alpha da linha
        temp_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        
        start_pos_ajustada = self.start_pos - offset
        end_pos_ajustada = self.end_pos - offset
        
        # Efeito opcional: fazer o laser "piscar" ou ficar mais forte perto do disparo
        tempo_passado = pygame.time.get_ticks() - self.tempo_criacao
        progresso = tempo_passado / self.duracao
        alpha = int(30 + (progresso * 90)) # Fica levemente mais visível com o tempo
        
        cor_com_alpha = (*self.cor_laser[:3], alpha)

        # Desenha a linha de aviso
        pygame.draw.line(temp_surface, cor_com_alpha, start_pos_ajustada, end_pos_ajustada, self.largura)
        
        # Cola na superfície principal
        surface.blit(temp_surface, (0, 0))

class RaioEscudo(pygame.sprite.Sprite):
    def __init__(self, fonte, alvo, grupos, cor=(255, 40, 0)):
        super().__init__(grupos)
        self.fonte = fonte
        self.alvo = alvo
        self.cor = cor
        
        self.duracao = 250 
        self.tempo_criacao = pygame.time.get_ticks()
        
        self.gerar_imagem()

    def gerar_imagem(self):
        # 1. Usa o rect.center para garantir que o raio saia do meio do inimigo
        pos_fonte = pygame.math.Vector2(self.fonte.rect.center)
        pos_alvo = pygame.math.Vector2(self.alvo.rect.center)

        # 2. Bounding Box
        min_x = min(pos_fonte.x, pos_alvo.x)
        max_x = max(pos_fonte.x, pos_alvo.x)
        min_y = min(pos_fonte.y, pos_alvo.y)
        max_y = max(pos_fonte.y, pos_alvo.y)

        # 3. Força valores inteiros na criação da Surface
        padding = 15
        width = int(max(max_x - min_x + padding * 2, 1))
        height = int(max(max_y - min_y + padding * 2, 1))

        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # 4. Posição global no mundo
        topleft_global = pygame.math.Vector2(min_x - padding, min_y - padding)
        self.rect = self.image.get_rect(topleft=topleft_global)
        
        # 5. A câmera precisa do self.posicao para aplicar o offset!
        self.posicao = pygame.math.Vector2(self.rect.center)

        # 6. Calcula a posição local desenhando na Surface
        local_start = pos_fonte - topleft_global
        local_end = pos_alvo - topleft_global

        pygame.draw.line(self.image, (*self.cor, 100), local_start, local_end, 15) 
        pygame.draw.line(self.image, (255, 255, 255), local_start, local_end, 3)

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()
        if agora - self.tempo_criacao > self.duracao or not self.alvo.alive() or not self.fonte.alive():
            self.kill()
        else:
            self.gerar_imagem()


class ContinuousBeam:
    def __init__(self, owner, color=(255, 0, 0), largura_base=4, dano_por_segundo=50, suavizacao=0.1):
        self.owner = owner  # O inimigo que disparou
        self.game = owner.game
        self.color = color
        self.largura_base = largura_base
        self.dps = dano_por_segundo
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
            self.game.player.tomar_dano_direto(self.dps * delta_time)

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