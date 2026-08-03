# source/feats/skills/onda_emp/config.py
from dataclasses import dataclass
from typing import Tuple

@dataclass
class EMPConfig:
    dano: int = 60
    raio_maximo: int = 650
    velocidade_expansao: float = 500.0
    espessura_borda: int = 4
    derrete_escudo: bool = True
    
    # Cores no formato RGBA para efeitos de blend alpha
    cor_externa: Tuple[int, int, int, int] = (255, 150, 120, 40)
    cor_central: Tuple[int, int, int, int] = (255, 100, 100, 200)
    cor_interna: Tuple[int, int, int, int] = (0, 255, 255, 80)

# === PRESETS DA ONDA EMP ===
EMP_PRESETS = {
    'padrao': EMPConfig(),
    
    'didact_shockwave': EMPConfig(
        dano=80,
        raio_maximo=700,
        velocidade_expansao=600.0,
        espessura_borda=6,
        cor_externa=(150, 50, 250, 35),   # Roxo tecnológico
        cor_central=(200, 100, 255, 180), # Núcleo brilhante
        cor_interna=(50, 0, 150, 90)       # Rastro escuro de distorção
    ),
    
    'harbinger_zone': EMPConfig(
        dano=40,
        raio_maximo=1250,
        velocidade_expansao=1000.0,
        espessura_borda=4,
        cor_externa=(255, 255, 130, 40),  
        cor_central=(255, 215, 0, 200), 
        cor_interna=(255, 255, 180, 80)
    ),

    'guardian_emp': EMPConfig(
        dano=40,
        raio_maximo=2557,
        velocidade_expansao=1500.0,
        espessura_borda=6,
        cor_externa=(255, 255, 255, 90),  
        cor_central=(215, 215, 255, 200), 
        cor_interna=(180, 190, 255, 80)
    )
}