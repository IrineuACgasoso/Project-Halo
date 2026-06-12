from source.systems.entitymanager import entity_manager
from source.enemies.base.enemy_base import *
from source.feats.items import *
from source.player.weapons import *
from source.feats.assets import *
import math


class OndaEMP(pygame.sprite.Sprite):
    def __init__(self, posicao, grupos, game, atacante,
                 cor_externa=(255, 150, 120, 40), 
                 cor_central=(255, 100, 100, 200), 
                 cor_interna=(0, 255, 255, 80)):
        
        super().__init__(grupos)
        self.game = game
        self.atacante = atacante
        self.posicao = pygame.math.Vector2(posicao)

        # --- Atributos de Cor ---
        self.cor_externa = cor_externa
        self.cor_central = cor_central
        self.cor_interna = cor_interna
        
        self.raio_atual = 10
        self.raio_maximo = 650
        self.velocidade_expansao = 500
        self.dano = 60
        self.atingiu_jogador = False
        
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.posicao)

    def draw(self, surface, offset):
        pos_ajustada = self.posicao - offset
        
        # Surface temporária para transparência
        temp_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        
        # Efeito de onda com múltiplas camadas sobrepostas para dar volume
        # Camada externa
        pygame.draw.circle(temp_surface, self.cor_externa, pos_ajustada, int(self.raio_atual + 15), 20)
        # Camada central 
        pygame.draw.circle(temp_surface, self.cor_central, pos_ajustada, int(self.raio_atual), 4)
        # Camada interna (rastro de energia arrastando atrás)
        if self.raio_atual > 20:
            pygame.draw.circle(temp_surface, self.cor_interna, pos_ajustada, int(self.raio_atual - 10), 15)
            
        surface.blit(temp_surface, (0, 0))

    def update(self, delta_time, paredes=None):
        self.raio_atual += self.velocidade_expansao * delta_time
        
        jogador = self.atacante.jogador
        distancia = (jogador.posicao - self.posicao).length()
        
        if not self.atingiu_jogador and abs(distancia - self.raio_atual) < 20: # Aumentei um pouco a tolerância da colisão da onda
            if hasattr(jogador, 'escudo_atual') and jogador.escudo_atual > 0:
                jogador.escudo_atual = 0  # Derrete o escudo instantaneamente
                
                # Opcional: Você pode colocar um som de "Shield Break" aqui!
                # if hasattr(self.game, 'sounds'): self.game.sounds['shield_break'].play()
                
            else:
                # Se não tem escudo, a onda frita a vida do jogador
                jogador.tomar_dano_direto(self.dano)

        if self.raio_atual >= self.raio_maximo:
            self.kill()
