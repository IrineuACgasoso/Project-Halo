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
    # Zealot: investidas do combo e do contra-ataque (até onde o jogador estava, no máximo 385 px)...
    'zealot': DashConfig(velocidade=550, duracao_ms=700, ate_o_alvo=True),
    # ... e o bote que sai da invisibilidade (passa reto pelo ponto mirado)
    'zealot_bote': DashConfig(velocidade=700, duracao_ms=800, ate_o_alvo=False),
    # Arbiter: investida da espada (Prophet's Bane), dashes do combo e a esquiva lateral (passa reto)
    'arbiter_investida': DashConfig(velocidade=900, duracao_ms=650, ate_o_alvo=True),
    'arbiter_combo': DashConfig(velocidade=950, duracao_ms=600, ate_o_alvo=True),
    'arbiter_esquiva': DashConfig(velocidade=1100, duracao_ms=260, ate_o_alvo=False),
}
