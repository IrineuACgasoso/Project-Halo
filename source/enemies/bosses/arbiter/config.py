"""Todos os números do Arbiter num lugar só (balanceamento sem caçar valor no código).

Danos e áreas dos golpes ficam nos presets `arbiter_*` das skills (`feats/skills/*/config.py`)."""
import math
from dataclasses import dataclass, field
from typing import Dict, Tuple

from source.enemies.base.boss import Clip, ConfigTravamento, FaseBoss, Habilidade


@dataclass(frozen=True)
class FaseArbiter(FaseBoss):
    # nome, limiar_vida, mult_cooldown e mult_velocidade vêm de FaseBoss (nesta ordem)
    carabina: bool              # fase 2: descarta a carabina (rajada e spray)
    invoca: bool                # fase 2: não chama mais Elites
    lamina_golpes: int          # combo da espada de energia de perto
    granadas: int               # granadas por arremesso
    mult_recuo: float           # pesa a vontade de recuar sem escudo (fase 2: recua menos)


FASES = (
    FaseArbiter('Comandante',       1.00, 1.00, 1.00, True,  True,  2, 2, 1.0),
    FaseArbiter('Espada e Honra',   0.40, 0.75, 1.20, False, False, 3, 3, 0.5),
)

# nome da habilidade -> `estado_habilidade`
ESTADOS = {
    'carabina': 'shooting', 'granada': 'grenade', 'lamina': 'blade',
    'investida': 'prophets_bane', 'salto': 'leap_strike', 'emboscada': 'stealth',
    'esquiva': 'evade', 'combo': 'shield_combo',
    'antistuck': 'antistuck_combat', 'transicao': 'phase_shift',
}

# Animação: um ciclo só (4 quadros); os clips só mudam o ritmo, sem reiniciar o passo.
CLIPS = {
    'andar': Clip(200),
    'parado': Clip(300),        # mirando, golpeando, atordoado
    'investida': Clip(60),      # dashes
    'furtivo': Clip(100),       # sprint camuflado
    'reaparecer': Clip(80),     # fim da camuflagem (fade-in)
    'grito': Clip(70),          # pose do grito Sangheili (o corpo treme)
}


