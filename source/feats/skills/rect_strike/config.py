"""Presets do ataque retangular (ver `core.py`)."""
import math
from dataclasses import dataclass
from typing import Tuple

Cor = Tuple[int, int, int, int]


@dataclass(frozen=True)
class RectStrikeConfig:
    dano: float = 120
    largura: float = 80             # espessura: de um lado ao outro da direção (px)
    altura: float = 400             # alcance: do dono até a ponta, na direção (px)
    duracao: float = 900            # aviso (ms de jogo)
    cor_fundo: Cor = (255, 170, 120, 55)            # o retângulo inteiro, claro
    cor_borda: Cor = (120, 30, 0, 220)              # contorno escuro
    cor_preenchimento: Cor = (190, 60, 0, 130)      # avança do dono até a ponta
    cor_explosao: Cor = (255, 200, 120, 230)        # clarão do golpe

    def __post_init__(self):
        for campo in ('largura', 'altura', 'duracao'):
            valor = getattr(self, campo)
            if not (math.isfinite(valor) and valor > 0):
                raise ValueError(f'RectStrikeConfig: {campo} precisa ser > 0 (veio {valor!r})')
        if not self.dano >= 0:          # NaN também falha
            raise ValueError(f'RectStrikeConfig: dano precisa ser >= 0 (veio {self.dano!r})')


RECT_STRIKE_PRESETS = {
    'padrao': RectStrikeConfig(),

    # Estocada da espada de energia do Zealot: fina, curtíssima e de altíssimo dano (esquiva lateral).
    'zealot_estocada': RectStrikeConfig(
        dano=220,
        largura=70,
        altura=460,
        duracao=350,
        cor_fundo=(150, 215, 255, 70),
        cor_borda=(10, 50, 130, 230),
        cor_preenchimento=(30, 110, 230, 150),
        cor_explosao=(210, 245, 255, 240)
    ),
}
