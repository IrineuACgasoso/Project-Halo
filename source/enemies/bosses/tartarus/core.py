import pygame

from source.enemies.base.boss import BossBase
from source.feats.items import Items

from .attacks import TartarusAttacks
from .config import CFG, CLIPS, ESTADOS, FASES, HABILIDADES
from .halo import ProtocoloHalo
from .movement import TartarusMovement
from .setup import TartarusSetup
from .states import TartarusAI
from .vfx import TartarusVFX


class Tartarus(TartarusMovement, TartarusAI, TartarusAttacks, TartarusVFX, TartarusSetup, BossBase):
    """Chefe dos Brutes: força bruta e caos gravitacional. Avança sempre, nunca recua; a Barreira do Punho
    de Rukt corta 90% do dano até ele errar golpes pesados (sobrecarga) ou a barra de esquivas encher.
    A luta tem hora para acabar (Ativação do Halo). Abaixo de 35%, Fúria Jiralhanae.
    Mixins ANTES de BossBase: os overrides deles (`orientar`, `pensar`, `iniciar`...) precisam vencer na MRO."""
    FASES = FASES
    COOLDOWNS = CFG.cooldown
    COOLDOWN_INICIAL = CFG.cooldown_inicial
    ESTADOS = ESTADOS
    ANTISTUCK = CFG.antistuck
    CLIPS = CLIPS
    CLIP_INICIAL = 'andar'
    HABILIDADES = HABILIDADES

    def __init__(self, posicao, game, ativar_halo=True, **kwargs):
        super().__init__(posicao, vida_base=CFG.vida, dano_base=CFG.dano_contato, velocidade_base=CFG.velocidade,
                         game=game, sprite_key='tartarus')
        self.titulo = "TARTARUS, O Punho de Rukt"

        largura, altura = CFG.hitbox_fracao
        self.hitbox = pygame.Rect(0, 0, self.rect.width * largura, self.rect.height * altura)
        self.hitbox.center = self.rect.center

        self.inicializar_habilidades()
        self.iniciar_vfx()
        self.halo = ProtocoloHalo(game=self.game, boss=self, tempo_limite_ms=CFG.halo_ms) if ativar_halo else None

    def morrer(self, grupos=None):
        Items.spawn_drop(
            self.posicao,
            grupos,
            big_shard=((6, 8, 10), (70, 28, 2), 100),
            life_orb=(1, 100, 100),
            upgrade=((1, 2), (99, 1), 100)
        )
        self.kill()
