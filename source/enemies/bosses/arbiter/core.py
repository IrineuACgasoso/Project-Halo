import pygame
from source.enemies.base.boss import BossBase
from source.feats.items import Items

from .config import CFG, FASES
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

    def __init__(self, posicao, game, **kwargs):
        super().__init__(posicao, vida_base=2500, dano_base=80, velocidade_base=90, game=game, sprite_key='arbiter', flip_sprite=True)

        self.titulo = "THEL 'VADAM, O Comandante da Frota Covenant"

        self.setup_animation(estado_inicial='right', velocidade_animacao=200)

        # Hitbox Personalizada
        nova_largura = self.rect.width / 3
        nova_altura = self.rect.height / 1.5
        self.hitbox = pygame.Rect(0, 0, nova_largura, nova_altura)
        self.hitbox.center = self.rect.center

        self.inicializar_habilidades()

    # ------------------------------------------------------------ combate
    @property
    def revelado(self):
        """Camuflado, mas denunciado por um flash (atirou / golpeou / encostou no jogador)."""
        return self.invis_phase is not None and self.flash_timer > 0

    @property
    def invulneravel(self):
        """Igual a base, exceto que revelar-se ao atacar abre uma janela de dano (counterplay ao stealth)."""
        if getattr(self, 'is_invulneravel', False) or getattr(self, 'invencivel', False):
            return True
        if self.invisivel:
            return not (CFG.vulneravel_ao_revelar and self.revelado)
        return False

    def morrer(self, grupos=None):
        Items.spawn_drop(
            self.posicao,
            grupos,
            big_shard=((6, 7, 8, 10), (60, 30, 9, 1), 100),
            life_orb=(1, 100, 100),
            upgrade=((1, 2), (99, 1), 100)
        )
        self.kill()
