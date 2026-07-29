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
    dot: bool = False
    dano_por_segundo: int = 0
    duracao_dot: int = 3000

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

    'spartan_laser': ArtilhariaConfig(
        dano=10,  # o dano já foi aplicado pelo próprio feixe, isso aqui é só o "boom" residual
        raio_explosao=200,
        duracao=250,  # telegraph quase instantâneo, é o rastro da explosão do impacto
        cor_borda=(255, 0, 0, 255),            # vermelho puríssimo, bem vivo
        cor_preenchimento=(255, 60, 60, 40),    # preenchimento bem claro/translúcido
        cor_explosao=(255, 140, 0, 245)         # clarão laranja forte
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

    'jega_spike': ArtilhariaConfig(
        dano=90,
        raio_explosao=120,                    # raio médio
        duracao=850,                          # tempo de telegraph antes de explodir
        cor_borda=(255, 170, 60, 220),        # borda laranja viva
        cor_preenchimento=(255, 140, 0, 140), # laranja translúcido (telegraph)
        cor_explosao=(255, 230, 190, 230)     # explosão clara/quente
    ),

    'plasma_grenade': ArtilhariaConfig(
        dano=50,
        raio_explosao=150,
        duracao=1500,  # tempo grudado antes de estourar (fidedigno ao Halo)
        cor_borda=(120, 150, 255, 200),
        cor_preenchimento=(200, 200, 255, 60),
        cor_explosao=(240, 255, 240, 240)
    ),

    'jega_decoy_explosion': ArtilhariaConfig(
        dano=100,
        raio_explosao=250,                    # raio pequeno/médio, é uma nuvem localizada
        duracao=400,                          # quase sem telegraph: o "estouro" é quase instantâneo
        cor_borda=(255, 60, 60, 200),        # roxo-plasma
        cor_preenchimento=(255, 69, 0, 90), # nuvem roxa translúcida
        cor_explosao=(230, 200, 200, 220),    # vermelho
        dot=True,
        dano_por_segundo=50,
        duracao_dot=5000
    ),
    
    'harbinger_energy_blast': ArtilhariaConfig(
        dano=140,
        raio_explosao=180,
        duracao=300,
        cor_borda=(30, 100, 255, 200),
        cor_preenchimento=(30, 120, 255, 70),
        cor_explosao=(150, 200, 255, 240)
    )
}