from dataclasses import dataclass, field
from typing import Any, Optional, Union, List, Dict

@dataclass
class WeaponStats:
    value: Any                      # O valor inicial/atual (int, float, bool, etc.)
    label: Optional[str] = None     # Nome exibido na interface de upgrades 
    increase: float = 0             # Quanto aumenta por nível
    range_val: Any = 0              # Multiplicador ou lista de limites [3, 5, 7]
    min_val: Optional[float] = None # Valor mínimo limite (útil para cooldowns)
    
    # ── FALLBACK INTELIGENTE COM TRADUÇÃO DE CHAVES ──
    def __getitem__(self, key):
        # Se o código antigo pedir 'range', entrega o 'range_val'
        if key == 'range':
            key = 'range_val'
        # Se o código antigo pedir 'min', entrega o 'min_val'
        elif key == 'min':
            key = 'min_val'
            
        return getattr(self, key)

    

@dataclass
class CompanionProfile:
    tipo: str
    stats: Dict[str, WeaponStats]
    def __getitem__(self, key):
        return getattr(self, key)

@dataclass
class WeaponProfile:
    stats: Dict[str, WeaponStats]
    # FALLBACK PARA CASOS DE USO DE COLCHETES
    def __getitem__(self, key):
        return getattr(self, key)

#======== WEAPON =========================

