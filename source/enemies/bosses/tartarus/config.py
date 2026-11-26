"""Todos os números do Tartarus num lugar só (balanceamento sem caçar valor no código).

Danos, áreas, knockback e lentidão dos golpes ficam nos presets `tartarus_*` das skills
(`feats/skills/*/config.py`): artilharia, rect_strike, dash, salto e purge_grid."""
import math
from dataclasses import dataclass, field
from typing import Dict, Tuple

from source.enemies.base.boss import Clip, ConfigTravamento, FaseBoss, Habilidade


@dataclass(frozen=True)
class FaseTartarus(FaseBoss):
    # nome, limiar_vida, mult_cooldown e mult_velocidade vêm de FaseBoss (nesta ordem)
    furia: bool                 # Fúria Jiralhanae: Punho de Rukt, Hammer Run e Brutes


FASES = (
    FaseTartarus('Chefe dos Jiralhanae', 1.00, 1.00, 1.00, False),
    FaseTartarus('Fúria Jiralhanae',     0.35, 0.80, 1.15, True),
)

# nome da habilidade -> `estado_habilidade`
ESTADOS = {
    'vortice': 'gravity_pull', 'onda': 'seismic_shockwave', 'salto': 'brute_leap',
    'rampage': 'chieftain_rampage', 'punho': 'fist_of_rukt', 'corrida': 'hammer_run',
    'antistuck': 'antistuck_combat', 'transicao': 'phase_shift',
}

# Animação: o sprite tem um ciclo só (4 quadros); os clips mudam o ritmo.
CLIPS = {
    'andar': Clip(220),
    'parado': Clip(380),        # preparando, golpeando
    'corrida': Clip(90),        # rampage e hammer run
    'grito': Clip(70),          # rugido (o corpo treme)
    'ofegante': Clip(650),      # exausto depois do rampage esquivado / pouso do meteoro
}


