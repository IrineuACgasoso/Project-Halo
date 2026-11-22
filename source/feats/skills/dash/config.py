"""Presets do dash: investida em linha reta de qualquer inimigo (ver `core.py`)."""
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class DashConfig:
    velocidade: float           # px/s
    duracao_ms: float           # tempo máximo de corrida (ms de jogo)
    ate_o_alvo: bool = False    # True: para no ponto travado (ou no fim do tempo, o que vier antes)
                                # False: corre na direção travada até o fim do tempo

    def __post_init__(self):
        for campo in ('velocidade', 'duracao_ms'):
            valor = getattr(self, campo)
            if not (math.isfinite(valor) and valor > 0):
                raise ValueError(f'DashConfig: {campo} precisa ser > 0 (veio {valor!r})')


DASH_PRESETS = {
    'padrao': DashConfig(velocidade=600, duracao_ms=800, ate_o_alvo=True),
    # Run do Hunter: a velocidade da corrida antiga (500), um pouco mais curta (era 2500 ms)
    'hunter': DashConfig(velocidade=500, duracao_ms=2000, ate_o_alvo=False),
}
