"""Todos os números do Scarab num lugar só (balanceamento sem caçar valor no código).

Danos, raios, cores e knockback das artilharias ficam nos presets `scarab_*` de
`feats/skills/artilharia/config.py`.

Pontos da arte: pixels do sprite de 1024×1024 olhando para a ESQUERDA (espelhados quando ele vira)."""
import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Dict, Tuple

from source.enemies.base.boss import Clip, FaseBoss

# nome, vida em que começa, mult. de cooldown das armas, mult. de velocidade
FASES = (
    FaseBoss('Blindado', 1.00, 1.0, 1.0),
    FaseBoss('Avariado', 0.60, 0.85, 1.15),
    FaseBoss('Sobrecarga Crítica', 0.30, 0.6, 1.45),
)
FASE_CRITICA = 3
VARIANTES = ('default', 'damaged', 'broken')     # a arte de cada fase

# nome da habilidade -> `estado_habilidade`. As armas (feixe, torreta, desembarque) não são rotinas.
ESTADOS = {'stomp': 'body_stomp', 'sismica': 'pisada_sismica', 'queda': 'queda', 'morte': 'colapso',
           'transicao': 'phase_shift'}

CLIPS = {'padrao': Clip(1000, (0,))}             # o corpo é desenhado em camadas (corpo.py)

TAMANHO = 1024                                   # lado da arte (e do rect)

# ── Pontos da arte ───────────────────────────────────────────────────────────
PES = MappingProxyType({'frente': (108, 722), 'centro': (606, 860), 'tras': (885, 728), 'oculta': (412, 672)})
PATAS_VULNERAVEIS = ('frente', 'centro', 'tras')  # as que aparecem inteiras na arte
CENTRO_CHAO = (512, 640)                          # o meio da sombra dele, entre as patas
NUCLEO = (751, 553)                               # na pose caída
PIVO_TORRETA = 545                                # x em volta do qual o canhão gira para o outro lado
PONTA_CANHAO = (745, 157)                         # com o cano apontado para a direita
TORRETA_SENTADO_DY = 172                          # quanto o canhão desce na pose sentada
ESCOTILHAS = ((300, 600), (620, 620))             # de onde a guarnição desce
CASCO = (200, 240, 660, 560)                      # (x0, y0, x1, y1) para fumaça, arcos e explosões


@dataclass(frozen=True)
class FeixeConfig:
    dps: float = 320
    raio_impacto: float = 55            # em volta da ponta
    suavizacao: float = 0.08            # 0..1: quanto a ponta anda até o jogador a cada passo
    suavizacao_critica: float = 0.10    # varre mais rápido (ainda dá para fugir correndo)
    largura: float = 34
    carga_ms: int = 2400
    duracao_ms: int = 5000
    cooldown_ms: Tuple[int, int] = (9000, 12000)
    alcance: float = 1500               # só começa com o jogador até esta distância
    cor: Tuple[int, int, int] = (60, 255, 90)
    shake_carga: float = 4
    shake: float = 22

    def __post_init__(self):
        if not all(v > 0 for v in (self.dps, self.raio_impacto, self.largura, self.carga_ms, self.duracao_ms)):
            raise ValueError(f'FeixeConfig: dps, raio_impacto, largura, carga e duração precisam ser > 0 ({self!r})')
        if not 0 < self.suavizacao <= self.suavizacao_critica <= 1:
            raise ValueError('FeixeConfig: 0 < suavizacao <= suavizacao_critica <= 1')


