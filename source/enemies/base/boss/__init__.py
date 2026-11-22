"""Motor comum dos bosses (roteiro F1). Desenho em docs/plano_bosses.md."""
from .boss_base import BossBase
from .contexto import ContextoCombate
from .fases import FASE_UNICA, FaseBoss, fase_pela_vida
from .travamento import ConfigTravamento, DetectorTravamento

__all__ = ['BossBase', 'ContextoCombate', 'FASE_UNICA', 'FaseBoss', 'fase_pela_vida',
           'ConfigTravamento', 'DetectorTravamento']
