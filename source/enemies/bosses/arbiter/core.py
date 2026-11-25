import pygame
from source.enemies.base.boss import BossBase
from source.feats.items import Items

from .config import CFG, CLIPS, FASES, HABILIDADES
from .setup import ArbiterSetup
from .states import ESTADOS, ArbiterAI
from .attacks import ArbiterAttacks
from .arsenal import ArbiterArsenal
from .movement import ArbiterMovement


class BossArbiter(ArbiterMovement, ArbiterAI, ArbiterAttacks, ArbiterArsenal, ArbiterSetup, BossBase):
    """Mixins ANTES de BossBase: os overrides deles (`mover`, `perceber`, `_esperar`...) precisam vencer na MRO."""
    FASES = FASES
    COOLDOWNS = CFG.cooldown
    COOLDOWN_INICIAL = CFG.cooldown_inicial
    ESTADOS = ESTADOS
    ANTISTUCK = CFG.antistuck
    CLIPS = CLIPS
    CLIP_INICIAL = 'andar'
    HABILIDADES = HABILIDADES

    def __init__(self, posicao, game, **kwargs):
        super().__init__(posicao, vida_base=2500, dano_base=80, velocidade_base=90, game=game, sprite_key='arbiter', flip_sprite=True)

        self.titulo = "THEL 'VADAM, O Comandante da Frota Covenant"

        # Hitbox Personalizada
        nova_largura = self.rect.width / 3
        nova_altura = self.rect.height / 1.5
        self.hitbox = pygame.Rect(0, 0, nova_largura, nova_altura)
        self.hitbox.center = self.rect.center

        self.inicializar_habilidades()

    def morrer(self, grupos=None):
        Items.spawn_drop(
            self.posicao,
            grupos,
            big_shard=((6, 7, 8, 10), (60, 30, 9, 1), 100),
            life_orb=(1, 100, 100),
            upgrade=((1, 2), (99, 1), 100)
        )
        self.kill()
