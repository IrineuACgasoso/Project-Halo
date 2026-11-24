"""Presets da invisibilidade (ver `core.py`). Tempos em ms de jogo."""
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class InvisibilidadeConfig:
    fade_out_ms: float          # sumindo (já não pode ser mirado)
    duracao_ms: float | None    # totalmente invisível, SEM contar os fades; None = até `encerrar()`
    fade_in_ms: float           # reaparecendo (já pode ser mirado)

    def __post_init__(self):
        for campo in ('fade_out_ms', 'fade_in_ms'):
            valor = getattr(self, campo)
            if not (math.isfinite(valor) and valor > 0):
                raise ValueError(f'InvisibilidadeConfig: {campo} precisa ser > 0 (veio {valor!r})')
        if self.duracao_ms is not None and not (math.isfinite(self.duracao_ms) and self.duracao_ms >= 0):
            raise ValueError(f'InvisibilidadeConfig: duracao_ms precisa ser >= 0 ou None (veio {self.duracao_ms!r})')


INVISIBILIDADE_PRESETS = {
    'padrao': InvisibilidadeConfig(fade_out_ms=500, duracao_ms=3000, fade_in_ms=500),
    'elite': InvisibilidadeConfig(fade_out_ms=800, duracao_ms=6400, fade_in_ms=800),
    'arbiter_furtivo': InvisibilidadeConfig(fade_out_ms=1000, duracao_ms=1900, fade_in_ms=600),
    'arbiter_antistuck': InvisibilidadeConfig(fade_out_ms=800, duracao_ms=1100, fade_in_ms=600),
    # Os fades da órbita (3000 ms) e da ilusão (2200 ms) do Jega cabem dentro do estado dele
    'jega_orbita': InvisibilidadeConfig(fade_out_ms=400, duracao_ms=2200, fade_in_ms=400),
    'jega_ilusao': InvisibilidadeConfig(fade_out_ms=350, duracao_ms=1500, fade_in_ms=350),
    'harbinger_teleporte': InvisibilidadeConfig(fade_out_ms=60, duracao_ms=240, fade_in_ms=100),
    'zealot_furtivo': InvisibilidadeConfig(fade_out_ms=500, duracao_ms=4500, fade_in_ms=250),
    # Sem fim: a fuga dele decide quando reaparecer (escudo cheio ou jogador perto)
    'zealot_defensiva': InvisibilidadeConfig(fade_out_ms=350, duracao_ms=None, fade_in_ms=300),
    'zealot_reposicao': InvisibilidadeConfig(fade_out_ms=500, duracao_ms=500, fade_in_ms=500),
}
