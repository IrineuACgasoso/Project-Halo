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
        """Camuflado (fade out ou oculto) ou fora do mundo: ninguém pode MIRAR nele (`alvejavel`).
        Continua podendo ser atingido (tiro perdido, aura, explosão): ver `invulneravel`."""
        return (self.alpha_atual == 0 or self.em_teleporte
                or (self.invisibilidade is not None and self.invisibilidade.oculta))

    @property
    def vivo(self):
        """Ainda tem vida. Sair do mundo é `alive()`: a consciência do Warden adia a morte."""
        return self.vida > 0

    @property
    def alvejavel(self):
        """Pode ser escolhido como alvo (armas, companheiros, veículos, projéteis teleguiados):
        vivo e visível. Toda busca de alvo nova passa por aqui."""
        return self.vivo and not self.invisivel

    @property
    def invulneravel(self):
        """
        Dita se o inimigo pode tomar dano ou colisões físicas.
        Vale com uma flag manual ativada, no meio de um teleporte ou na proteção de spawn.
        Invisível NÃO é invulnerável: só não pode ser mirado.
        """
        flag_manual = getattr(self, 'is_invulneravel', False)
        protecao_spawn = getattr(self, 'invencivel', False)

        return flag_manual or self.em_teleporte or protecao_spawn
    
    @property
    def inofensivo(self):
        """
        Dita se o inimigo perde temporariamente a capacidade de causar dano de contato.
        Ideal para quando estão no ar (eixo Z falso), atordoados (inclusive pelo sistema de status), etc.
        """
        return getattr(self, 'is_inofensivo', False) or self.status.atordoado

    @property
    def quadro_original(self):
        """Quadro mostrado, como está no cache (sem o alpha desta instância): a silhueta da distorção."""
        return self.sprites[self.estado_animacao][self.frame_atual]

    def update(self, delta_time, paredes=None):
        self.mover(delta_time)

        if paredes:
            self.aplicar_colisao_mapa(paredes)

        self.sync_rect()

