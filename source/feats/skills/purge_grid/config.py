# source/feats/skills/purge_grid/config.py
from dataclasses import dataclass
from typing import Tuple

@dataclass
class PurgeConfig:
    # Valores padrão (o que era o seu init antigo)
    modo: str = 'grid'
    qtd_eixos: int = 1
    artilharias_por_eixo: int = 5
    espacamento: int = 80
    raio_artilharia: int = 40
    dano: int = 10
    intervalo: int = 150
    direcao_inicio: str = 'north'
    direcao: str = 'exit'
    duracao_aviso: int = 300
    cor_borda: Tuple[int, int, int, int] = (255, 50, 0, 150)
    cor_preenchimento: Tuple[int, int, int, int] = (255, 50, 0, 50)
    cor_explosao: Tuple[int, int, int, int] = (255, 100, 50, 220)


# === SEU CARDÁPIO DE ATAQUES ===
# Aqui você cria as variações do ataque mudando só o que precisa!
PURGE_PRESETS = {
    'padrao': PurgeConfig(),

    'guilty_hell_x': PurgeConfig(
        modo='eixo_x', 
        qtd_eixos=6, 
        artilharias_por_eixo=35, 
        espacamento=400, 
        raio_artilharia=150, 
        dano=100, 
        intervalo=450, 
        duracao_aviso=600, 
        direcao_inicio='west',
        cor_preenchimento=(255, 0, 0, 80),
        cor_explosao=(200, 200, 255, 120)
    ),
    
    'guilty_hell_y': PurgeConfig(
        modo='eixo_y', 
        qtd_eixos=4, 
        artilharias_por_eixo=25, 
        espacamento=500, 
        raio_artilharia=150, 
        dano=100, 
        intervalo=450, 
        duracao_aviso=600, 
        direcao_inicio='north',
        cor_preenchimento=(255, 0, 0, 80),
        cor_explosao=(200, 200, 255, 120)
    ),
    
    'grid_fechado_rapido': PurgeConfig(
        modo='grid',
        artilharias_por_eixo=8,
        espacamento=50,
        intervalo=80,
        duracao_aviso=200
    ),
    
    'desespero_radial': PurgeConfig(
        modo='eixos_inimigo',
        qtd_eixos=8,
        artilharias_por_eixo=6,
        intervalo=100,
        cor_preenchimento=(255, 0, 200, 60) 
    ),
    
    'snyper_direcional': PurgeConfig(
        modo='inimigo_player',
        artilharias_por_eixo=12,
        intervalo=50
    )
}