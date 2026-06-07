from dataclasses import dataclass, field
from typing import Any, Optional, Union, List, Dict

@dataclass
class EnemyStats:
    vida: float = 0
    dano: float = 0
    velocidade: float = 0
    velocidade_animacao: float = 0