WEAPON_DATA: Dict[str, WeaponProfile] = {
    'rifle_assalto': WeaponProfile(
        stats={
            'dano':                  WeaponStats(value=1,    label='Dano',          increase=1,   range_val=2),
            'cooldown':              WeaponStats(value=500,  label='Cadência (ms)', increase=-20, range_val=2, min_val=300),
            'projeteis_por_disparo': WeaponStats(value=1,    label='Projéteis',     increase=1,   range_val=[3, 5, 7, 9]),
            'velocidade_projetil':   WeaponStats(value=2000, label=None,            increase=0,   range_val=0),
        }
    ),

    'brick': WeaponProfile(
        stats={
            'dano':       WeaponStats(value=1,    label='Dano',       increase=1,     range_val=1),
            'rebatidas':  WeaponStats(value=3,    label='Rebotes',    increase=1,     range_val=1),
            'velocidade': WeaponStats(value=1000, label='Velocidade', increase=100,   range_val=1),
            'cooldown':   WeaponStats(value=2000, label='Cooldown',   increase=-100,  range_val=1),
        }
    ),

    'energy_sword': WeaponProfile(
        stats={
            'dano':               WeaponStats(value=5,    label='Dano',              increase=3,   range_val=1),
            'velocidade_rotacao': WeaponStats(value=120,  label='Velocidade Angular',increase=10,  range_val=1),
            'distancia_orbita':   WeaponStats(value=140,  label='Raio da Órbita',    increase=10,  range_val=1),
            'num_listas':         WeaponStats(value=1,    label='Num. Listas',       increase=1,   range_val=2),
            'duracao':            WeaponStats(value=5000, label=None,                increase=0,   range_val=0),
            'cooldown':           WeaponStats(value=3000, label='Cooldown',          increase=-50, range_val=1, min_val=0),
        }
    ),

    'mk2_shield': WeaponProfile(
        stats={
            'dano_por_segundo':        WeaponStats(value=1,           label='Dano/s',       increase=1,   range_val=1),
            'raio':                    WeaponStats(value=120,         label='Raio',         increase=30,  range_val=1),
            'cooldown':                WeaponStats(value=float('inf'),label=None,           increase=0,   range_val=0),
            'escudo':                  WeaponStats(value=100,          label='Escudo',       increase=50,  range_val=1),
            'shield_regen':            WeaponStats(value=5000,        label='Delay Regen',  increase=-250, range_val=1, min_val=2500),
            'velocidade_regen_escudo': WeaponStats(value=40,          label='Shield Regen', increase=20,   range_val=1),
        }
    ),

    'needler': WeaponProfile(
        stats={
            'dano':           WeaponStats(value=1,    label='Dano',     increase=1,     range_val=1),
            'burst_count':    WeaponStats(value=3,    label='Rajada',   increase=1,     range_val=3),
            'cooldown':       WeaponStats(value=2000, label='Cooldown', increase=-50,   range_val=1, min_val=1500),
            'burst_interval': WeaponStats(value=100,  label=None,       increase=0,     range_val=0),
            'velocidade':     WeaponStats(value=650,  label=None,       increase=0,     range_val=0),
        }
    ),

    'carabin_rifle': WeaponProfile(
            stats={
                'dano':           WeaponStats(value=1,    label='Dano',     increase=1,     range_val=1),
                'burst_count':    WeaponStats(value=5,    label='Rajada',   increase=1,     range_val=[1, 2, 3, 4]),
                'cooldown':       WeaponStats(value=3500, label='Cooldown', increase=-100,  range_val=1, min_val=2500),
                'burst_interval': WeaponStats(value=90,   label=None,       increase=0,     range_val=0),
                'velocidade':     WeaponStats(value=650,  label=None,       increase=0,     range_val=0),
            }
        ),

    'shotgun': WeaponProfile(
        stats={
            'dano':                     WeaponStats(value=1,    label='Dano',              increase=1,      range_val=1),
            'cooldown':                 WeaponStats(value=3000, label='Cooldown',          increase=-100,    range_val=1, min_val=2000),
            'projeteis_por_disparo':    WeaponStats(value=6,    label='N° de Projéteis',   increase=1,      range_val=1),
            'velocidade_projetil':      WeaponStats(value=1000,  label='Velocidade',       increase=50,     range_val=1),
            'spread':                   WeaponStats(value=10,   label='Espalhamento',      increase=2,      range_val=2),
        }
    ),

    'spartan_laser': WeaponProfile(
        stats={
            'dano':               WeaponStats(value=20,   label='Dano',           increase=5,    range_val=1),
            'cooldown':           WeaponStats(value=10000, label='Cadência (ms)', increase=-250, range_val=1, min_val=7500),
            'velocidade_projetil':WeaponStats(value=2800, label=None,             increase=0,    range_val=0),
            'raio_maximo':        WeaponStats(value=800,  label='Alcance',        increase=50,   range_val=1),
            'piercing':           WeaponStats(value=1,    label='Perfuração',     increase=1,    range_val=3),
        }
    ),

    'grenade_launcher': WeaponProfile(
        stats={
            'dano':         WeaponStats(value=30,   label='Dano',          increase=10,  range_val=1),
            'cooldown':     WeaponStats(value=8000, label='Cadência (ms)', increase=-80, range_val=1, min_val=6000),
            'raio_maximo':  WeaponStats(value=650,  label='Alcance',       increase=50,  range_val=1),
        }
    ),

    'sniper_rifle': WeaponProfile(
        stats={
            'dano':               WeaponStats(value=120,  label='Dano',           increase=30,   range_val=1),
            'cooldown':           WeaponStats(value=12000, label='Cadência (ms)', increase=-300, range_val=1, min_val=9000),
            'velocidade_projetil':WeaponStats(value=3000, label=None,             increase=0,    range_val=0),
            'piercing':           WeaponStats(value=1,    label='Perfuração',     increase=1,    range_val=3),
        }
    ),

    'sidekick_pistol': WeaponProfile(
        stats={
            'dano':               WeaponStats(value=4,    label='Dano',          increase=2,    range_val=2),
            'cooldown':           WeaponStats(value=1200, label='Cadência (ms)', increase=-30,  range_val=1, min_val=900),
            'velocidade_projetil':WeaponStats(value=1800, label='Velocidade',     increase=100, range_val=1),
        }
    ),

    'light_rifle': WeaponProfile(
        stats={
            'dano':                 WeaponStats(value=1,     label='Dano',          increase=1,     range_val=2),
            'cooldown':             WeaponStats(value=7500,  label='Cadência (ms)', increase=-250,  range_val=1, min_val=5000),
            'velocidade_projetil':  WeaponStats(value=1800,  label=None,            increase=0,     range_val=0),
            'raio_maximo':          WeaponStats(value=1000,  label='Alcance',       increase=50,    range_val=1),
            'burst_count':          WeaponStats(value=10,    label='Rajada',        increase=1,     range_val=1),
            'burst_interval':       WeaponStats(value=100,   label=None,            increase=0,     range_val=0),
            }
    ),

    'machine_gun': WeaponProfile(
        stats={
            'dano':           WeaponStats(value=1,    label='Dano',     increase=1,     range_val=3),
            'burst_count':    WeaponStats(value=50,   label='Rajada',   increase=10,    range_val=1),
            'cooldown':       WeaponStats(value=20000,label='Cooldown', increase=-500,  range_val=1, min_val=15000),
            'burst_interval': WeaponStats(value=60,   label=None,       increase=0,     range_val=0),
            'velocidade':     WeaponStats(value=950,  label=None,       increase=0,     range_val=0),
        }
    ),

    'mjolnir_punch': WeaponProfile(
        stats={
            'espinhos':           WeaponStats(value=5,    label='Dano de Espinhos', increase=5,     range_val=1),
            'espinho_disponivel': WeaponStats(value=0,    label=None,               increase=0,     range_val=0),
            'cooldown':           WeaponStats(value=1500, label='Cooldown',         increase=-100,  range_val=1, min_val=500),
        }
    ),
    'dizimator': WeaponProfile(
        stats={
            'dano':                 WeaponStats(value=4,     label='Dano',          increase=1,     range_val=1),
            'cooldown':             WeaponStats(value=5000,  label='Cadência (ms)', increase=-250,  range_val=1, min_val=2500),
            'velocidade_projetil':  WeaponStats(value=1200,  label=None,            increase=0,     range_val=0),
            'burst_count':          WeaponStats(value=3,    label='Rajada',        increase=1,     range_val=[3, 5]),
            'burst_interval':       WeaponStats(value=300,   label=None,            increase=0,     range_val=0),
        }
    ),
}

