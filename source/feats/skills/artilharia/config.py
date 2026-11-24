# source/feats/skills/artilharia/config.py
from dataclasses import dataclass
from typing import Tuple, Union

from source.systems.empurrao import forca_valida

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
    impacto_com_dot: bool = False   # com dot=True: aplica `dano` na explosão ANTES de iniciar os ticks
    # Empurra quem a explosão atinge (não os ticks) para longe do centro: False = não empurra; um
    # número = quantos px (`systems/empurrao.py`)
    knockback: Union[bool, float] = False

    def __post_init__(self):
        if self.knockback is not False and not forca_valida(self.knockback):
            raise ValueError(f'knockback {self.knockback!r} (precisa ser False ou um número > 0)')

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

    # Fuel Rod: plasma verde; a arma troca dano, dano_por_segundo e duracao_dot pelos stats dela
    'fuel_rod': ArtilhariaConfig(
        dano=25,
        raio_explosao=150,
        duracao=1500,
        cor_borda=(150, 255, 60, 210),
        cor_preenchimento=(70, 235, 50, 70),
        cor_explosao=(190, 255, 90, 230),
        dot=True,
        dano_por_segundo=3,
        duracao_dot=4000,
        impacto_com_dot=True
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
    ),

    # ── Scarab ── (avisos cinza, sujos, com preenchimento vermelho e estouro claro)
    'scarab_passo': ArtilhariaConfig(           # a duração de verdade é a do passo (config do Scarab)
        dano=130,
        raio_explosao=115,
        duracao=700,
        cor_borda=(112, 106, 98, 220),
        cor_preenchimento=(205, 28, 24, 95),
        cor_explosao=(238, 230, 214, 215),
        knockback=110
    ),
    'scarab_sismica': ArtilhariaConfig(         # persegue o jogador
        dano=190,
        raio_explosao=200,
        duracao=1300,
        cor_borda=(98, 90, 82, 240),
        cor_preenchimento=(225, 22, 18, 110),
        cor_explosao=(250, 240, 220, 235),
        knockback=340
    ),
    'scarab_stomp': ArtilhariaConfig(           # a barriga inteira
        dano=240,
        raio_explosao=410,
        duracao=1400,
        cor_borda=(98, 90, 82, 240),
        cor_preenchimento=(205, 24, 20, 90),
        cor_explosao=(250, 240, 220, 225),
        knockback=380
    ),
    'scarab_detonacao': ArtilhariaConfig(       # a explosão final, no fim do colapso
        dano=350,
        raio_explosao=820,
        duracao=2500,
        cor_borda=(90, 255, 120, 220),
        cor_preenchimento=(60, 220, 90, 45),
        cor_explosao=(225, 255, 230, 200),
        knockback=600
    ),

    # ── Guilty Spark ──
    'guilty_sentinela': ArtilhariaConfig(       # cada uma vira uma sentinela
        dano=40,
        raio_explosao=80,
        duracao=1100,
        cor_borda=(255, 225, 140, 210),         # prata e âmbar da sentinela
        cor_preenchimento=(225, 225, 205, 70),
        cor_explosao=(255, 250, 215, 230)
    ),
    'guilty_super_sentinela': ArtilhariaConfig(
        dano=110,
        raio_explosao=160,
        duracao=1400,
        cor_borda=(255, 190, 0, 230),           # dourado
        cor_preenchimento=(255, 170, 20, 80),
        cor_explosao=(255, 225, 110, 245)
    ),
    'guilty_flood': ArtilhariaConfig(
        dano=40,
        raio_explosao=240,
        duracao=1500,
        cor_borda=(95, 85, 35, 230),            # marrom esverdeado
        cor_preenchimento=(84, 82, 34, 110),
        cor_explosao=(120, 115, 50, 230)
    ),
    # Luz visível: 4 no mesmo centro, cada uma maior e mais forte
    'guilty_luz_1': ArtilhariaConfig(
        dano=50, raio_explosao=100, duracao=700,
        cor_borda=(0, 220, 255, 230), cor_preenchimento=(0, 170, 255, 80), cor_explosao=(190, 245, 255, 170)
    ),
    'guilty_luz_2': ArtilhariaConfig(
        dano=80, raio_explosao=170, duracao=650,
        cor_borda=(0, 200, 255, 230), cor_preenchimento=(0, 150, 255, 80), cor_explosao=(180, 240, 255, 150)
    ),
    'guilty_luz_3': ArtilhariaConfig(
        dano=110, raio_explosao=250, duracao=650,
        cor_borda=(0, 180, 255, 235), cor_preenchimento=(0, 130, 255, 85), cor_explosao=(170, 235, 255, 130)
    ),
    'guilty_luz_4': ArtilhariaConfig(
        dano=150, raio_explosao=340, duracao=650,
        cor_borda=(0, 160, 255, 240), cor_preenchimento=(0, 110, 255, 90), cor_explosao=(160, 230, 255, 115)
    ),
}