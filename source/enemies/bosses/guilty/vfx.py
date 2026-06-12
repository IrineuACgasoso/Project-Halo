import pygame
from source.feats.assets import ASSETS
from source.systems.entitymanager import entity_manager

class GuiltyTeleport(pygame.sprite.Sprite):
    def __init__(self, posicao):
        super().__init__(entity_manager.all_sprites)
        self.posicao = pygame.math.Vector2(posicao) 
        self.sprites = ASSETS['enemies']['guilty']['teleport']

        self.frame_atual = 0
        self.image = self.sprites[self.frame_atual]
        self.rect = self.image.get_rect(center=self.posicao)
        
        self.tempo_criacao = pygame.time.get_ticks()
        self.ultimo_update_animacao = pygame.time.get_ticks()
        self.velocidade_animacao = 30
        self.duracao_aviso = 330
    
    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        if agora - self.tempo_criacao >= self.duracao_aviso:
            self.kill()
        self.animar()

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites)
            self.image = self.sprites[self.frame_atual]
            self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))


import pygame
from source.systems.entitymanager import entity_manager

class EnergyAura(pygame.sprite.Sprite):
    def __init__(self, owner, raio, dano_contato, game, cor_base=(0, 150, 255), impenetravel=True):
        super().__init__(entity_manager.all_sprites)
        self.owner = owner
        self.game = game
        self.raio = raio
        self.cor_base = cor_base
        self.impenetravel = impenetravel
        
        self.dano_contato = dano_contato
        self.cooldown_dano = 400 
        self.ultimo_dano = 0
        
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.owner.posicao)
        self.desenhar_aura()

    def desenhar_aura(self):
        """Gera o visual dinâmico com base na cor fornecida"""
        self.image.fill((0, 0, 0, 0))
        r, g, b = self.cor_base
        
        for raio_atual in range(self.raio - 20, self.raio + 10, 4):
            alpha = max(0, 60 - abs(self.raio - raio_atual) * 3)
            pygame.draw.circle(self.image, (r, g, b, alpha), (self.raio, self.raio), raio_atual, 3)
            
        # Brilho central (clareia um pouco a cor base)
        r_claro = min(r + 50, 255)
        g_claro = min(g + 50, 255)
        b_claro = min(b + 50, 255)
        pygame.draw.circle(self.image, (r_claro, g_claro, b_claro, 180), (self.raio, self.raio), self.raio, 2)

    def update(self, delta_time):
        # Se o dono morrer, a aura se desfaz
        if not self.owner.alive():
            self.kill()
            return
            
        # Regra específica do Guilty Spark (se for ele e sair da transição, desliga)
        if hasattr(self.owner, 'estado_fase') and self.owner.estado_fase != 'TRANSICAO':
            self.kill()
            return
        
        self.rect.center = (round(self.owner.posicao.x), round(self.owner.posicao.y))
        
        # === LÓGICA DE DANO E COLISÃO ===
        player = self.game.player
        vetor_distancia = player.posicao - self.owner.posicao
        distancia_atual = vetor_distancia.length()
        raio_colisao = self.raio + 15
        
        if distancia_atual < raio_colisao:
            # SÓ APLICA O EMPURRÃO SE FOR IMPENETRÁVEL
            if self.impenetravel:
                if distancia_atual > 0:
                    direcao_empurrao = vetor_distancia.normalize()
                else:
                    direcao_empurrao = pygame.math.Vector2(1, 0)
                    
                player.posicao = self.owner.posicao + direcao_empurrao * raio_colisao
                player.rect.center = (round(player.posicao.x), round(player.posicao.y))
                
            # O TICK DE DANO ACONTECE DE QUALQUER FORMA
            agora = pygame.time.get_ticks()
            if agora - self.ultimo_dano >= self.cooldown_dano:
                self.ultimo_dano = agora
                if hasattr(player, 'receber_dano'):
                    player.receber_dano(self.dano_contato)
                elif hasattr(player, 'tomar_dano'):
                    player.tomar_dano(self)
                else:
                    player.vida_atual -= self.dano_contato