# ===== COMPANION =======================

COMPANION_DATA: Dict[str, CompanionProfile] = {
    'arbiter': CompanionProfile(
        tipo='CAÇADOR',
        stats={
            'velocidade_andar':          WeaponStats(value=250,   label='Vel. Patrulha',    increase=25,  range_val=1),
            'velocidade_correr':         WeaponStats(value=320,   label='Vel. Corrida',     increase=30,  range_val=1),
            'raio_deteccao_inimigo':     WeaponStats(value=450,   label='Raio de Caça',     increase=50,  range_val=1),
            'dano':                      WeaponStats(value=10,    label='Dano',             increase=5,   range_val=1),
            'pode_atirar':               WeaponStats(value=False, label=None,               increase=0,   range_val=0),
            'velocidade_animacao':       WeaponStats(value=120,   label=None,               increase=0,   range_val=0),
            'distancia_maxima_retorno':  WeaponStats(value=600,   label=None,               increase=0,   range_val=0),
            'angulo_orbita':             WeaponStats(value=0,     label=None,               increase=0,   range_val=0),
            'raio_orbita':               WeaponStats(value=80,    label=None,               increase=0,   range_val=0),
            'velocidade_orbita':         WeaponStats(value=5,     label=None,               increase=0,   range_val=0),
            'ultimo_dano_tempo':         WeaponStats(value=0,     label=None,               increase=0,   range_val=0),
            'cooldown':                  WeaponStats(value=1000,  label='Cooldown',         increase=-50, range_val=1, min_val=500),
        }
    ),

    'cortana': CompanionProfile(
        tipo='COLETOR',
        stats={
            'velocidade_andar':          WeaponStats(value=180,   label='Velocidade Base',                 increase=30,  range_val=1),
            'velocidade_correr':         WeaponStats(value=280,   label='Velocidade de Busca',             increase=40,  range_val=1),
            'raio_deteccao_item':        WeaponStats(value=400,   label='Raio de Busca',                   increase=50,  range_val=1),
            'pode_atirar':               WeaponStats(value=False, label=None,                              increase=0,   range_val=0),
            'velocidade_animacao':       WeaponStats(value=200,   label=None,                              increase=0,   range_val=0),
            'distancia_maxima_retorno':  WeaponStats(value=500,   label=None,                              increase=0,   range_val=0),
            'jogador_speed_bonus':       WeaponStats(value=0,     label='Bônus de Velocidade do Jogador',  increase=10,  range_val=1),
        }
    ),

    'marine': CompanionProfile(
        tipo='MISTO',
        stats={
            'velocidade_andar':          WeaponStats(value=120,   label='Vel. Patrulha',       increase=20,  range_val=1),
            'velocidade_correr':         WeaponStats(value=180,   label='Vel. Sprint',         increase=20,  range_val=1),
            'raio_deteccao_inimigo':     WeaponStats(value=450,   label='Detecção de Inimigos',increase=50,  range_val=1),
            'raio_deteccao_item':        WeaponStats(value=250,   label='Detecção de Itens',   increase=25,  range_val=1),
            'range_tiro':                WeaponStats(value=400,   label='Alcance do Disparo',  increase=40,  range_val=1),
            'cooldown_tiro':             WeaponStats(value=1000,  label='Vel. de Ataque (ms)', increase=-50, range_val=1, min_val=500),
            'dano':                      WeaponStats(value=1,     label='Dano',                increase=1,   range_val=1),
            'pode_atirar':               WeaponStats(value=True,  label=None,                  increase=0,   range_val=0),
            'distancia_seguidor':        WeaponStats(value=150,   label=None,                  increase=0,   range_val=0),
            'distancia_maxima_retorno':  WeaponStats(value=750,   label=None,                  increase=0,   range_val=0),
            'velocidade_animacao':       WeaponStats(value=200,   label=None,                  increase=0,   range_val=0),
            '_soldados':                 WeaponStats(value=None,  label='N° de Soldados',      increase=1,   range_val=[3, 5, 7]),
        }
    )
}

