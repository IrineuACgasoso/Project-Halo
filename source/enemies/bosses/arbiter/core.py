import pygame
from source.enemies.base.boss import BossBase
from source.feats.items import Items

from .config import CFG, CLIPS, ESTADOS, FASES, HABILIDADES
from .setup import ArbiterSetup
from .states import ArbiterAI
from .attacks import ArbiterAttacks
from .arsenal import ArbiterArsenal
from .movement import ArbiterMovement
from .vfx import ArbiterVFX


class BossArbiter(ArbiterMovement, ArbiterAI, ArbiterAttacks, ArbiterArsenal, ArbiterVFX, ArbiterSetup, BossBase):
    """Guerreiro completo: escudo regenerativo, carabina e granadas de longe, espada de perto, salto,
    camuflagem curta e um combo quando o escudo quebra. Abaixo de 40%, só espada e granadas.
    Mixins ANTES de BossBase: os overrides deles (`mover`, `perceber`, `_esperar`...) precisam vencer na MRO."""
    FASES = FASES
    COOLDOWNS = CFG.cooldown
    COOLDOWN_INICIAL = CFG.cooldown_inicial
    ESTADOS = ESTADOS
    ANTISTUCK = CFG.antistuck
    CLIPS = CLIPS
    CLIP_INICIAL = 'andar'
    HABILIDADES = HABILIDADES

    def __init__(self, posicao, game, **kwargs):
        super().__init__(posicao, vida_base=CFG.vida, dano_base=CFG.dano_contato, velocidade_base=CFG.velocidade,
                         game=game, sprite_key='arbiter', flip_sprite=True)

        self.titulo = "THEL 'VADAM, O Comandante da Frota Covenant"

        # Hitbox Personalizada
        nova_largura = self.rect.width / 3
        nova_altura = self.rect.height / 1.5
        self.hitbox = pygame.Rect(0, 0, nova_largura, nova_altura)
        self.hitbox.center = self.rect.center

        self.inicializar_habilidades()
        self.iniciar_vfx()

    def morrer(self, grupos=None):
        Items.spawn_drop(
            self.posicao,
            grupos,
            big_shard=((6, 7, 8, 10), (60, 30, 9, 1), 100),
            life_orb=(1, 100, 100),
            upgrade=((1, 2), (99, 1), 100)
        )
        self.kill()
