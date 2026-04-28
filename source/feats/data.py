


COMPANION_DATA = {
    'arbiter': {
        'stats': {
            'velocidade_andar': 250, 
            'velocidade_correr': 320, 
            'raio_deteccao_inimigo': 450, 
            'dano': 10, 
            'pode_atirar': False, 
            'velocidade_animacao': 120,
            'distancia_maxima_retorno': 600,            
            'angulo_orbita': 0,
            'raio_orbita': 80,
            'velocidade_orbita': 5,
            'ultimo_dano_tempo': 0,
            'cooldown': 1000
            },

        'tipo': 'CAÇADOR'
    },

    'cortana': {
        'stats': {
            'velocidade_andar': 180,
            'velocidade_correr': 280, 
            'raio_deteccao_item': 400, 
            'pode_atirar': False, 
            'velocidade_animacao': 200,
            'distancia_maxima_retorno': 500            
            },

        'tipo': 'COLETOR'
    },

    'marine': {
        'stats': {
            'velocidade_andar': 120, 
            'velocidade_correr': 180, 
            'raio_deteccao_item': 250, 
            'raio_deteccao_inimigo': 450, 
            'pode_atirar': True, 
            'distancia_seguidor': 150,
            'range_tiro': 400, 
            'cooldown_tiro': 1000, 
            'velocidade_animacao': 200,
            'distancia_maxima_retorno': 750
            },

        'tipo': 'MISTO'
    }
}