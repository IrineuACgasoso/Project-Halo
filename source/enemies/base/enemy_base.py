import pygame
import random
from os.path import join
from source.windows.settings import *
from source.feats.items import *
from source.feats.assets import ASSETS
from source.systems.entitymanager import entity_manager

from .enemy_collision import EnemyCollision
from .enemy_combat import EnemyCombat
from .enemy_movement import EnemyMovement
from .enemy_scaling import EnemyScaling
from .enemy_sprites import EnemySprites
from .enemy_setup import EnemySetup
from .enemy_animation import EnemyAnimation
from .enemy_effects import EnemyEffects



class BaseEnemy(
    pygame.sprite.Sprite,
    EnemySetup,
    EnemySprites,
    EnemyAnimation,
    EnemyMovement,
    EnemyCollision,
    EnemyCombat,
    EnemyScaling,
    EnemyEffects
):
    def __init__(
            self, posicao, vida_base, dano_base, 
            velocidade_base, game, sprite_key, 
            flip_sprite= False, variante = None
            ):
        super().__init__(entity_manager.all_sprites, entity_manager.inimigos_grupo)

        self.setup_core(game, sprite_key, variante)

        self.setup_stats(vida_base, dano_base, velocidade_base)
        self.setup_shield()

        self.setup_collision()
        self.setup_spawn_protection()

        self.setup_invisibility()

        # Gerencia o cache automaticamente para qualquer filho
        if self.sprite_key is not None:
            self._check_and_load_sprites(sprite_key, flip_sprite)

        self.setup_animation()
        
        self.setup_visual(posicao, variante)

        self.aplicar_dificuldade()
    
    @property
    def invisivel(self):
        """Verifica se o inimigo está visualmente indetectável."""
        alpha = getattr(self, 'alpha_atual', 255)
        phase = getattr(self, 'invis_phase', 'none')
        
        return alpha == 0 or phase in ['fade_out', 'hold']

    @property
    def invulneravel(self):
        """
        Dita se o inimigo pode tomar dano ou colisões físicas.
        Se ele tiver uma flag manual ativada OU estiver invisível, ele fica invulnerável.
        """
        flag_manual = getattr(self, 'is_invulneravel', False) 
        protecao_spawn = getattr(self, 'invencivel', False)
        
        return flag_manual or self.invisivel or protecao_spawn

    def update(self, delta_time, paredes=None):
        self.mover(delta_time)

        if paredes:
            self.aplicar_colisao_mapa(paredes)

        self.sync_rect()

