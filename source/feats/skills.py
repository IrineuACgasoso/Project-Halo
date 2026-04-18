from source.systems.entitymanager import entity_manager
from source.enemies.enemies import *
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
            jogador.tomar_dano_direto(self.dano)
            self.atingiu_jogador = True

        if self.raio_atual >= self.raio_maximo:
            self.kill()


class ArtilhariaAviso(pygame.sprite.Sprite):
    def __init__(self, posicao, grupos, game, atacante,
                 dano = 100,
                 cor_borda=(255, 0, 0, 150),        # Borda vermelha padrão
                 cor_preenchimento=(255, 0, 0, 50), # Preenchimento vermelho padrão
                 cor_explosao=(255, 100, 50, 220),  # Explosão laranja/avermelhada padrão
                 raio_explosao=120):
        
        super().__init__(grupos)
        self.game = game
        self.atacante = atacante
        self.posicao = pygame.math.Vector2(posicao)
        
        self.raio_explosao = 120
        self.duracao_aviso = 1000 
        self.tempo_criacao = pygame.time.get_ticks()
        self.explodiu = False

        # --- Atributos Parametrizados ---
        self.dano = dano
        self.cor_borda = cor_borda
        self.cor_preenchimento = cor_preenchimento
        self.cor_explosao = cor_explosao
        self.raio_explosao = raio_explosao
        
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.posicao)

    def draw(self, surface, offset):
        pos_ajustada = self.posicao - offset
        agora = pygame.time.get_ticks()
        
        temp_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        
        if not self.explodiu:
            progresso = min((agora - self.tempo_criacao) / self.duracao_aviso, 1)
            raio_interno = int(self.raio_explosao * progresso)
            
            # Borda do círculo de aviso (Alpha 150)
            pygame.draw.circle(temp_surface, self.cor_borda, pos_ajustada, self.raio_explosao, 4)
            # Interior preenchendo com transparência alta (Alpha 50)
            if raio_interno > 0:
                pygame.draw.circle(temp_surface, self.cor_preenchimento, pos_ajustada, raio_interno)
        else:
            # Impacto da explosão
            pygame.draw.circle(temp_surface, self.cor_explosao, pos_ajustada, self.raio_explosao)

        surface.blit(temp_surface, (0, 0))

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()
        
        if not self.explodiu and agora - self.tempo_criacao >= self.duracao_aviso:
            self.explodiu = True
            self.tempo_criacao = agora 
            
            jogador = self.atacante.jogador
            if (jogador.posicao - self.posicao).length() <= self.raio_explosao:
                jogador.tomar_dano_direto(self.dano)
                
        elif self.explodiu and agora - self.tempo_criacao >= 150:
            self.kill()