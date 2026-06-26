# source/feats/skills/artilharia/config.py
from dataclasses import dataclass
from typing import Tuple

@dataclass
class ArtilhariaConfig:
    dano: int = 100
    raio_explosao: int = 120
    duracao: int = 1000
    cor_borda: Tuple[int, int, int, int] = (255, 0, 0, 150)
    cor_preenchimento: Tuple[int, int, int, int] = (255, 0, 0, 50)
    cor_explosao: Tuple[int, int, int, int] = (255, 100, 50, 220)

# === PRESETS DA ARTILHARIA ===
ARTILHARIA_PRESETS = {
    'padrao': ArtilhariaConfig(),
    
    'hunter_cannon': ArtilhariaConfig(
        dano=250, 
        raio_explosao=270, 
        duracao=600,
        cor_borda=(20, 255, 20, 150), 
        cor_preenchimento=(50, 255, 50, 50), 
        cor_explosao=(100, 255, 100, 220)
    ),
    
    # Exemplo: A explosão rosa rápida da Needler (Supercombine)
    'needler_supercombine': ArtilhariaConfig(
        dano=60, 
        raio_explosao=120, 
        duracao=300,
        cor_borda=(255, 50, 255, 150), 
        cor_preenchimento=(255, 50, 255, 50), 
        cor_explosao=(255, 220, 255, 220)
    ),

    'tartarus_run': ArtilhariaConfig(
        dano=200,
        raio_explosao=300,
        duracao=300, 
        cor_borda=(255, 100, 0, 200),
        cor_preenchimento=(255, 50, 0, 80),
        cor_explosao=(255, 255, 255, 250) # Clarão branco
        ),

    'tartarus_leap': ArtilhariaConfig(
        dano=20,
        raio_explosao=120,
        duracao=100, 
        cor_borda=(255, 100, 0, 200),
        cor_preenchimento=(255, 50, 0, 80),
        cor_explosao=(255, 255, 255, 250) # Clarão branco
        ),

    'flood_warning': ArtilhariaConfig(
        dano=150,
        raio_explosao=300, 
        duracao=2500,
        cor_borda=(255, 0, 0, 200),           # Borda vermelha
        cor_preenchimento=(74, 93, 35, 100),  # Verde musgo
        cor_explosao=(255, 140, 0, 220)       # Laranja (crescimento/impacto)
    ),
    
    'grave_pit': ArtilhariaConfig(
        dano=float('inf'), 
        raio_explosao=400, 
        duracao=2000,
        cor_borda=(255, 0, 0, 200),           # Borda vermelha
        cor_preenchimento=(30, 46, 17, 100),  # Verde escuro musgo
        cor_explosao=(255, 140, 0, 220)       # Laranja (crescimento/impacto)
    ),

    'acid_rain': ArtilhariaConfig(
        dano=250,
        raio_explosao=200, 
        duracao=1000,
        cor_borda=(255, 0, 0, 200),           # Borda vermelha
        cor_preenchimento=(74, 120, 35, 100),  # Verde musgo
        cor_explosao=(255, 140, 0, 220)       # Laranja (crescimento/impacto)
    ),

    'didact_collapse': ArtilhariaConfig(
        dano=200,                             
        raio_explosao=260,                   
        duracao=1200,                         
        cor_borda=(255, 100, 0, 220),         # Laranja Promethean bem definido
        cor_preenchimento=(255, 120, 0, 60),  # Laranja translúcido preenchendo a área
        cor_explosao=(255, 255, 180, 240)     # Explosão em Amarelo Bem Claro / Brilhante
    ),

    'warden_bruiser_leap': ArtilhariaConfig(
        dano=220,
        raio_explosao=300,
        duracao=250,
        cor_borda=(255, 140, 0, 230),
        cor_preenchimento=(255, 100, 0, 55),
        cor_explosao=(255, 230, 120, 255)
    ),
}