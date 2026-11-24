"""Todos os números do Guilty Spark num lugar só (balanceamento sem caçar valor no código).

Danos, raios, avisos e cores das artilharias ficam nos presets `guilty_*` de
`feats/skills/artilharia/config.py`."""
from dataclasses import dataclass, field
from typing import Dict, Tuple

from source.enemies.base.boss import Clip, ConfigTravamento, FaseBoss

# nome, vida em que começa, mult. de cooldown, mult. de velocidade
FASES = (
    FaseBoss('Ronda', 1.00, 1.0, 1.0),
    FaseBoss('Protocolo de Contenção', 0.60, 1.0, 2.0),
    FaseBoss('Monitor Debilitado', 0.20, 1.0, 1.0),
)

# nome da habilidade -> `estado_habilidade`
ESTADOS = {
    'proximidade': 'feixe_proximidade', 'laser': 'laser', 'teleporte': 'teleporte',
    'antistuck': 'antistuck_combat', 'transicao': 'phase_shift',
}
SORTEAVEIS_FASE2 = ('passear', 'laser', 'luz')   # 'passear' = só continua a ronda por um instante

# Um quadro por clip (ordem do manifesto). Vermelho só nos ataques dele (feixes).
CLIPS = {
    'azul': Clip(1000, (0,)), 'vermelho': Clip(1000, (1,)),
    'azul_destruido': Clip(1000, (2,)), 'vermelho_destruido': Clip(1000, (3,)),
}


@dataclass(frozen=True)
class FeixeConfig:
    dps: float
    duracao_ms: int
    suavizacao: float       # 0..1: quanto a ponta anda até o jogador a cada passo (1 = colada nele)
    largura: int
    cor: Tuple[int, int, int]
    shake: float

    def __post_init__(self):
        if not (self.dps > 0 and self.duracao_ms > 0 and self.largura > 0):
            raise ValueError(f'FeixeConfig: dps, duracao_ms e largura precisam ser > 0 ({self!r})')
        if not 0 < self.suavizacao <= 1:
            raise ValueError(f'FeixeConfig: suavizacao precisa estar em (0, 1] (veio {self.suavizacao!r})')


