from game import * 
from enemies import *
from items import *
from weapon import *

class ProjetilInimigoBase(pygame.sprite.Sprite):
    def __init__(self, posicao_inicial, grupos, jogador, game, dano, velocidade, duracao):
        super().__init__(grupos)
        self.jogador = jogador
        self.game = game
        self.posicao = pygame.math.Vector2(posicao_inicial)
        
        #status
        self.dano = dano
        self.velocidade = velocidade
        self.duracao = duracao

        # Aparência
        self.image = pygame.Surface((20,20))
        self.rect = self.image.get_rect(center=self.posicao)

        # Calcula a direção para o jogador
        direcao_para_jogador = self.jogador.posicao - self.posicao
        if direcao_para_jogador.length() > 0:
            self.direcao = direcao_para_jogador.normalize()
        else:
            self.direcao = pygame.math.Vector2(0, 0)
        
        self.tempo_criacao = pygame.time.get_ticks()

    def update(self, delta_time):
        self.posicao += self.direcao * self.velocidade * delta_time
        self.rect.center = self.posicao
        
        # Mata o projétil se o tempo de vida se esgotar
        if pygame.time.get_ticks() - self.tempo_criacao >= self.duracao:
            self.kill()

class PlasmaGun(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, tamanho, dano, velocidade):
        super().__init__(posicao_inicial, grupos, jogador, game, dano=dano, velocidade=velocidade, duracao=5000)
        self.image = pygame.image.load(join('assets', 'img', 'plasmagun.png'))
        self.image = pygame.transform.scale(self.image, tamanho)
        self.rect = self.image.get_rect(center=self.posicao)

class Carabin(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, tamanho, dano, velocidade, duracao =3000):
        super().__init__(posicao_inicial, grupos, jogador, game, dano=dano, velocidade=velocidade, duracao=duracao)
        self.image = pygame.image.load(join('assets', 'img', 'carabin.png'))
        self.image = pygame.transform.scale(self.image, tamanho)
        self.rect = self.image.get_rect(center=self.posicao)

class Dizimator(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, tamanho, dano, velocidade, duracao = 2500):
        super().__init__(posicao_inicial, grupos, jogador, game, dano=dano, velocidade=velocidade, duracao=duracao)
        self.image = pygame.image.load(join('assets', 'img', 'dizimator.png'))
        self.image = pygame.transform.scale(self.image, tamanho)
        self.rect = self.image.get_rect(center=self.posicao)

