# source/enemies/<...>/arbi/config.py
"""Todos os números do Arbiter num lugar só (balanceamento sem caçar valor no código)."""
from dataclasses import dataclass, field
from typing import Dict, Tuple

from source.enemies.base.boss import ConfigTravamento, FaseBoss


@dataclass(frozen=True)
class FaseArbiter(FaseBoss):
    # nome, limiar_vida, mult_cooldown e mult_velocidade vêm de FaseBoss (nesta ordem)
    carabina_tiros: int
    carabina_rastreio: float    # 0..1: quanto a rajada "puxa" pro jogador a cada tiro
    lamina_golpes: int          # combo da espada de energia
    granadas: int               # granadas por arremesso
    elites_por_invocacao: int
    max_elites: int             # teto de Elites invocados vivos ao mesmo tempo
    escudo_transicao: int       # escudo ganho ao entrar na fase (0 = nenhum)


FASES = (
    FaseArbiter('Comandante',      1.00, 1.00, 1.00, 5, 0.10, 1, 1, 2, 4,   0),
    FaseArbiter('Furia Sangheili', 0.60, 0.80, 1.12, 7, 0.16, 2, 2, 2, 5, 300),
    FaseArbiter('Ultimo Folego',   0.30, 0.65, 1.25, 9, 0.22, 3, 3, 3, 6, 400),
)


@dataclass
class ArbiterConfig:
    # --- a quem as habilidades "pertencem" (define quem leva o dano) ---
    dono_skills: str = 'BOSS'         # ConeStrike / Granada (confirme com o seu ArtilhariaAviso)
    dono_projetil: str = 'INIMIGO'    # Carabin (mesmo valor que o código original usava)

    # --- cooldowns: (min, max) em ms; sorteados e multiplicados por FaseArbiter.mult_cooldown ---
    cooldown: Dict[str, Tuple[int, int]] = field(default_factory=lambda: {
        'carabina':  (4500, 7000),
        'lamina':    (5000, 7500),
        'granada':   (7000, 10000),
        'furtivo':   (14000, 18000),
        'invocacao': (12000, 18000),
    })
    # primeiro uso depois do spawn (ms), pra ele não abrir o combate usando tudo
    cooldown_inicial: Dict[str, int] = field(default_factory=lambda: {
        'carabina': 3000, 'lamina': 3500, 'granada': 5000, 'furtivo': 10000, 'invocacao': 14000,
    })

    # --- movimento / posicionamento ---
    dist_min: float = 260             # abaixo disso ele recua (kite)
    dist_max: float = 480             # acima disso ele avança
    strafe_troca_ms: Tuple[int, int] = (1200, 2600)

    # --- revelar-se (flash) e janela de dano enquanto está camuflado ---
    vulneravel_ao_revelar: bool = True   # camuflado + revelado (atirou/golpeou) = pode tomar dano
    revelar_tiro_ms: int = 80
    revelar_tiro_alpha: int = 90

    # --- Carabina ---
    carabina_mira: int = 300             # telegraph: para e mira antes da rajada
    carabina_intervalo: int = 80
    carabina_dano: int = 15
    carabina_vel_proj: int = 550
    carabina_spread: float = 0.03
    carabina_antecipacao: float = 0.55   # 0 = mira onde o jogador está; 1 = mira perfeita no futuro
    carabina_leque_arco: float = 30.0    # graus (rajada em leque, fases 2+)
    carabina_recuperacao: int = 400
    carabina_alcance: float = 800

    # --- Espada de energia (ConeStrike azul, curto alcance) ---
    lamina_preset: str = 'arbiter_energy_sword'
    lamina_combo_mult: float = 0.82      # cada golpe seguinte do combo telegrafa mais rápido
    lamina_flash: int = 150              # duração do clarão pós-explosão do cone
    lamina_avanco_ms: int = 150
    lamina_avanco_mult: float = 6.5
    lamina_pausa: int = 60
    lamina_recuperacao: int = 500

    # --- Granada de plasma ---
    granada_preset: str = 'plasma_grenade'   # crie 'arbiter_plasma_grenade' no seu preset de artilharia p/ balancear
    granada_preparo: int = 550
    granada_intervalo: int = 380
    granada_recuperacao: int = 600
    granada_dist_min: float = 150
    granada_dist_max: float = 700
    granada_vel: float = 700
    granada_antecipacao: float = 0.8
    granada_offset_lateral: float = 150

    # --- Sprint invisivel ---
    furtivo_escudo: int = 250
    furtivo_fade_out: int = 1000
    furtivo_fade_in: int = 600
    furtivo_duracao: int = 3500
    furtivo_mult_vel: float = 4.0
    emboscada_dist: float = 205          # dist. p/ cortar o sprint e dar o golpe de espada

    # --- Anti-stuck: caminho percorrido < 40 px em 1,5 s (livre) e longe do jogador (> 200 px) ---
    antistuck: ConfigTravamento = ConfigTravamento(janela_ms=1500, caminho_min=40, dist_min=200)
    antistuck_tiros: int = 20
    antistuck_intervalo: int = 45
    antistuck_dano: int = 15
    antistuck_spread: float = 0.1

    # --- Invocacao ---
    invocacao_canal: int = 1000
    spawn_raio: Tuple[int, int] = (50, 110)
    spawn_tentativas: int = 14


CFG = ArbiterConfig()