@dataclass(frozen=True)
class GuiltyConfig:
    # --- atributos ---
    vida: float = 2000
    dano_contato: float = 80
    velocidade: float = 130             # fase 1; a fase 2 dobra (FASES)
    mult_sem_barreira: float = 1.9      # fase 1 sem o escudo: mais rápido
    raio_colisao_mapa: int = 45

    # --- barreira do Monitor ---
    barreira_raio: int = 110
    barreira_dano: float = 15           # de contato, a cada 400 ms
    barreira_cor: Tuple[int, int, int] = (0, 150, 255)
    barreira_empurrao_max: float = 24   # px por passo: não atravessa o jogador por uma parede
    sentinelas_para_cair: int = 40      # fase 1: sentinelas derrotadas até a barreira cair
    luz_dano_no_guilty: float = 0.05    # fase 2: fração da vida máxima por artilharia que o acerta
    raio_corpo: float = 40              # folga do acerto da luz nele (o corpo, não só o centro)

    # --- ronda: caminhos que passam perto do jogador ---
    ronda_desvio: float = 170           # a que distância do jogador o caminho passa, no máximo
    ronda_alem: Tuple[float, float] = (300, 650)      # quanto segue depois de passar por ele
    ronda_max_ms: int = 9000
    ronda_chegou: float = 40
    ronda_tentativas: int = 12
    travado_ms: int = 350               # sem sair do lugar por este tempo (parede): sorteia outro caminho
    flutuacao_px: float = 5
    flutuacao_ms: int = 2200

    # --- cooldowns das rotinas (min, max) em ms, sorteados no fim da habilidade ---
    cooldown: Dict[str, Tuple[int, int]] = field(default_factory=lambda: {
        'proximidade': (1200, 1200), 'laser': (7000, 11000)})
    # contado do começo da fase em que a habilidade existe
    cooldown_inicial: Dict[str, int] = field(default_factory=lambda: {'proximidade': 800, 'laser': 5000})

    # --- invocações: correm por fora das rotinas (min, max entre uma e outra, em ms) ---
    intervalo: Dict[str, Tuple[int, int]] = field(default_factory=lambda: {
        'chuva': (900, 1500), 'armadilha': (8000, 12000),                                   # fase 1
        'luz': (4500, 6500), 'chuva_super': (13000, 18000), 'infestacao': (14000, 20000)})  # fase 2
    intervalo_inicial: Dict[str, int] = field(default_factory=lambda: {
        'chuva': 1200, 'armadilha': 7000, 'luz': 3000, 'chuva_super': 6000, 'infestacao': 10000})

    # --- feixes ---
    proximidade_dist: float = 215       # do centro dele (a barreira acaba em 125)
    # 250 de dano se o jogador tomar os 500 ms inteiros
    proximidade: FeixeConfig = FeixeConfig(dps=500, duracao_ms=500, suavizacao=0.6, largura=32,
                                           cor=(255, 15, 15), shake=12)
    laser_carga_ms: int = 1000
    laser_shake_carga: float = 2
    laser: FeixeConfig = FeixeConfig(dps=200, duracao_ms=4000, suavizacao=0.1, largura=25,
                                     cor=(255, 30, 25), shake=5)
    laser_fase3: FeixeConfig = FeixeConfig(dps=320, duracao_ms=2000, suavizacao=0.18, largura=30,
                                           cor=(255, 0, 0), shake=7)

    # --- fase 1: chuva de sentinelas ---
    chuva_raio: Tuple[float, float] = (0, 900)        # distância do jogador
    chuva_max_vivas: int = 18           # acima disso a chuva espera
    shake_chuva: float = 2

    # --- fase 1: armadilha forerunner ---
    armadilha_dist_inicio: float = 1000   # nascem fora da tela
    armadilha_dist: float = 330         # de cada esfera ao jogador, na linha
    armadilha_velocidade: float = 950
    armadilha_tolerancia: float = 12    # px: chegou à ponta da linha
    armadilha_busca_max_ms: int = 4000  # não fechou a linha: para onde está e dispara
    armadilha_parada_ms: int = 320      # o "brevíssimo período": a chance de sair da linha
    armadilha_azul_ms: int = 120        # no fim da parada, a que vai disparar fica azul
    armadilha_disparo_ms: int = 450
    armadilha_saida_ms: int = 350
    armadilha_feixe_suavizacao: float = 0.45
    armadilha_feixe_largura: int = 14
    armadilha_alcance: float = 38       # distância do feixe que acerta o jogador
    armadilha_dano: float = 160         # uma única vez
    armadilha_queimadura_dps: float = 18
    armadilha_queimadura_ms: int = 4000
    shake_armadilha: float = 10         # cai até zero ao longo do disparo
    armadilha_cor: Tuple[int, int, int] = (40, 170, 255)

    # --- fase 2: decisão (andar pesa bem mais que atacar) ---
    pesos_fase2: Dict[str, float] = field(default_factory=lambda: {'passear': 6, 'laser': 1.5, 'luz': 2.5})
    passear_ms: Tuple[int, int] = (900, 1600)

    # --- fase 2: chuva de super sentinelas (triângulo equilátero em volta do jogador) ---
    super_dist: float = 430
    super_max_vivas: int = 6
    shake_super: float = 5

    # --- fase 2: infestação ---
    flood_tela: Tuple[float, float] = (560, 300)      # até onde, em x e y, do jogador (a tela dele)
    flood_quantidade: int = 5
    flood_max_vivos: int = 15
    flood_lentidao: float = 0.5
    flood_lentidao_ms: int = 3000
    flood_poeira: int = 240
    shake_flood: float = 9

    # --- fase 2: luz visível ---
    luz_presets: Tuple[str, ...] = ('guilty_luz_1', 'guilty_luz_2', 'guilty_luz_3', 'guilty_luz_4')
    luz_raio_antes_ms: int = 80         # o feixe cai do céu este tanto antes de a artilharia estourar
    luz_raio_ms: int = 320              # quanto o feixe dura
    shake_luz: Tuple[float, ...] = (4, 5, 6, 8)

    # --- fase 3: teleporte ---
    tp_raio: Tuple[float, float] = (420, 640)         # em volta do jogador
    tp_tentativas: int = 30
    tp_fade_ms: int = 220               # some (e depois aparece) neste tempo
    tp_pausa_ms: int = 500              # parado entre o teleporte e o laser
    fase3_respiro_ms: int = 500         # depois do laser, antes do próximo teleporte

    # --- vfx ---
    brilho_cor: Tuple[int, int, int] = (40, 150, 255)
    brilho_raio: int = 120
    brilho_periodo_ms: int = 1800
    shake_barreira: float = 6

    # --- anti-stuck: teleporta para perto do jogador ---
    antistuck: ConfigTravamento = ConfigTravamento(janela_ms=3500, caminho_min=40, dist_min=600)

    def __post_init__(self):
        if set(self.cooldown) != set(self.cooldown_inicial):
            raise ValueError('GuiltyConfig: cooldown e cooldown_inicial precisam ter as mesmas habilidades')
        if set(self.intervalo) != set(self.intervalo_inicial):
            raise ValueError('GuiltyConfig: intervalo e intervalo_inicial precisam ter as mesmas invocações')
        for nome, (minimo, maximo) in self.intervalo.items():
            if not 0 < minimo <= maximo:
                raise ValueError(f'GuiltyConfig: intervalo de "{nome}" ({minimo}, {maximo}) inválido')
        if set(self.pesos_fase2) != set(SORTEAVEIS_FASE2) or not all(p > 0 for p in self.pesos_fase2.values()):
            raise ValueError(f'GuiltyConfig: pesos_fase2 inválidos: {self.pesos_fase2!r}')
        if self.pesos_fase2['passear'] <= max(p for n, p in self.pesos_fase2.items() if n != 'passear'):
            raise ValueError('GuiltyConfig: na fase 2, passear precisa pesar mais que cada ataque')
        if len(self.shake_luz) != len(self.luz_presets):
            raise ValueError('GuiltyConfig: shake_luz e luz_presets precisam ter o mesmo tamanho')
        if not self.proximidade_dist > self.barreira_raio:
            raise ValueError('GuiltyConfig: proximidade_dist precisa passar da barreira')
        if not 0 < self.luz_dano_no_guilty < 1 or self.sentinelas_para_cair <= 0:
            raise ValueError('GuiltyConfig: luz_dano_no_guilty em (0, 1) e sentinelas_para_cair > 0')


CFG = GuiltyConfig()
