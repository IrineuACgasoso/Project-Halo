import pygame

from source.enemies.base.boss import BossBase
from source.feats.items import Items

from .config import CFG, CLIPS, ESTADOS
from .setup import ZealotSetup
from .states import ZealotAI
from .movement import ZealotMovement
from .attacks import ZealotAttacks
from .vfx import ZealotVFX


class Zealot(ZealotMovement, ZealotAI, ZealotAttacks, ZealotVFX, ZealotSetup, BossBase):
    """Vida baixa e escudo avantajado. Com escudo, ataca (combo de 3 dashes, invisibilidade ofensiva);
    sem escudo, foge invisível e o regenera até ser caçado. Mixins ANTES de BossBase (MRO)."""
    COOLDOWNS = CFG.cooldown
    COOLDOWN_INICIAL = CFG.cooldown_inicial
    ESTADOS = ESTADOS
    ANTISTUCK = CFG.antistuck
    CLIPS = CLIPS
    CLIP_INICIAL = 'andar'

    def __init__(self, posicao, game, **kwargs):
        super().__init__(posicao, vida_base=CFG.vida, dano_base=CFG.dano_contato, velocidade_base=CFG.velocidade,
                         game=game, sprite_key='zealot', flip_sprite=True)   # a arte aponta para a esquerda
        self.titulo = "ZEALOT, Soldado de Elite Covenant"

        # Hitbox customizada
        self.hitbox = pygame.Rect(0, 0, self.rect.width / 2, self.rect.height)
        self.hitbox.center = self.rect.center

        self.inicializar_habilidades()
        self.iniciar_vfx()

    def morrer(self, grupos=None):
        Items.spawn_drop(
            self.posicao,
            grupos,
            big_shard=((3, 4), (70, 30), 100),
            life_orb=(1, 100, 100),
            upgrade=((1, 2), (99, 1), 100)
        )
        self.kill()
