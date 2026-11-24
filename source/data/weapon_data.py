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
    'assault_rifle': WeaponProfile(
        stats={
            'dano':                  WeaponStats(value=1,    label='Dano',          increase=1,   range_val=1),
            'cooldown':              WeaponStats(value=500,  label='Cadência (ms)', increase=-20, range_val=2, min_val=260),
            'projeteis_por_disparo': WeaponStats(value=1,    label='Projéteis',     increase=1,   range_val=[2, 4, 6, 8, 10]),
            'velocidade_projetil':   WeaponStats(value=2400, label=None,            increase=0,   range_val=0),
            'raio_maximo':           WeaponStats(value=600,  label='Alcance',       increase=25,  range_val=1),
        }
    ),

    'brick': WeaponProfile(
        stats={
            'dano':       WeaponStats(value=1,    label='Dano',       increase=1,     range_val=1),
            'rebatidas':  WeaponStats(value=3,    label='Rebotes',    increase=2,     range_val=1),
            'velocidade': WeaponStats(value=1000, label='Velocidade', increase=250,   range_val=1),
            'cooldown':   WeaponStats(value=2000, label='Cooldown',   increase=-250,  range_val=1, min_val=1000),
            'raio_maximo': WeaponStats(value=1200, label=None,        increase=0,     range_val=0),
        }
    ),

    'energy_sword': WeaponProfile(
        stats={
            'dano':               WeaponStats(value=5,    label='Dano',              increase=5,   range_val=1),
            'velocidade_rotacao': WeaponStats(value=120,  label='Velocidade Angular',increase=10,  range_val=1),
            'distancia_orbita':   WeaponStats(value=130,  label=None,                increase=0,   range_val=0),
            'num_listas':         WeaponStats(value=1,    label='Num. Listas',       increase=1,   range_val=[2, 3, 4, 5]),
            'duracao':            WeaponStats(value=5000, label='Duração',           increase=200, range_val=1),
            'cooldown':           WeaponStats(value=12700,label='Cooldown',          increase=-300, range_val=1, min_val=10000),
        }
    ),

    'mk2_shield': WeaponProfile(
        stats={
            'dano_por_segundo':        WeaponStats(value=1,           label='Dano/s',       increase=1,   range_val=1),
            'raio':                    WeaponStats(value=150,         label='Raio',         increase=30,  range_val=1),
            'cooldown':                WeaponStats(value=float('inf'),label=None,           increase=0,   range_val=0),
            'escudo':                  WeaponStats(value=100,          label='Escudo',       increase=50,  range_val=1),
            'shield_regen':            WeaponStats(value=4000,        label='Delay Regen',  increase=-50, range_val=1, min_val=2800),
            'velocidade_regen_escudo': WeaponStats(value=60,          label='Shield Regen', increase=30,   range_val=1),
        }
    ),

    'needler': WeaponProfile(
        stats={
            'dano':           WeaponStats(value=1,    label='Dano',     increase=1,     range_val=1),
            'burst_count':    WeaponStats(value=3,    label='Rajada',   increase=1,     range_val=3),
            'cooldown':       WeaponStats(value=2000, label='Cooldown', increase=-25,   range_val=1, min_val=1525),
            'burst_interval': WeaponStats(value=100,  label=None,       increase=0,     range_val=0),
            'velocidade':     WeaponStats(value=650,  label=None,       increase=0,     range_val=0),
            'raio_maximo':    WeaponStats(value=500,  label='Alcance',  increase=25,    range_val=1,),
        }
    ),

    'carabin_rifle': WeaponProfile(
            stats={
                'dano':           WeaponStats(value=1,    label='Dano',     increase=1,     range_val=1),
                'burst_count':    WeaponStats(value=5,    label='Rajada',   increase=1,     range_val=[2, 3, 4, 5]),
                'cooldown':       WeaponStats(value=3500, label='Cooldown', increase=-70,   range_val=1, min_val=2520),
                'burst_interval': WeaponStats(value=90,   label=None,       increase=0,     range_val=0),
                'velocidade':     WeaponStats(value=650,  label=None,       increase=0,     range_val=0),
                'raio_maximo':    WeaponStats(value=650,  label='Alcance',  increase=25,    range_val=2),
            }
        ),

    'shotgun': WeaponProfile(
        stats={
            'dano':                     WeaponStats(value=1,    label='Dano',              increase=1,      range_val=1),
            'cooldown':                 WeaponStats(value=3000, label='Cooldown',          increase=-50,   range_val=1, min_val=2050),
            'projeteis_por_disparo':    WeaponStats(value=8,    label='N° de Projéteis',   increase=4,      range_val=1),
            'velocidade_projetil':      WeaponStats(value=1000, label='Velocidade',        increase=50,     range_val=1),
            'spread':                   WeaponStats(value=5,    label='Espalhamento',      increase=5,      range_val=2),
            'raio_maximo':              WeaponStats(value=500,  label=None,                increase=0,      range_val=0),
        }
    ),

    'spartan_laser': WeaponProfile(
        stats={
            'dano':               WeaponStats(value=20,   label='Dano',           increase=5,    range_val=1),
            'cooldown':           WeaponStats(value=10000, label='Cadência (ms)', increase=-625, range_val=1, min_val=7500),
            'velocidade_projetil':WeaponStats(value=2800, label=None,             increase=0,    range_val=0),
            'raio_maximo':        WeaponStats(value=800,  label='Alcance',        increase=50,   range_val=1),
            'piercing':           WeaponStats(value=1,    label='Perfuração',     increase=1,    range_val=1),
        }
    ),

    'grenade_launcher': WeaponProfile(
        stats={
            'dano':         WeaponStats(value=30,   label='Dano',          increase=10,  range_val=1),
            'cooldown':     WeaponStats(value=8000, label='Cadência (ms)', increase=-150, range_val=1, min_val=5900),
            'raio_maximo':  WeaponStats(value=650,  label='Alcance',       increase=25,  range_val=1),
        }
    ),

    'sniper_rifle': WeaponProfile(
        stats={
            'dano':               WeaponStats(value=120,  label='Dano',           increase=40,   range_val=1),
            'cooldown':           WeaponStats(value=12000,label='Cadência (ms)',  increase=-350, range_val=1, min_val=8850),
            'velocidade_projetil':WeaponStats(value=3000, label=None,             increase=0,    range_val=0),
            'piercing':           WeaponStats(value=1,    label='Perfuração',     increase=1,    range_val=3),
            'raio_maximo':        WeaponStats(value=1200, label='Alcance',        increase=50,   range_val=1),
        }
    ),

    'sidekick_pistol': WeaponProfile(
        stats={
            'dano':               WeaponStats(value=4,    label='Dano',           increase=2,    range_val=2),
            'cooldown':           WeaponStats(value=1200, label='Cadência (ms)',  increase=-12,  range_val=1, min_val=912),
            'velocidade_projetil':WeaponStats(value=1800, label='Velocidade',     increase=100,  range_val=1),
            'raio_maximo':        WeaponStats(value=450,  label='Alcance',        increase=25,   range_val=1),
        }
    ),

    'light_rifle': WeaponProfile(
        stats={
            'dano':                 WeaponStats(value=1,     label='Dano',          increase=1,     range_val=2),
            'cooldown':             WeaponStats(value=7500,  label='Cadência (ms)', increase=-625,  range_val=1, min_val=5000),
            'velocidade_projetil':  WeaponStats(value=1600,  label=None,            increase=0,     range_val=0),
            'raio_maximo':          WeaponStats(value=700,   label='Alcance',       increase=50,    range_val=1),
            'burst_count':          WeaponStats(value=12,    label='Rajada',        increase=2,     range_val=1),
            'burst_interval':       WeaponStats(value=100,   label=None,            increase=0,     range_val=0),
            }
    ),

    'machine_gun': WeaponProfile(
        stats={
            'dano':           WeaponStats(value=1,    label='Dano',     increase=1,     range_val=3),
            'burst_count':    WeaponStats(value=40,   label='Rajada',   increase=15,    range_val=1),
            'cooldown':       WeaponStats(value=20000,label='Cooldown', increase=-1250, range_val=1, min_val=15000),
            'burst_interval': WeaponStats(value=60,   label=None,       increase=0,     range_val=0),
            'velocidade':     WeaponStats(value=950,  label=None,       increase=0,     range_val=0),
            'raio_maximo':    WeaponStats(value=600,  label='Alcance',  increase=50,    range_val=1),
        }
    ),

    'mjolnir_punch': WeaponProfile(
        stats={
            'espinhos':           WeaponStats(value=5,    label='Dano de Espinhos', increase=5,     range_val=1),
            'espinho_disponivel': WeaponStats(value=0,    label=None,               increase=0,     range_val=0),
            'cooldown':           WeaponStats(value=1500, label='Cooldown',         increase=-50,  range_val=1, min_val=300),
        }
    ),
    'dizimator': WeaponProfile(
        stats={
            'dano':                 WeaponStats(value=4,     label='Dano',          increase=1,     range_val=1),
            'cooldown':             WeaponStats(value=5000,  label='Cadência (ms)', increase=-125,  range_val=1, min_val=2625),
            'velocidade_projetil':  WeaponStats(value=1200,  label=None,            increase=0,     range_val=0),
            'burst_count':          WeaponStats(value=3,     label='Rajada',        increase=1,     range_val=[2, 3, 4, 5]),
            'burst_interval':       WeaponStats(value=300,   label=None,            increase=0,     range_val=0),
            'raio_maximo':          WeaponStats(value=550,   label=None, increase=0, range_val=0),
        }
    ),
    'fuel_rod': WeaponProfile(
        stats={
            'dano':         WeaponStats(value=25,   label='Dano',           increase=10,    range_val=1),
            'dot':          WeaponStats(value=3,    label='Dano do Veneno', increase=1,     range_val=1),
            'quique':       WeaponStats(value=1,    label='Quiques',        increase=1,     range_val=1),
            'duracao':      WeaponStats(value=4000, label='Duração',        increase=1000,  range_val=1),
            'cooldown':     WeaponStats(value=12000,label='Cadência (ms)',  increase=-450,  range_val=1, min_val=7950),
            'raio_maximo':  WeaponStats(value=750,  label='Alcance',        increase=50,    range_val=1),
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
            'cooldown':                  WeaponStats(value=1000,  label='Cooldown',         increase=-60, range_val=1, min_val=460),
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
            # Em pontos percentuais: vira um BuffVelocidade sem fim no jogador (sistema de status)
            'jogador_speed_bonus':       WeaponStats(value=0,     label='Bônus de Velocidade do Jogador (%)', increase=2, range_val=1),
        }
    ),

    'marine': CompanionProfile(
        tipo='MISTO',
        stats={
            'velocidade_andar':          WeaponStats(value=120,     label='Vel. Patrulha',       increase=20,  range_val=1),
            'velocidade_correr':         WeaponStats(value=180,     label='Vel. Sprint',         increase=20,  range_val=1),
            'raio_deteccao_inimigo':     WeaponStats(value=450,     label='Detecção de Inimigos',increase=50,  range_val=1),
            'raio_deteccao_item':        WeaponStats(value=250,     label='Detecção de Itens',   increase=25,  range_val=1),
            'range_tiro':                WeaponStats(value=400,     label='Alcance do Disparo',  increase=40,  range_val=1),
            'range_rifle':               WeaponStats(value=400,     label='Alcance do Disparo',  increase=40,  range_val=1),
            'cooldown_tiro_burst':       WeaponStats(value=1000,    label='Vel. de Ataque (ms)', increase=-35, range_val=1, min_val=510),
            'dano_burst':                WeaponStats(value=1,       label='Dano',                increase=1,   range_val=1),
            'pode_atirar':               WeaponStats(value=True,    label=None,                  increase=0,   range_val=0),
            'distancia_seguidor':        WeaponStats(value=150,     label=None,                  increase=0,   range_val=0),
            'distancia_maxima_retorno':  WeaponStats(value=750,     label=None,                  increase=0,   range_val=0),
            'velocidade_animacao':       WeaponStats(value=200,     label=None,                  increase=0,   range_val=0),
            '_soldados':                 WeaponStats(value=None,    label='N° de Soldados',      increase=1,   range_val=[3, 5, 7]),
        }
    ),

    'noble': CompanionProfile(
        tipo='CAÇADOR',
        stats={
            'velocidade_andar':          WeaponStats(value=230,   label='Vel. Patrulha',        increase=20,  range_val=1),
            'velocidade_correr':         WeaponStats(value=280,   label='Vel. Corrida',         increase=30,  range_val=1),
            'raio_deteccao_inimigo':     WeaponStats(value=900,   label='Raio de Caça',         increase=50,  range_val=1),
            'dano_burst':                WeaponStats(value=3,     label='Dano do Rifle',        increase=2,   range_val=1),
            'dano_sniper':               WeaponStats(value=30,    label='Dano da Sniper',       increase=10,   range_val=1),
            'range_tiro':                WeaponStats(value=1200,  label=None,   increase=40,  range_val=1),
            'cooldown_tiro_burst':       WeaponStats(value=1000,  label='Vel. de Ataque Rifle (ms)',  increase=-125, range_val=1, min_val=500),
            'range_sniper':              WeaponStats(value=1200,  label='Alcance do Disparo Sniper',   increase=100,  range_val=1),
            'cooldown_tiro_sniper':      WeaponStats(value=10000, label='Vel. de Ataque Sniper(ms)',  increase=-1250, range_val=1, min_val=5000),
            'range_rifle':               WeaponStats(value=600,   label='Alcance do Disparo Rifle',   increase=50,  range_val=[2, 3, 4]),
            'pode_atirar':               WeaponStats(value=True,  label=None,                   increase=0,   range_val=0),
            'velocidade_animacao':       WeaponStats(value=120,   label=None,                   increase=0,   range_val=0),
            'distancia_maxima_retorno':  WeaponStats(value=1000,  label=None,                   increase=0,   range_val=0),
        }
    ),
}


