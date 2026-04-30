COMPANION_DATA = {
    'arbiter': {
        'tipo': 'CAÇADOR',
        'stats': {
            'velocidade_andar':         {'value': 250,   'label': None,                   'increase': 10,  'range': 1},
            'velocidade_correr':        {'value': 320,   'label': 'Velocidade',           'increase': 30,  'range': 1},
            'raio_deteccao_inimigo':    {'value': 450,   'label': 'Raio de Caça',         'increase': 50,  'range': 1},
            'dano':                     {'value': 10,    'label': 'Dano',                 'increase': 5,   'range': 1},
            'pode_atirar':              {'value': False, 'label': None,                   'increase': 0,   'range': 0},
            'velocidade_animacao':      {'value': 120,   'label': None,                   'increase': 0,   'range': 0},
            'distancia_maxima_retorno': {'value': 600,   'label': None,                   'increase': 0,   'range': 0},
            'angulo_orbita':            {'value': 0,     'label': None,                   'increase': 0,   'range': 0},
            'raio_orbita':              {'value': 80,    'label': None,                   'increase': 0,   'range': 0},
            'velocidade_orbita':        {'value': 5,     'label': None,                   'increase': 0,   'range': 0},
            'ultimo_dano_tempo':        {'value': 0,     'label': None,                   'increase': 0,   'range': 0},
            'cooldown':                 {'value': 1000,  'label': None,                   'increase': 0,   'range': 0},
        }
    },

    'cortana': {
        'tipo': 'COLETOR',
        'stats': {
            'velocidade_andar':         {'value': 180,   'label': 'Velocidade Base',      'increase': 25,  'range': 1},
            'velocidade_correr':        {'value': 280,   'label': 'Velocidade de Busca',  'increase': 25,  'range': 1},
            'raio_deteccao_item':       {'value': 400,   'label': 'Raio de Busca',        'increase': 50,  'range': 1},
            'pode_atirar':              {'value': False, 'label': None,                   'increase': 0,   'range': 0},
            'velocidade_animacao':      {'value': 200,   'label': None,                   'increase': 0,   'range': 0},
            'distancia_maxima_retorno': {'value': 500,   'label': None,                   'increase': 0,   'range': 0},
        }
    },

    'marine': {
        'tipo': 'MISTO',
        'stats': {
            'velocidade_andar':         {'value': 120,   'label': None,                    'increase': 0,   'range': 0},
            'velocidade_correr':        {'value': 180,   'label': 'Velocidade',            'increase': 15,  'range': 1},
            'raio_deteccao_inimigo':    {'value': 450,   'label': 'Detecção de Inimigos',  'increase': 40,  'range': 1},
            'raio_deteccao_item':       {'value': 250,   'label': 'Detecção de Itens',     'increase': 30,  'range': 1},
            'range_tiro':               {'value': 400,   'label': 'Alcance',               'increase': 30,  'range': 1},
            'cooldown_tiro':            {'value': 1000,  'label': 'Vel. de Ataque (ms)',   'increase': -20, 'range': 1,  'min': 500},
            'dano':                     {'value': 1,     'label': 'Dano',                  'increase': 1,   'range': 1},
            'pode_atirar':              {'value': True,  'label': None,                    'increase': 0,   'range': 0},
            'distancia_seguidor':       {'value': 150,   'label': None,                    'increase': 0,   'range': 0},
            'distancia_maxima_retorno': {'value': 750,   'label': None,                    'increase': 0,   'range': 0},
            'velocidade_animacao':      {'value': 200,   'label': None,                    'increase': 0,   'range': 0},
            # Soldados é gerenciado pela arma, não pelo companion
            '_soldados':                {'value': None,  'label': 'Soldados',              'increase': 1,   'range': [3, 5, 7]},
        }
    }
}

WEAPON_DATA = {
    'rifle_assalto': {
        'stats': {
            'dano':                  {'value': 1,    'label': 'Dano',             'increase': 1,   'range': 1},
            'cooldown':              {'value': 500,  'label': 'Cadência (ms)',    'increase': -20, 'range': 2,  'min': 100},
            'projeteis_por_disparo': {'value': 1,    'label': 'Projéteis',        'increase': 1,   'range': [3, 5, 7, 9]},
            'velocidade_projetil':   {'value': 2000, 'label': None,               'increase': 0,   'range': 0},
        }
    },

    'bola_calderânica': {
        'stats': {
            'dano':     {'value': 5,    'label': 'Dano',    'increase': 2,  'range': 1},
            'rebatidas':{'value': 2,    'label': 'Rebotes', 'increase': 1,  'range': 1},
            'velocidade':{'value': 1000,'label': None,      'increase': 0,  'range': 0},
            'cooldown': {'value': 1000, 'label': None,      'increase': 0,  'range': 0},
        }
    },

    'ciclo_de_laminas': {
        'stats': {
            'dano':              {'value': 15,   'label': 'Dano',              'increase': 5,  'range': 1},
            'velocidade_rotacao':{'value': 120,  'label': 'Velocidade Angular','increase': 10, 'range': 1},
            'distancia_orbita':  {'value': 140,  'label': 'Raio da Órbita',    'increase': 10, 'range': 1},
            'num_listas':        {'value': 1,    'label': 'Num. Listas',       'increase': 1,  'range': 2},
            'duracao':           {'value': 5000, 'label': None,                'increase': 0,  'range': 0},
            'cooldown':          {'value': 6000, 'label': None,                'increase': 0,  'range': 0},
        }
    },

    'dicionario_divino': {
        'stats': {
            'dano_por_segundo': {'value': 1,          'label': 'Dano/s',  'increase': 1,  'range': 2},
            'raio':             {'value': 120,         'label': 'Raio',   'increase': 20, 'range': 1},
            'cooldown':         {'value': float('inf'),'label': None,     'increase': 0,  'range': 0},
        }
    },

    'needler': {
        'stats': {
            'dano':           {'value': 1,    'label': 'Dano',           'increase': 1,  'range': 1},
            'burst_count':    {'value': 3,    'label': 'Rajada',         'increase': 1,  'range': 3},
            'cooldown':       {'value': 2000, 'label': None,             'increase': 0,  'range': 0},
            'burst_interval': {'value': 100,  'label': None,             'increase': 0,  'range': 0},
            'velocidade':     {'value': 650,  'label': None,             'increase': 0,  'range': 0},
        }
    },
}