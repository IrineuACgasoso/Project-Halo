"""Motor comum dos bosses (roteiro F1: ciclo e fases; F2: animação). Desenho em docs/plano_bosses.md."""
from .animador import Animador, Clip
from .boss_base import BossBase
from .contexto import ContextoCombate
from .fases import FASE_UNICA, FaseBoss, fase_pela_vida
from .travamento import ConfigTravamento, DetectorTravamento

__all__ = ['Animador', 'Clip', 'BossBase', 'ContextoCombate', 'FASE_UNICA', 'FaseBoss', 'fase_pela_vida',
           'ConfigTravamento', 'DetectorTravamento']
