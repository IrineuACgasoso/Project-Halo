import pygame
from source.feats.assets import ASSETS

# Seta todo o init do Player
class PlayerSetup:
    def setup_movimento(self):
        self.direcao = pygame.math.Vector2()
        self.velocidade = 500

    def setup_animacao(self, posicao_inicial):
        self.sprites = {}
        # Sprites
        self.sprites['right'] = ASSETS['player']['right']
        self.sprites['left'] = ASSETS['player']['left']

        # Variaveis de animacao
        self.frame_atual = 0  
        self.estado_animacao = 'right'
        self.indice_animacao = 0

        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center = posicao_inicial)
        self.posicao = pygame.math.Vector2(self.rect.center)
        self.velocidade_animacao = 150
        self.ultimo_update_animacao = pygame.time.get_ticks()

    def setup_hitbox(self):
        self.mask = pygame.mask.from_surface(self.image) 
        self.tamanho_hitbox = self.rect.width / 1.5
        self.hitbox = pygame.Rect(0, 0, self.tamanho_hitbox, self.rect.height)
        self.hitbox.center = self.rect.center
    
    def setup_armas(self):
        self.armas = {}

    def setup_shield(self):
        # --- SISTEMA DE ESCUDO ---
        self.escudo_maximo = 0
        self.escudo_atual = 0
        # Regeneração
        self.shield_regen = 0
        self.velocidade_regen_escudo = 0
        # Controle
        self.ultimo_dano_sofrido = 0
        self.regenerando_escudo = False

    def setup_status(self):
        self.vida_maxima = 500
        self.vida_atual = self.vida_maxima
        self.buff_timer = 0
        self.buff_cooldown_ativo = False

    def setup_xp(self):
        self.contador_niveis = 1
        self.experiencia_level_up_base = 100 
        self.experiencia_level_up = self.experiencia_level_up_base 
        self.experiencia_atual = 0
        # Em %
        self.aumento_xp = 1

        self.coletaveis = {
            "exp_shard": 0,
            "life_orb": 0,
            "big_shard": 0,
            "cafe" : 0
        }

    def setup_invencibilidade(self):
        self.invencivel = False
        self.tempo_ultimo_dano = 0
        self.duracao_invencibilidade = 100

    def setup_ranking(self):
        self.pontuacao = 0