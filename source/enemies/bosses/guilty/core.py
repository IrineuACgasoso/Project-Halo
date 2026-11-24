from source.enemies.base.boss import BossBase
from source.feats.items import Items

from .attacks import GuiltyAttacks
from .barreira import GuiltyBarreira
from .config import CFG, CLIPS, ESTADOS, FASES
from .invocacoes import GuiltyInvocacoes
from .movement import GuiltyMovement
from .setup import GuiltySetup
from .states import GuiltyAI
from .vfx import GuiltyVFX


class GuiltySpark(GuiltyMovement, GuiltyAI, GuiltyBarreira, GuiltyAttacks, GuiltyInvocacoes, GuiltyVFX,
                  GuiltySetup, BossBase):
    """Invocador atrás de uma barreira. Mixins ANTES de BossBase (MRO).

    - Fase 1: ronda e chuva de sentinelas; derrotar 40 derruba a barreira e religa o spawner.
    - Fase 2 (80% da vida): barreira de novo; só a luz visível dele mesmo o fere (5% por acerto).
    - Fase 3 (30%): sem barreira; teleporte + laser até morrer."""
    FASES = FASES
    COOLDOWNS = CFG.cooldown
    COOLDOWN_INICIAL = CFG.cooldown_inicial
    ESTADOS = ESTADOS
    ANTISTUCK = CFG.antistuck
    CLIPS = CLIPS
    CLIP_INICIAL = 'azul'

    def __init__(self, posicao, game, grupos=None):
        super().__init__(posicao, vida_base=CFG.vida, dano_base=CFG.dano_contato, velocidade_base=CFG.velocidade,
                         game=game, sprite_key='guilty', flip_sprite=True)   # a arte olha para a esquerda
        self.titulo = "343 GUILTY SPARK, Monitor da Instalação 04"
        self.inicializar_habilidades()
        self.iniciar_vfx()
        self.erguer_barreira(efeito=False)

    def morrer(self, grupos=None):
        Items.spawn_drop(
            self.posicao,
            grupos,
            big_shard=((4, 5, 6, 8), (50, 35, 14, 1), 100),
            life_orb=(1, 100, 100),
            upgrade=((1, 2, 3, 4), (99, 0.9, 0.09, 0.01), 100)
        )
        self.kill()
