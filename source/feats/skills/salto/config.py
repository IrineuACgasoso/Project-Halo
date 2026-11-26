"""Presets do salto: pulo em arco de qualquer inimigo (ver `core.py`)."""
import math
from dataclasses import dataclass
from typing import Tuple

ALVOS = ('jogador', 'ponto', 'aleatorio')


@dataclass(frozen=True)
class SaltoConfig:
    duracao_ms: float               # tempo no ar (ms de jogo)
    altura: float                   # px do pico do arco (só o desenho sobe)
    alvo: str = 'jogador'           # 'jogador': onde ele está no início | 'ponto': o `alvo` passado |
                                    # 'aleatorio': direção sorteada, a uma distância de `distancia`
    distancia: Tuple[float, float] = (0, math.inf)   # comprimento do salto: o destino é puxado para esta faixa
    recuo: float = 0                # pousa tanto antes do alvo, na linha do salto (0 = em cima dele)
    invulneravel: bool = True       # no ar também não é atingido (o Tartarus); False = só não é mirado
    tentativas: int = 12            # 'aleatorio': sorteios até achar chão válido

    def __post_init__(self):
        if self.alvo not in ALVOS:
            raise ValueError(f'SaltoConfig: alvo {self.alvo!r} (conhecidos: {ALVOS})')
        for campo in ('duracao_ms', 'altura'):
            valor = getattr(self, campo)
            if not (math.isfinite(valor) and valor > 0):
                raise ValueError(f'SaltoConfig: {campo} precisa ser > 0 (veio {valor!r})')
        minimo, maximo = self.distancia
        if not 0 <= minimo <= maximo or self.recuo < 0:
            raise ValueError(f'SaltoConfig: distancia {self.distancia!r} / recuo {self.recuo!r} inválidos')
        if self.alvo == 'aleatorio' and math.isinf(maximo):
            raise ValueError("SaltoConfig: alvo 'aleatorio' precisa de uma distancia máxima finita")


SALTO_PRESETS = {
    # O salto do Tartarus: no jogador, alto e longo
    'padrao': SaltoConfig(duracao_ms=1200, altura=300),
    # Arbiter: salto curto e baixo que pousa antes do jogador e golpeia à frente
    'arbiter_investida': SaltoConfig(duracao_ms=520, altura=90, distancia=(120, 460), recuo=170),
    # Arbiter preso: mais alto, por cima da parede, e pousa exatamente onde o jogador está
    'arbiter_antistuck': SaltoConfig(duracao_ms=750, altura=150),
    # Tartarus reformulado: o meteoro pousa onde o jogador VAI estar (o ponto é dado pela rotina)...
    'tartarus_meteoro': SaltoConfig(duracao_ms=1100, altura=320, alvo='ponto'),
    # ... o Punho de Rukt vai ao meio da arena...
    'tartarus_punho': SaltoConfig(duracao_ms=1000, altura=380, alvo='ponto'),
    # ... e o anti-stuck pula em cima do jogador
    'tartarus_antistuck': SaltoConfig(duracao_ms=900, altura=260),
}