@dataclass(frozen=True)
class TartarusConfig:
    # --- atributos ---
    vida: float = 4000
    dano_contato: float = 60
    velocidade: float = 120
    hitbox_fracao: Tuple[float, float] = (1 / 2.4, 1 / 1.6)   # (largura, altura) do sprite

    # --- Ativação do Halo: a luta acaba quando o cronômetro zera ---
    halo_ms: int = 180000

    # --- Barreira do Punho de Rukt ---
    barreira_reducao: float = 0.90       # dano recebido com a barreira ativa: -90%
    sobrecarga_ms: int = 3000            # errou um golpe pesado do martelo: a barreira cai por isto
    meta_esquivas: int = 5               # golpes esquivados que enchem a barra do HUD...
    quebra_ms: int = 9000                # ...e derrubam a barreira por isto (e disparam o Rampage)

    # --- dono das skills (quem leva o crédito do dano) ---
    dono_skills: str = 'BOSS'

    # --- cooldowns (min, max) em ms; sorteados e multiplicados por FaseTartarus.mult_cooldown ---
    cooldown: Dict[str, Tuple[int, int]] = field(default_factory=lambda: {
        'vortice':  (6000, 8500),
        'onda':     (4500, 6500),
        'salto':    (5000, 7000),
        'rampage':  (1000, 1000),        # reação à quebra da barreira (o gatilho é a barra)
        'punho':    (14000, 18000),
        'corrida':  (8000, 11000),
    })
    cooldown_inicial: Dict[str, int] = field(default_factory=lambda: {
        'vortice': 2500, 'onda': 1500, 'salto': 3000, 'rampage': 0, 'punho': 1500, 'corrida': 4000,
    })
    descanso_ms: Tuple[int, int] = (250, 450)   # exaustão entre golpes: extremamente ofensivo

    # --- movimento: nunca recua; avança em linha reta ---
    perto_px: float = 70                 # colado: para de empurrar (o contato fere sozinho)

    # --- Vórtice Gravitacional (perto) ---
    vortice_preparo_ms: int = 300        # ergue o martelo
    vortice_ms: int = 1500               # a aura que puxa
    vortice_raio: int = 420              # raio da aura roxa
    vortice_alcance: float = 330         # só usa com o jogador dentro disto (certeza de alcance)
    vortice_lentidao: float = 0.65       # lentidão alta enquanto está na aura...
    vortice_lentidao_ms: int = 350       # ...renovada a cada 100 ms (sai e dura só isto)
    vortice_puxao: float = 110           # px/s: fraco de propósito, sem vencer a corrida do jogador
    vortice_puxao_min: float = 90        # px: não puxa para dentro do corpo
    vortice_artilharia: str = 'tartarus_vortice'
    vortice_particulas_ms: int = 60
    vortice_particulas: int = 9
    vortice_shake: Tuple[float, int] = (6, 1500)
    vortice_recuperacao_ms: int = 450

    # --- Esmagamento Sísmico em Linha (média) ---
    onda_preparo_ms: int = 350
    onda_preset: str = 'tartarus_onda'
    onda_antecipacao: float = 0.35       # mira um pouco à frente de quem foge
    onda_poeira: int = 110
    onda_shake: Tuple[float, int] = (16, 650)
    onda_recuperacao_ms: int = 450

    # --- Salto Meteoro (longe) ---
    salto_preparo_ms: int = 260
    salto_preset: str = 'tartarus_meteoro'
    salto_artilharia: str = 'tartarus_meteoro'
    salto_antecipacao: float = 0.85      # pousa onde o jogador VAI estar
    salto_shake: Tuple[float, int] = (14, 550)
    salto_recuperacao_ms: int = 1500     # recuperação lenta: a melhor janela para puni-lo

    # --- Chieftain Rampage (a barreira caiu pela barra) ---
    grito_ms: int = 800
    grito_shake: Tuple[float, int] = (10, 700)
    rampage_golpes: int = 3
    rampage_preparo_ms: int = 260
    rampage_dash: str = 'tartarus_rampage'
    rampage_artilharia: str = 'tartarus_rampage'
    rampage_pausa_ms: int = 150
    rampage_shake: Tuple[float, int] = (9, 320)
    ofegante_ms: int = 3200              # esquivou dos 3: exausto, parado, inofensivo...
    ofegante_mult: float = 1.5           # ...e tomando mais dano (a maior janela da luta)

    # --- Fúria (abaixo de 35%) ---
    furia_buff: float = 0.35             # +35% de velocidade (corrida e dashes), até o fim
    transicao_ms: int = 1000             # rugido da Fúria (descarta o capacete)

    # Punho de Rukt: salta ao meio da arena e soca o chão (cruz, depois diagonais)
    punho_salto: str = 'tartarus_punho'
    punho_cruz: str = 'tartarus_rukt_cruz'
    punho_diagonal: str = 'tartarus_rukt_diagonal'
    punho_intervalo_ms: int = 900        # da cruz às diagonais
    punho_shake: Tuple[float, int] = (16, 700)
    punho_energia_densidade: float = 0.45
    punho_recuperacao_ms: int = 900
    punho_raio_busca: Tuple[int, ...] = (0, 120, 240, 360, 480)   # chão válido perto do meio

    # Hammer Run: dash longo, reto, e a mega explosão no fim
    corrida_preparo_ms: int = 550
    corrida_dash: str = 'tartarus_corrida'
    corrida_artilharia: str = 'tartarus_corrida'
    corrida_poeira_ms: int = 45
    corrida_shake: Tuple[float, int] = (18, 750)
    corrida_recuperacao_ms: int = 700

    # Invocação de Brutes (fora da rotina, só na Fúria)
    brutes_por_invocacao: int = 3
    max_brutes: int = 6
    brutes_cooldown: Tuple[int, int] = (18000, 24000)
    brutes_primeira_ms: int = 3000       # depois do rugido da Fúria
    spawn_raio: Tuple[int, int] = (90, 150)
    spawn_tentativas: int = 14

    # --- Anti-stuck: preso longe do jogador -> salta em cima dele (com o impacto do meteoro) ---
    antistuck: ConfigTravamento = ConfigTravamento(janela_ms=800, caminho_min=40, dist_min=220, janela_livre=True)
    antistuck_salto: str = 'tartarus_antistuck'

    # --- vfx ---
    cor_barreira: Tuple[int, int, int] = (120, 140, 255)
    cor_sobrecarga: Tuple[int, int, int] = (255, 230, 120)
    cor_furia: Tuple[int, int, int] = (255, 40, 20)
    barreira_alpha: Tuple[int, int] = (60, 120)
    barreira_periodo_ms: int = 900
    furia_alpha: Tuple[int, int] = (40, 110)
    furia_periodo_ms: int = 520
    furia_brasas_ms: int = 80
    ofegante_vapor_ms: int = 260

    def __post_init__(self):
        if set(self.cooldown) != set(self.cooldown_inicial):
            raise ValueError('TartarusConfig: cada cooldown precisa do seu primeiro uso (e vice-versa)')
        if not 0 < self.barreira_reducao < 1:
            raise ValueError('TartarusConfig: barreira_reducao precisa estar em (0, 1)')
        if self.vortice_alcance >= self.vortice_raio:
            raise ValueError('TartarusConfig: vortice_alcance precisa ficar dentro do vortice_raio')


CFG = TartarusConfig()

# Decisão (F3). "Nunca usa um golpe sem ter certeza do alcance": o `alcance` corta (nota 0 fora) e os
# `pontuar_*` conferem o resto. Longe, o salto domina; de média, a onda; colado, o vórtice.
# Rampage é reação (`pensar`); a invocação corre fora da rotina (`perceber`).
HABILIDADES = {
    'vortice': Habilidade(peso=1.1, alcance=(0, CFG.vortice_alcance), ideal=(0, 240)),
    'onda':    Habilidade(peso=0.9, alcance=(140, 820), ideal=(260, 640)),
    'salto':   Habilidade(peso=1.2, alcance=(520, math.inf), ideal=(650, 1500)),
    'punho':   Habilidade(peso=0.8),
    'corrida': Habilidade(peso=0.9, alcance=(300, 900), ideal=(420, 760)),
}