# ===== VEHICLES =========================

VEHICLES_DATA: Dict[str, CompanionProfile] = {
    'warhog': CompanionProfile(
        tipo='VEICULO',
        stats={
            'vida_maxima':             WeaponStats(value=200,   label='Vida do Veículo',              increase=40,   range_val=1),
            'dano_burst':              WeaponStats(value=1,     label='Dano da Metralhadora',         increase=1,    range_val=2),
            'cooldown_tiro_burst':     WeaponStats(value=300,   label='Cadência (ms)',                increase=-8,  range_val=1, min_val=148),
            'raio_deteccao_inimigo':   WeaponStats(value=650,   label='Raio de Mira',                 increase=50,   range_val=1),
            'dano_atropelamento':      WeaponStats(value=15,    label='Dano de Atropelamento',        increase=5,    range_val=1),
            'raio_atropelamento':      WeaponStats(value=70,    label=None,                           increase=0,    range_val=0),
            'cooldown_atropelamento':  WeaponStats(value=400,   label=None,                           increase=0,    range_val=0),
            'cooldown_destruicao':     WeaponStats(value=50000, label='Cooldown p/ Reutilizar (ms)',  increase=-500,range_val=1, min_val=40500),
            'velocidade_animacao':     WeaponStats(value=150,   label=None,                           increase=0,    range_val=0),
        }
    ),

    'pelican': CompanionProfile(
            tipo='VEICULO',
            stats={
                'vida_maxima':             WeaponStats(value=400,   label='Vida do Veículo',              increase=40,   range_val=1),
                'dano_burst':              WeaponStats(value=4,     label='Dano da Metralhadora',         increase=1,    range_val=2),
                'cooldown_tiro_burst':     WeaponStats(value=300,   label='Cadência (ms)',                increase=-17,  range_val=1, min_val=147),
                'raio_deteccao_inimigo':   WeaponStats(value=650,   label='Raio de Mira',                 increase=50,   range_val=1),
                'dano_atropelamento':      WeaponStats(value=15,    label='Dano de Atropelamento',        increase=5,    range_val=1),
                'raio_atropelamento':      WeaponStats(value=70,    label=None,                           increase=0,    range_val=0),
                'cooldown_atropelamento':  WeaponStats(value=400,   label=None,                           increase=0,    range_val=0),
                'cooldown_destruicao':     WeaponStats(value=50000, label='Cooldown p/ Reutilizar (ms)',  increase=-1200,range_val=1, min_val=39200),
                'velocidade_animacao':     WeaponStats(value=150,   label=None,                           increase=0,    range_val=0),
            }
        ),
}
