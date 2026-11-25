# source/feats/skills/purge_grid/config.py
from dataclasses import dataclass
from typing import Optional, Tuple
import math

@dataclass
class PurgeConfig:
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
    offset_angulo: float = 0.0      # Permite girar o ataque inteiro
    angulo_aleatorio: bool = False  # 'linha_jogador': soma um ângulo sorteado ao offset
    cor_borda: Tuple[int, int, int, int] = (255, 50, 0, 150)
    cor_preenchimento: Tuple[int, int, int, int] = (255, 50, 0, 50)
    cor_explosao: Tuple[int, int, int, int] = (255, 100, 50, 220)
    disparo: Optional[str] = None   # preset de `disparo.py`: um tiro cai do céu em cada ponto (só visual)


# === CARDÁPIO DE ATAQUES ===
PURGE_PRESETS = {
    'padrao': PurgeConfig(),

    # Fase 1: (Para Cima, Baixo-Direita, Baixo-Esquerda)
    'tartarus_smash_1': PurgeConfig(
        modo='eixos_inimigo',
        qtd_eixos=3,
        artilharias_por_eixo=10,
        espacamento=150,
        raio_artilharia=150,
        dano=150,
        intervalo=80, 
        duracao_aviso=500,
        offset_angulo=-math.pi / 2, # -90 graus (Aponta pro Norte)
        cor_borda=(0, 150, 255, 150),       # Azul Halo
        cor_preenchimento=(0, 50, 255, 60),
        cor_explosao=(50, 200, 255, 220)
    ),
    
    # Fase 2: Invertido (Para Baixo, Cima-Esquerda, Cima-Direita)
    'tartarus_smash_2': PurgeConfig(
        modo='eixos_inimigo',
        qtd_eixos=3,
        artilharias_por_eixo=10,
        espacamento=150,
        raio_artilharia=150,
        dano=150,
        intervalo=80, 
        duracao_aviso=500,
        offset_angulo=math.pi / 2,  # +90 graus (Aponta pro Sul)
        cor_borda=(0, 150, 255, 150),
        cor_preenchimento=(0, 50, 255, 60),
        cor_explosao=(50, 200, 255, 220)
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
    
    'tentaculos_perseguidores': PurgeConfig(
        modo='inimigo_player',
        artilharias_por_eixo=15,
        espacamento=180,
        dano=200,
        intervalo=150,
        raio_artilharia=160,
        duracao_aviso=400,
        cor_preenchimento=(132, 130, 101, 100), # Marrom Musgo do Flood
        cor_explosao=(150, 100, 0, 220)      # Laranja do Gravemind
    ),

    'assassino_cross': PurgeConfig(
        modo='eixos_inimigo',
        qtd_eixos=4,               # 4 linhas formando um X
        artilharias_por_eixo=7,    # Tamanho das linhas
        espacamento=100,
        raio_artilharia=70,        # Mais estreito e fatal
        dano=180,
        intervalo=70,              # Rápido!
        duracao_aviso=450,
        offset_angulo=math.pi / 4, # Gira 45 graus (pi/4) para formar o "X"
        cor_borda=(230, 150, 100, 200),     # Roxo Veneno/Sombra
        cor_preenchimento=(255, 210, 0, 80),
        cor_explosao=(218, 190, 214, 250)
    ),

    # Bombardeio do Phantom (Arbiter): uma linha que varre o mapa passando pelo jogador, em ângulo sorteado
    'arbiter_phantom': PurgeConfig(
        modo='linha_jogador',
        artilharias_por_eixo=10,
        espacamento=140,
        raio_artilharia=130,
        dano=150,
        intervalo=150,
        duracao_aviso=1500,
        angulo_aleatorio=True,
        cor_borda=(170, 110, 255, 210),       # azul-arroxeado do plasma Covenant
        cor_preenchimento=(110, 70, 255, 70),
        cor_explosao=(215, 190, 255, 240),
        disparo='phantom'                     # o canhão do Phantom acerta cada ponto
    ),
}
