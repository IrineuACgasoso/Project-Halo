import pygame
import random
from source.feats.assets import *

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


class Portal(pygame.sprite.Sprite):
    def __init__(self, pos, grupos):
        super().__init__(grupos)
        self.image = ASSETS['effects']['portal']
        # Cria a máscara baseada nos pixels não transparentes da imagem
        self.mask = pygame.mask.from_surface(self.image)
        # Desenha um círculo ciano para debug ou visualização
        self.rect = self.image.get_rect(center=pos)


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



class EfeitoFaiscas(pygame.sprite.Sprite):
    """
    Pequeno estouro de faíscas, usado no contra-ataque dos espinhos
    (e reaproveitável em qualquer outro impacto/reflexo de dano).
    Não depende de nenhum asset — desenha tudo proceduralmente e some
    sozinho depois de `duracao` ms.
    """

    def __init__(self, posicao, grupos, cor=(255, 210, 90), quantidade=10, duracao=280):
        super().__init__(grupos)
        self.posicao = pygame.math.Vector2(posicao)
        self.cor = cor
        self.duracao = duracao
        self.criado_em = pygame.time.get_ticks()

        self.particulas = [
            {
                'dir': pygame.math.Vector2(1, 0).rotate(random.uniform(0, 360)),
                'vel': random.uniform(120, 260),
                'tam': random.uniform(2, 5),
            }
            for _ in range(quantidade)
        ]

        tam_canvas = 240
        self.image = pygame.Surface((tam_canvas, tam_canvas), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.posicao)
        self._centro_local = pygame.math.Vector2(tam_canvas / 2, tam_canvas / 2)

    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        decorrido = agora - self.criado_em
        if decorrido >= self.duracao:
            self.kill()
            return

        progresso = decorrido / self.duracao
        alpha = max(0, int(255 * (1 - progresso)))

        self.image.fill((0, 0, 0, 0))
        for p in self.particulas:
            offset = p['dir'] * p['vel'] * (decorrido / 1000)
            pos = self._centro_local + offset
            raio = max(0.5, p['tam'] * (1 - progresso))
            pygame.draw.circle(self.image, (*self.cor, alpha), pos, raio)

        self.rect.center = self.posicao