"""Presets do ataque retangular (ver `core.py`)."""
import math
from dataclasses import dataclass
from typing import Tuple, Union

from source.feats.skills.artilharia.config import validar_efeitos
from source.systems.empurrao import forca_valida
from source.systems.status import Lentidao

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
    # Quem o golpe atinge é empurrado na direção do golpe (False = não; um número = quantos px)...
    knockback: Union[bool, float] = False
    # ...e leva estes buffs/debuffs do sistema de status (ex.: (Lentidao(0.5, 2000),))
    efeitos: tuple = ()

    def __post_init__(self):
        if self.knockback is not False and not forca_valida(self.knockback):
            raise ValueError(f'RectStrikeConfig: knockback {self.knockback!r} (precisa ser False ou um número > 0)')
        validar_efeitos(self.efeitos, 'RectStrikeConfig')
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

    # Arbiter: o golpe do pouso do salto curto (largo e comprido, cores da espada de energia).
    'arbiter_investida_frontal': RectStrikeConfig(
        dano=150,
        largura=180,
        altura=450,
        duracao=420,
        cor_fundo=(150, 215, 255, 60),
        cor_borda=(10, 60, 150, 230),
        cor_preenchimento=(40, 130, 255, 140),
        cor_explosao=(210, 245, 255, 240)
    ),

    # Combo da quebra de escudo: um corte fino e bem comprido para a frente do dash.
    'arbiter_combo_linha': RectStrikeConfig(
        dano=130,
        largura=60,
        altura=800,
        duracao=450,
        cor_fundo=(150, 215, 255, 60),
        cor_borda=(10, 60, 150, 230),
        cor_preenchimento=(40, 130, 255, 140),
        cor_explosao=(210, 245, 255, 240)
    ),

    # Tartarus: Esmagamento Sísmico. Fissura gravitacional larga e comprida; arremessa e deixa lento.
    'tartarus_onda': RectStrikeConfig(
        dano=170,
        largura=240,
        altura=950,
        duracao=750,
        cor_fundo=(140, 180, 255, 50),
        cor_borda=(40, 70, 200, 220),
        cor_preenchimento=(70, 120, 255, 110),
        cor_explosao=(200, 225, 255, 230),
        knockback=420,
        efeitos=(Lentidao(0.45, 2500),)
    ),
}