@dataclass(frozen=True)
class ArbiterConfig:
    # --- atributos ---
    vida: float = 2500
    dano_contato: float = 80
    velocidade: float = 90
    # Escudo de energia (escala com a vida): volta sozinho depois de um tempo sem tomar dano
    escudo: float = 600
    escudo_atraso_ms: int = 3500         # sem tomar dano por isto...
    escudo_regen_ms: int = 2500          # ...e enche de zero ao máximo neste tempo

    # --- a quem as habilidades "pertencem" (define quem leva o dano) ---
    dono_skills: str = 'BOSS'
    dono_projetil: str = 'INIMIGO'

    # --- cooldowns (min, max) em ms; sorteados e multiplicados por FaseArbiter.mult_cooldown ---
    cooldown: Dict[str, Tuple[int, int]] = field(default_factory=lambda: {
        'carabina':   (4000, 6500),
        'granada':    (6500, 9500),
        'lamina':     (4500, 7000),
        'investida':  (6000, 9000),
        'salto':      (5500, 8500),
        'emboscada':  (13000, 17000),
        'esquiva':    (6000, 9000),
        'combo':      (12000, 15000),
    })
    cooldown_inicial: Dict[str, int] = field(default_factory=lambda: {
        'carabina': 2500, 'granada': 4500, 'lamina': 3000, 'investida': 4000, 'salto': 5000,
        'emboscada': 10000, 'esquiva': 3000, 'combo': 0,
    })
    # fora da rotina (ordens dadas sem parar): (min, max) e o primeiro uso, como acima
    cooldown_fora: Dict[str, Tuple[int, int]] = field(default_factory=lambda: {
        'bombardeio': (15000, 21000), 'invocacao': (16000, 22000)})
    cooldown_fora_inicial: Dict[str, int] = field(default_factory=lambda: {'bombardeio': 12000, 'invocacao': 9000})

    # --- movimento / postura ---
    dist_min: float = 260                # neutro: abaixo disso ele recua...
    dist_max: float = 480                # ...e acima disso avança
    aproximacao_jogador_fraco: float = 160   # a faixa chega até tanto mais perto com o jogador sem vida
    dist_recuo: float = 720              # recuando: até esta distância (depois circula)
    strafe_troca_ms: Tuple[int, int] = (1200, 2600)
    # Sem escudo, as vontades brigam (nota de recuo = vida dele + jogador longe + escolta - jogador fraco):
    peso_vida_propria: float = 1.0       # vida dele baixa -> recua para o escudo voltar
    peso_distancia: float = 0.6          # jogador se afastou -> recua também
    dist_afastou: Tuple[float, float] = (300, 650)   # 0 em 300 px, cheio em 650 px
    peso_escolta: float = 0.6            # Elites vivos cobrem o recuo -> recua bem mais...
    escolta_cheia: int = 2               # ...cheio a partir de tantos Elites
    peso_vida_jogador: float = 1.1       # jogador com pouca vida -> ignora o recuo e avança
    limiar_recuo: float = 0.55           # nota >= isto: recua
    limiar_avanco: float = 0.25          # nota <= isto: avança (entre os dois, mantém a postura)
    # quanto cada postura puxa cada golpe (nota da IA)
    mult_postura: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        'avanco': {'carabina': 0.5, 'granada': 0.7, 'lamina': 1.5, 'investida': 1.7, 'salto': 1.5, 'emboscada': 1.2},
        'recuo':  {'carabina': 1.5, 'granada': 1.5, 'lamina': 0.6, 'investida': 0.3, 'salto': 0.3, 'emboscada': 0.4},
    })
    agressividade_melee: float = 0.8     # golpes de perto valem até +80% com o jogador sem vida
    # Recuo: rumo com chão que mais se afasta do jogador (leque em volta do "para trás"), puxado para a escolta
    recuo_mult_vel: float = 1.3
    recuo_leque: Tuple[float, ...] = (0, 35, -35, 70, -70, 105, -105)   # graus a partir do "para trás"
    recuo_sonda: float = 140             # px: o rumo precisa de chão até aqui
    recuo_rumo_ms: int = 350             # recalcula o rumo a cada tanto
    recuo_puxa_escolta: float = 0.5      # quanto a direção da escolta pesa no rumo
    recuo_esquiva_graus: float = 40      # sem escudo e recuando, a esquiva sai na diagonal para trás

    # --- revelar-se (clarão) enquanto está camuflado ---
    revelar_tiro_ms: int = 80
    revelar_tiro_alpha: int = 90

    # --- Carabina (rajada de precisão com strafe) ---
    carabina_tiros: int = 6
    carabina_mira: int = 280
    carabina_intervalo: int = 85
    carabina_dano: int = 15
    carabina_vel_proj: int = 560
    carabina_tamanho: int = 40           # px (o Elite usa 32)
    carabina_spread: float = 0.03
    carabina_antecipacao: float = 0.55
    carabina_rastreio: float = 0.15      # 0..1: quanto a rajada "puxa" pro jogador a cada tiro
    carabina_strafe: float = 0.85
    carabina_recuperacao: int = 350

    # --- Espada de energia de perto (ConeStrike azul) ---
    lamina_preset: str = 'arbiter_energy_sword'
    lamina_combo_mult: float = 0.82      # cada golpe seguinte do combo telegrafa mais rápido
    lamina_flash: int = 150
    lamina_avanco_ms: int = 150
    lamina_avanco_mult: float = 6.5
    lamina_pausa: int = 60
    lamina_recuperacao: int = 500

    # --- Granada de plasma ---
    granada_preset: str = 'arbiter_plasma_grenade'
    granada_preparo: int = 500
    granada_intervalo: int = 360
    granada_recuperacao: int = 550
    granada_dist_min: float = 150
    granada_dist_max: float = 700
    granada_vel: float = 700
    granada_antecipacao: float = 0.8
    granada_offset_lateral: float = 170

    # --- Investida em cone (Prophet's Bane) ---
    investida_preparo_ms: int = 280      # saca a espada (parado): o aviso
    investida_dash: str = 'arbiter_investida'
    investida_cone: str = 'arbiter_investida'
    investida_para_antes: float = 70     # para tanto antes de onde o jogador estava
    investida_cone_min_ms: int = 320     # o cone nunca carrega mais rápido que isto
    investida_cone_folga_ms: int = 60    # estoura um instante depois de ele chegar
    investida_stun_ms: int = 1300        # atordoado depois do golpe...
    costas_graus: float = 65             # ...com as costas (meia-abertura em volta de -direção) expostas
    costas_mult: float = 2.0             # dano pelas costas enquanto atordoado

    # --- Salto curto com investida frontal (também o anti-stuck) ---
    salto_preparo_ms: int = 220
    salto_preset: str = 'arbiter_investida'
    salto_golpe: str = 'arbiter_investida_frontal'
    salto_recuperacao_ms: int = 450

    # --- Golpe fantasma (emboscada camuflada) ---
    emboscada_preset: str = 'arbiter_furtivo'
    emboscada_mult_vel: float = 4.0
    emboscada_dist: float = 205          # dist. p/ cortar o sprint e dar o golpe de espada
    flanco_raio: Tuple[float, float] = (420, 600)
    flanco_angulo: Tuple[float, float] = (100, 160)   # graus a partir da direção jogador -> Arbiter
    flanco_tentativas: int = 30

    # --- Esquiva tática (+ spray camuflado) ---
    esquiva_limiar: float = 0.10         # dano recente >= esta fração de (vida + escudo) máximos
    esquiva_memoria_ms: float = 1500     # constante de tempo do "dano recente"
    esquiva_dash: str = 'arbiter_esquiva'
    esquiva_dist_teste: float = 260      # lado da esquiva: o que tem chão a tanto
    esquiva_spray_chance: float = 0.45
    esquiva_preset: str = 'arbiter_esquiva'
    spray_tiros: int = 14
    spray_intervalo: int = 45
    spray_dano: int = 15
    spray_spread: float = 0.1
    spray_saida_ms: int = 350            # ainda invisível depois do spray

    # --- Combo da quebra de escudo ---
    grito_ms: int = 750
    combo_dashes: int = 5
    combo_dash: str = 'arbiter_combo'
    combo_tipos: Tuple[str, ...] = ('cruz', 'artilharia', 'reverso', 'frontal')
    combo_preparo_ms: Tuple[int, int] = (220, 320)   # parado, encarando, antes de cada dash
    combo_pausa_ms: Tuple[int, int] = (120, 220)     # depois que o golpe do dash estoura
    combo_cruz_no_caminho: float = 0.5   # a cruz sai quando ele passa por esta fração do caminho
    combo_corte: str = 'arbiter_combo_corte'
    combo_artilharia: str = 'arbiter_combo_artilharia'
    combo_reverso: str = 'arbiter_investida'          # cone da investida, para trás
    combo_frontal: str = 'arbiter_investida_frontal'  # corte do salto, para a frente
    combo_recuperacao_ms: int = 500
    furia_buff: float = 0.45             # Fúria Honorável: +45% de velocidade do grito até...
    furia_ms: int = 2500                 # ...tanto depois do fim do combo

    # --- Fora da rotina ---
    bombardeio_preset: str = 'arbiter_phantom'
    elites_por_invocacao: int = 2
    max_elites: int = 4
    spawn_raio: Tuple[int, int] = (60, 120)
    spawn_tentativas: int = 14

    # --- Anti-stuck: caminho < 40 px em 1,5 s (livre) e longe do jogador -> salto com golpe ---
    antistuck: ConfigTravamento = ConfigTravamento(janela_ms=1500, caminho_min=40, dist_min=200)
    antistuck_salto: str = 'arbiter_antistuck'

    # --- transição (fase 2): grito + onda + escudo cheio ---
    transicao_cone: str = 'arbiter_nova'

    # --- leitura do jogador (multiplicam a nota em `pontuar_*`) ---
    parado_ms: float = 800               # parado há mais que isto: granada nele
    bonus_parado: float = 1.4
    fuga_vel: float = 90                 # fugindo mais rápido que isto (px/s)
    bonus_fuga: float = 1.3

    # --- vfx ---
    cor_energia: Tuple[int, int, int] = (60, 170, 255)
    cor_costas: Tuple[int, int, int] = (255, 210, 70)
    brilho_alpha: Tuple[int, int] = (35, 120)
    brilho_periodo_ms: int = 320
    aura_alpha: Tuple[int, int] = (25, 80)
    aura_periodo_ms: int = 900
    aura_particulas_ms: int = 90
    faiscas_grito: int = 40
    shake_grito: float = 6
    shake_golpe: float = 3
    recarga_alpha: Tuple[int, int] = (40, 140)   # escudo voltando: o corpo pisca em azul
    recarga_periodo_ms: int = 260
    recarga_faiscas: int = 18
    escudo_cheio_ms: int = 350           # clarão quando o escudo termina de encher

    def __post_init__(self):
        if (set(self.cooldown) != set(self.cooldown_inicial)
                or set(self.cooldown_fora) != set(self.cooldown_fora_inicial)):
            raise ValueError('ArbiterConfig: cada cooldown precisa do seu primeiro uso (e vice-versa)')
        if not self.limiar_avanco < self.limiar_recuo:
            raise ValueError('ArbiterConfig: limiar_avanco precisa ser menor que limiar_recuo')
        if len(self.combo_tipos) < 2 or not set(self.combo_tipos) <= {'cruz', 'artilharia', 'reverso', 'frontal'}:
            raise ValueError(f'ArbiterConfig: combo_tipos desconhecidos: {self.combo_tipos!r}')

    @property
    def cos_costas(self):
        return math.cos(math.radians(self.costas_graus))


CFG = ArbiterConfig()
COS_COSTAS = CFG.cos_costas

# Decisão (F3): notas da IA de utilidade. A lâmina usa o raio do cone (`pontuar_lamina`).
# Esquiva e combo são reações (`pensar`); bombardeio e invocação correm fora da rotina (`perceber`).
HABILIDADES = {
    'lamina':    Habilidade(peso=1.0),
    'investida': Habilidade(peso=0.9, alcance=(120, 560), ideal=(180, 420)),
    'salto':     Habilidade(peso=0.8, alcance=(200, 620), ideal=(260, 480)),
    'granada':   Habilidade(peso=0.7, alcance=(CFG.granada_dist_min, CFG.granada_dist_max), ideal=(280, 600)),
    'carabina':  Habilidade(peso=0.7, alcance=(150, 900), ideal=(300, 650)),
    'emboscada': Habilidade(peso=0.8, alcance=(420, math.inf), ideal=(550, 1000)),
}
