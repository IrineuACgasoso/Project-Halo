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
    ),

    'warden_chop': ConeStrikeConfig(
        dano=300,                   # Dano massivo
        raio=600,                   # Alcance longo da espada gigantesca dele
        angulo_spray=45,            # Mais fechado que o cleave, focando a energia num ponto mais denso
        duracao=500,                # Telegraph rápido e perigoso
        cor_borda=(255, 80, 0, 220),       # Laranja/Vermelho Promethean vibrante
        cor_preenchimento=(200, 50, 0, 90),# Preenchimento denso e quente
        cor_explosao=(255, 230, 150, 250)  # Clarão branco/dourado no impacto
    ),

    # Shield slam do Hunter: colado nele, 90° à frente, carga mais lenta para dar para desviar.
    'hunter_shield_slam': ConeStrikeConfig(
        dano=150,
        raio=300,
        angulo_spray=90,
        duracao=1000,
        cor_borda=(120, 255, 90, 210),
        cor_preenchimento=(60, 170, 40, 80),
        cor_explosao=(200, 255, 170, 240)
    ),

    # === ARBITER (Covenant) — energia azul ===
    # Espada de energia: curtissimo alcance, arco aberto, telegraph rapido.
    'arbiter_energy_sword': ConeStrikeConfig(
        dano=120,
        raio=230,
        angulo_spray=100,
        duracao=450,
        cor_borda=(90, 190, 255, 225),
        cor_preenchimento=(40, 120, 255, 90),
        cor_explosao=(190, 240, 255, 245)
    ),

    # Onda de choque 360 usada na transicao de fase (punir quem fica colado nele).
    'arbiter_nova': ConeStrikeConfig(
        dano=80,
        raio=260,
        angulo_spray=360,
        duracao=900,
        cor_borda=(70, 170, 255, 210),
        cor_preenchimento=(30, 100, 255, 70),
        cor_explosao=(170, 225, 255, 240)
    ),
}
