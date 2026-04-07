import pygame
import math
from source.windows.settings import *
from source.player.player import *
from source.feats.assets import ASSETS


class Arma(ABC):
    def __init__(self, jogador, **kwargs):
        self.jogador = jogador
        self.nivel = 1
        self.dano = 0
        self.velocidade = 0
        self.cooldown = 0
        self.ultimo_tiro = 0
        self.nome = ""
        self.descricao = ""

    def encontrar_inimigo_mais_proximo(self, grupo_inimigos, raio_maximo=2000):
        if not grupo_inimigos: return None
        
        inimigo_mais_proximo = None
        menor_distancia = raio_maximo
        
        for inimigo in grupo_inimigos:
            distancia = self.jogador.posicao.distance_to(inimigo.posicao)
            if distancia < menor_distancia:
                menor_distancia = distancia
                inimigo_mais_proximo = inimigo
                
        return inimigo_mais_proximo

    def update(self, delta_time):
        """Lógica de cooldown padronizada"""
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro > self.cooldown:
            # O disparar() agora pode retornar True/False se de fato atirou
            if self.disparar():
                self.ultimo_tiro = agora

    @abstractmethod
    def disparar(self) -> bool:
        """Deve retornar True se o disparo foi realizado com sucesso"""
        pass

    def upgrade(self):
        self.nivel += 1 

    def equipar(self):
        pass 

    @abstractmethod
    def ver_proximo_upgrade(self):
        pass

    @abstractmethod
    def get_estatisticas_para_exibir(self):
        pass


class Projetil(pygame.sprite.Sprite):
    def __init__(self, surface, posicao_inicial, velocidade, direcao, dano, grupo_sprites, jogador, piercing=1):
        super().__init__(grupo_sprites) 
        self.jogador = jogador 
        self.image = surface
        self.rect = self.image.get_rect(center=posicao_inicial)
        
        self.posicao = pygame.math.Vector2(posicao_inicial)
        self.direcao = direcao.normalize() if direcao.length() > 0 else pygame.math.Vector2(0,0)
        self.velocidade = velocidade

        # LOGICA DE PIERCING
        self.dano = dano
        self.piercing = piercing # 1 = morre no primeiro, 2 = atravessa um, etc.
        self.inimigos_atingidos = set() 
        
        self.vida_util = 1500 

    def update(self, delta_time):
        self.posicao += self.direcao * self.velocidade * delta_time
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        # Se o projétil sumir da tela ou distância, kill
        if self.posicao.distance_squared_to(self.jogador.posicao) > self.vida_util ** 2:
            self.kill()