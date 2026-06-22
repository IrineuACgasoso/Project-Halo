# source/feats/skills/cone_strike/config.py
from dataclasses import dataclass
from typing import Tuple

@dataclass
class ConeStrikeConfig:
    dano: int = 120
    raio: int = 200
    angulo_spray: int = 60          # Abertura total do cone em graus
    duracao: int = 1200             # Tempo de carregamento em milissegundos
    cor_borda: Tuple[int, int, int, int] = (255, 60, 0, 180)
    cor_preenchimento: Tuple[int, int, int, int] = (255, 100, 0, 60)
    cor_explosao: Tuple[int, int, int, int] = (255, 200, 50, 230)

# === PRESETS DO CONE STRIKE ===
CONE_STRIKE_PRESETS = {
    'padrao': ConeStrikeConfig(),
    
    'cleave_knight': ConeStrikeConfig(
        dano=180,
        raio=400,
        angulo_spray=90,            # Arco bem aberto de espada
        duracao=750,
        cor_borda=(255, 50, 50, 200),
        cor_preenchimento=(150, 80, 85, 70),
        cor_explosao=(255, 255, 255, 240)
    ),
    
    'promethean_incinerator': ConeStrikeConfig(
        dano=300,
        raio=320,
        angulo_spray=45,            # Sopro de chamas concentrado e longo
        duracao=1500,
        cor_borda=(255, 0, 0, 200),
        cor_preenchimento=(255, 60, 0, 80),
        cor_explosao=(255, 150, 0, 250)
    )
}