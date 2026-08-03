import pygame
from source.enemies.base.enemy_base import BaseEnemy
from source.feats.items import Items

# Imports locais do pacote
from .setup import GuardianSetup
from .ia import GuardianAI
from .attacks import GuardianAttacks

class Guardian(BaseEnemy, GuardianSetup, GuardianAI, GuardianAttacks):
    def __init__(self, posicao, game, **kwargs):
        super().__init__(posicao, vida_base=1000, dano_base=1, velocidade_base=40, game=game, sprite_key='guardian', flip_sprite=False)
        self.titulo = "GUARDIAN, O Anjo Forerunner"
        self.is_boss = True

        self.setup_animation(
            estado_inicial='left',
            velocidade_animacao=900
        )        
        
        self.mask = pygame.mask.from_surface(self.image)
        self.inicializar_habilidades()

    def animar(self):
        agora = pygame.time.get_ticks()
        
        if agora - getattr(self, 'ultimo_update_animacao', 0) > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            
            self.mask = pygame.mask.from_surface(self.image)
            self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))

    def morrer(self, grupos=None):
        Items.spawn_drop(
            self.posicao, 
            grupos, 
            big_shard=((8, 9, 10, 12), (60, 25, 13, 2), 100), 
            life_orb=(1, 100, 100),              
            upgrade=((1, 2), (99, 1), 100)       
        )
        self.kill()

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()
        dist_sq = self.posicao.distance_squared_to(self.jogador.posicao)

        self.executar_estados(agora, delta_time, dist_sq)

        super().update(delta_time, paredes)

        direcao_x = self.jogador.posicao.x - self.posicao.x 
        self.set_sprite_direction(direcao_x)
            
        self.animar()