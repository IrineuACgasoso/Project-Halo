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
    # Arbiter: investida da espada (Prophet's Bane), dashes do combo e a esquiva lateral (passa reto).
    # O combo corre com a Fúria (+45%): 600 vira ~870 px/s; o alcance (vel x duração) ficou o de antes.
    'arbiter_investida': DashConfig(velocidade=720, duracao_ms=800, ate_o_alvo=True),
    'arbiter_combo': DashConfig(velocidade=600, duracao_ms=750, ate_o_alvo=True),
    'arbiter_esquiva': DashConfig(velocidade=900, duracao_ms=320, ate_o_alvo=False),
    # Tartarus: os 3 passos curtos e não muito rápidos do Chieftain Rampage...
    'tartarus_rampage': DashConfig(velocidade=430, duracao_ms=520, ate_o_alvo=True),
    # ... e a Hammer Run da Fúria: longa e "devagar", reta até o fim (sem trava no jogador)
    'tartarus_corrida': DashConfig(velocidade=520, duracao_ms=1700, ate_o_alvo=False),
}
