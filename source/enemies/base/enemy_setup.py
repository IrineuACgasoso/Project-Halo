import pygame
from source.systems.entitymanager import entity_manager

class EnemySetup:
    def setup_core(self, game, sprite_key, variante):
        self.game = game
        self.sprite_key = sprite_key
        self.variante = variante
        self.jogador = self.game.player
        self.nome_completo = "INIMIGO"
        self.is_boss = False

    def setup_stats(self, vida_base, dano_base, velocidade_base):
        # Base
        self.vida_base = vida_base
        self.dano_base = dano_base
        self.velocidade_base = velocidade_base

        # Stats atuais
        self.vida_maxima = vida_base
        self.vida = self.vida_base
        self.dano = self.dano_base
        self.velocidade = self.velocidade_base
    
    def setup_shield(self):
        self.escudo_maximo = 0
        self.escudo_atual = 0

    def setup_sprite_placeholder(self, posicao):
        self.image = pygame.Surface((40, 40))
        self.image.fill('white')
        self.rect = self.image.get_rect(center=posicao)
        self.posicao = pygame.math.Vector2(self.rect.center)

    def setup_collision(self):
        self.raio_colisao_mapa = 15
        self.iteracoes_colisao_mapa = 2

    def setup_spawn_protection(self):
        self.invencivel = False
        self.tempo_criacao = pygame.time.get_ticks()
        self.tempo_invencibilidade = 0
    
    def setup_invisibility(self):
        # Invisibilidade
        self.invis_phase = None

        self.invis_alpha_base = 255
        self.invis_alpha_target = 255

        self.invis_fade_out = 0
        self.invis_fade_in = 0
        self.invis_duracao = 0

        self.invis_timer = 0
        self.invis_phase_timer = 0
        # Flash
        self.flash = False
        self.flash_timer = 0
        # Alpha
        self.alpha_atual = 255
    