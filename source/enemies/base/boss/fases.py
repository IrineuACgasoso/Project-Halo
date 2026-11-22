"""Fases de um boss: dados validados + a regra de subida (só pela vida, nunca volta)."""
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class FaseBoss:
    """Campos que o motor lê. O boss estende com os dele (ex.: `FaseArbiter`), na mesma ordem."""
    nome: str
    limiar_vida: float          # a fase vale quando vida / vida_maxima <= limiar
    mult_cooldown: float        # < 1 = habilidades voltam mais rápido
    mult_velocidade: float

    def __post_init__(self):
        if not isinstance(self.nome, str) or not self.nome:
            raise ValueError(f'fase sem nome: {self.nome!r}')
        if not (isinstance(self.limiar_vida, (int, float)) and 0 < self.limiar_vida <= 1):
            raise ValueError(f'fase "{self.nome}": limiar_vida {self.limiar_vida!r} (precisa estar em (0, 1])')
        for campo in ('mult_cooldown', 'mult_velocidade'):
            valor = getattr(self, campo)
            if not (isinstance(valor, (int, float)) and math.isfinite(valor) and valor > 0):
                raise ValueError(f'fase "{self.nome}": {campo} {valor!r} (precisa ser > 0 e finito)')


FASE_UNICA = FaseBoss('Única', 1.0, 1.0, 1.0)


def fase_pela_vida(fases, razao_vida, fase_atual):
    """Número (1-based) da fase mais avançada cujo limiar a vida já cruzou. Nunca volta, e pode
    pular fases (um golpe grande leva da 1 direto para a 3)."""
    nova = fase_atual
    for numero, fase in enumerate(fases, start=1):
        if numero > nova and razao_vida <= fase.limiar_vida:
            nova = numero
    return nova
