"""Todos os números do Hunter num lugar só (balanceamento sem caçar valor no código)."""
import math
from dataclasses import dataclass, field
from typing import Dict, Tuple

from source.systems.status import Defesa


@dataclass(frozen=True)
class HunterConfig:
    # --- atributos ---
    vida: int = 800
    dano_contato: int = 40
    velocidade: float = 40

    # --- armadura: Defesa sem fim, tirada enquanto o jogador está nas costas (vulnerável) ---
    defesa: float = 0.9
    costas_graus: float = 30            # meia-abertura do cone das costas (±30° do eixo x dele)

    # --- virar o sprite com atraso (o timer não reinicia com spam de lado) ---
    atraso_virar_ms: int = 1500
    atraso_virar_pos_dash_ms: int = 2500   # e é também a recuperação parada depois do dash

    # --- decisão ---
    dist_perto: float = 450             # dentro disso ele prefere os golpes físicos
    pausa_entre_ataques_ms: int = 1000
    repetir_mult: float = 0.4           # peso de repetir a última habilidade
    pesos_longe: Dict[str, float] = field(default_factory=lambda: {
        'canhao': 5, 'burst': 5, 'dash': 1, 'slam': 0})
    pesos_perto: Dict[str, float] = field(default_factory=lambda: {
        'canhao': 1, 'burst': 1, 'dash': 6, 'slam': 8})
    # cooldowns (min, max) em ms, sorteados no FIM da habilidade
    cooldown: Dict[str, Tuple[int, int]] = field(default_factory=lambda: {
        'canhao': (6000, 12000), 'burst': (4000, 9000), 'dash': (8000, 14000), 'slam': (4000, 7000)})
    cooldown_inicial: Dict[str, int] = field(default_factory=lambda: {
        'canhao': 1500, 'burst': 2500, 'dash': 3000, 'slam': 1500})

    # --- movimentação livre (fora do dash, do slam e da recuperação) ---
    troca_movimento_ms: Tuple[int, int] = (1000, 2500)
    chance_lateral: float = 0.5         # resto: avança direto no jogador

    # --- burst (plasma) ---
    burst_tiros: int = 10
    burst_intervalo_ms: int = 150
    burst_dano: int = 15
    burst_velocidade: float = 500
    burst_spread: float = 0.15
    burst_tamanho: Tuple[int, int] = (36, 36)

    # --- canhão (morteiro parabólico) ---
    canhao_preset: str = 'hunter_cannon'

    # --- dash ---
    dash_preset: str = 'hunter'
    dash_animacao_ms: int = 250

    # --- shield slam (cone de 90° à frente) ---
    slam_preset: str = 'hunter_shield_slam'
    slam_dist: float = 230              # só dispara com o jogador colado...
    slam_frente_graus: float = 45       # ... e na frente dele (meia-abertura)

    # --- vfx ---
    brilho_cor: Tuple[int, int, int] = (255, 30, 30)
    brilho_alpha: Tuple[int, int] = (35, 105)   # pulsa entre estes valores
    brilho_periodo_ms: int = 600
    poeira_dash_intervalo_ms: int = 90
    poeira_dash_por_lado: int = 1
    poeira_explosao: int = 14
    poeira_slam: int = 26

    def __post_init__(self):
        if set(self.pesos_longe) != set(self.cooldown) or set(self.pesos_perto) != set(self.cooldown) \
                or set(self.cooldown_inicial) != set(self.cooldown):
            raise ValueError('HunterConfig: pesos, cooldowns e cooldown inicial precisam ter as mesmas habilidades')
        if not 0 < self.costas_graus < 90 or not 0 < self.slam_frente_graus < 90:
            raise ValueError('HunterConfig: ângulos precisam estar entre 0 e 90 graus')

    @property
    def cos_costas(self):
        return math.cos(math.radians(self.costas_graus))

    @property
    def cos_frente_slam(self):
        return math.cos(math.radians(self.slam_frente_graus))


CFG = HunterConfig()
DEFESA = Defesa(CFG.defesa)            # sem fim: o Hunter a tira e põe de volta (chave = ele mesmo)
COS_COSTAS = CFG.cos_costas
COS_FRENTE_SLAM = CFG.cos_frente_slam