@dataclass(frozen=True)
class ScarabConfig:
    # --- atributos ---
    vida: float = 2800
    velocidade: float = 62
    raio_aura: float = 260              # círculo para as auras do jogador (MK2)

    # --- patas: cada uma tem a própria vida (escala com a dele) ---
    vida_pata: float = 300
    pata_danificada: float = 0.5        # abaixo desta fração ela já aparece danificada
    # meia-abertura (graus) do ângulo que evidencia cada pata, em volta da direção do pé
    angulo_pata: Dict[str, float] = field(default_factory=lambda: {'frente': 38, 'centro': 26, 'tras': 26})
    carapaca_passa: float = 0.04        # fora dos ângulos, só esta fração chega à vida dele

    # --- queda: núcleo exposto ---
    queda_ms: int = 350                 # desabando (o núcleo ainda não abriu)
    exposto_ms: int = 7000
    erguer_ms: int = 1100
    nucleo_mult: float = 4              # dano de quem está atrás, no ângulo do núcleo
    nucleo_fora_mult: float = 1         # caído, mas fora do ângulo
    nucleo_graus: float = 75            # meia-abertura, em volta do eixo das costas
    rearme_ms: int = 2500               # depois de se erguer, as armas esperam ao menos isto

    # --- andar ---
    raio_sob: float = 320               # dentro disto (do centro do chão) o jogador está "por baixo"
    passo_ms: Tuple[int, int, int] = (700, 620, 480)      # quanto a pata fica no ar, por fase (= o aviso)
    apoio_ms: Tuple[int, int, int] = (700, 560, 380)      # com as 4 no chão, entre um passo e outro
    mult_no_ar: float = 1.6             # o corpo avança quando a pata está no ar...
    mult_apoio: float = 0.35            # ...e quase para com as 4 no chão
    dist_longe: float = 1100            # além disso ele se apressa
    mult_longe: float = 2.2
    margem_mapa: float = 320            # não chega mais perto da borda do mapa
    atraso_virar_ms: int = 1500         # como o Hunter: mudar de lado não reinicia

    # --- decisão ---
    # cooldowns (min, max) em ms, sorteados no fim da habilidade
    cooldown: Dict[str, Tuple[int, int]] = field(default_factory=lambda: {
        'stomp': (5000, 7500), 'sismica': (4000, 6000)})
    cooldown_inicial: Dict[str, int] = field(default_factory=lambda: {'stomp': 2500, 'sismica': 3000})
    pesos: Dict[str, float] = field(default_factory=lambda: {'stomp': 10, 'sismica': 6, 'esperar': 2})
    esperar_ms: Tuple[int, int] = (250, 600)

    # --- body stomp ---
    stomp_sobe_px: float = 26           # o corpo toma impulso durante o aviso
    sentado_ms: int = 950
    stomp_pausa_ms: int = 900

    # --- pisada sísmica ---
    acampar_raio: float = 180           # colado numa pata
    acampar_ms: int = 2200              # por este tempo, sem sair
    sismica_velocidade: float = 330     # da artilharia atrás do jogador
    sismica_trava_ms: int = 250         # nos últimos instantes ela para onde está
    sismica_alcance: float = 420        # até onde ela vai, a partir do pé
    sismica_ergue_px: float = 46        # além da arte com a pata erguida
    sismica_pausa_ms: int = 600

    # --- armas autônomas ---
    feixe: FeixeConfig = FeixeConfig()
    # torreta de plasma (dois canhões laterais): igual à de antes
    torreta_cooldown_ms: Tuple[int, int] = (4000, 8000)
    torreta_tiros: int = 6
    torreta_intervalo_ms: int = 250
    torreta_dano: int = 20
    torreta_velocidade: float = 750
    torreta_tamanho: Tuple[int, int] = (96, 16)
    torreta_canhoes: Tuple[Tuple[int, int], ...] = ((160, -40), (-160, -40))
    torreta_mult_critica: float = 0.5   # o dobro da cadência
    torreta_alcance: float = 1500
    # desembarque de guarnição
    desembarque_ms: Tuple[int, int] = (13000, 18000)
    desembarque_inicial_ms: int = 9000
    desembarque_aviso_ms: int = 1000    # a escotilha abrindo
    desembarque_qtd: Tuple[int, int] = (3, 5)
    desembarque_max_vivos: int = 12
    desembarque_pesos: Dict[str, float] = field(default_factory=lambda: {
        'grunt_blue': 35, 'grunt_red': 30, 'jackal': 25, 'elite': 10})
    desembarque_life_orb: float = 18    # chance (%) de orbe de vida de cada um

    # --- câmera ---
    zoom: float = 0.5625                # mostra 2276×1280 do mundo
    zoom_entrada_ms: int = 2600
    zoom_saida_ms: int = 2000

    # --- tremores (px do mundo, ms; com o zoom, na tela saem pela metade) ---
    shake_passo: Tuple[float, int] = (6, 220)
    shake_sismica: Tuple[float, int] = (30, 500)
    shake_stomp: Tuple[float, int] = (56, 900)
    shake_queda: Tuple[float, int] = (34, 600)
    shake_detonacao: Tuple[float, int] = (64, 1100)

    # --- partículas ---
    terra_passo: int = 16
    terra_sismica: int = 70
    terra_stomp: int = 320
    terra_queda: int = 140

    # --- colapso final (a duração é a do preset scarab_detonacao) ---
    explosao_intervalo_ms: int = 105

    def __post_init__(self):
        if set(self.cooldown) != set(self.cooldown_inicial) or set(self.pesos) != {*self.cooldown, 'esperar'}:
            raise ValueError('ScarabConfig: cooldown, cooldown_inicial e pesos precisam ter as mesmas habilidades')
        if set(self.angulo_pata) != set(PATAS_VULNERAVEIS):
            raise ValueError(f'ScarabConfig: angulo_pata precisa ter exatamente {PATAS_VULNERAVEIS}')
        if not all(0 < a < 90 for a in (*self.angulo_pata.values(), self.nucleo_graus)):
            raise ValueError('ScarabConfig: ângulos precisam estar entre 0 e 90 graus')
        if not 0 <= self.carapaca_passa < 1 or not 0 < self.pata_danificada < 1:
            raise ValueError('ScarabConfig: carapaca_passa em [0, 1) e pata_danificada em (0, 1)')
        if not (len(self.passo_ms) == len(self.apoio_ms) == len(FASES)) or min(*self.passo_ms, *self.apoio_ms) <= 0:
            raise ValueError('ScarabConfig: passo_ms e apoio_ms precisam de um valor > 0 por fase')
        if not self.nucleo_mult > self.nucleo_fora_mult > self.carapaca_passa:
            raise ValueError('ScarabConfig: nucleo_mult > nucleo_fora_mult > carapaca_passa')
        if not 0 < self.zoom <= 1:
            raise ValueError('ScarabConfig: zoom precisa estar em (0, 1]')
        if self.vida <= 0 or self.vida_pata <= 0:
            raise ValueError('ScarabConfig: vida e vida_pata precisam ser > 0')


CFG = ScarabConfig()

# ── Ângulos (calculados uma vez; `no_cone` só multiplica) ────────────────────
def _eixo(ponto):
    dx, dy = ponto[0] - CENTRO_CHAO[0], ponto[1] - CENTRO_CHAO[1]
    tamanho = math.hypot(dx, dy)
    return dx / tamanho, dy / tamanho


EIXO_PATA = MappingProxyType({nome: _eixo(PES[nome]) for nome in PATAS_VULNERAVEIS})
COS_PATA = MappingProxyType({nome: math.cos(math.radians(CFG.angulo_pata[nome])) for nome in PATAS_VULNERAVEIS})
EIXO_NUCLEO = (1.0, 0.0)                         # olhando para a esquerda, as costas são a direita
COS_NUCLEO = math.cos(math.radians(CFG.nucleo_graus))
