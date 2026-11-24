"""Todos os números do Zealot num lugar só (balanceamento sem caçar valor no código).

Danos, áreas e velocidades das habilidades ficam nos presets de `feats/skills/*/config.py`."""
import math
from dataclasses import dataclass, field
from typing import Dict, Tuple

from source.enemies.base.boss import Clip, ConfigTravamento

# nome da habilidade -> `estado_habilidade`
ESTADOS = {
    'combo': 'dash_combo', 'furtivo': 'stealth', 'defensiva': 'stealth_defesa',
    'antistuck': 'antistuck_combat', 'transicao': 'phase_shift',
}
SORTEAVEIS = ('combo', 'furtivo', 'perseguir')   # 'perseguir' = nenhuma habilidade por um instante

# Um ciclo só (4 quadros): os clips só mudam o ritmo, sem reiniciar o passo
CLIPS = {
    'andar': Clip(200),
    'preparo': Clip(300),       # parado: mirando, golpeando, recuperando
    'correr': Clip(110),        # sprint e camuflado
    'dash': Clip(40),
}


@dataclass(frozen=True)
class ZealotConfig:
    # --- atributos (vida e escudo escalam juntos com o nível do jogador) ---
    vida: float = 100
    escudo: float = 300
    dano_contato: float = 80
    velocidade: float = 120
    mult_sprint: float = 2.0            # longe do jogador, sem habilidade

    # --- decisão: pesos por faixa de distância (com escudo; sem ele, só a defensiva) ---
    dist_perto: float = 250
    dist_medio: float = 600             # acima disso é "longe"
    pesos: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        'perto': {'combo': 1},
        'medio': {'combo': 7, 'furtivo': 2},
        'longe': {'furtivo': 8, 'perseguir': 2}})
    perseguir_ms: Tuple[int, int] = (500, 900)
    # cooldowns (min, max) em ms, sorteados no FIM da habilidade
    cooldown: Dict[str, Tuple[int, int]] = field(default_factory=lambda: {
        'combo': (4000, 7000), 'furtivo': (6500, 9000)})
    cooldown_inicial: Dict[str, int] = field(default_factory=lambda: {'combo': 1500, 'furtivo': 2000})

    # --- combo de 3 dashes: puro → estocada (retângulo) → varredura (cone largo) ---
    combo_dash_preset: str = 'zealot'
    combo_preparo_ms: int = 400         # parado antes do 1º dash
    combo_pausa_ms: Tuple[int, int] = (600, 850)    # entre um dash e o próximo
    combo_estocada_preset: str = 'zealot_estocada'
    combo_cone_preset: str = 'zealot_varredura'
    combo_recuperacao_ms: int = 700     # parado depois do último golpe: a janela de punição

    # --- invisibilidade ofensiva ---
    furtivo_preset: str = 'zealot_furtivo'
    furtivo_buff: float = 2.4           # +240% de velocidade (408 px/s; o jogador começa com 500)
    furtivo_dist_bote: float = 200
    contorno_travado_ms: int = 200      # sem sair do lugar por este tempo (parede): contorna de lado...
    contorno_ms: Tuple[int, int] = (400, 900)         # ... por este tempo
    furtivo_bote_preset: str = 'zealot_bote'
    furtivo_preparo_ms: int = 150       # reaparece um instante antes do bote
    furtivo_recuperacao_ms: int = 600

    # --- invisibilidade defensiva (sem escudo) ---
    fuga_preset: str = 'zealot_defensiva'
    fuga_sprint_ms: int = 1800          # foge em disparada no começo...
    fuga_sprint_buff: float = 3.5       # ... a 540 px/s (o jogador começa com 500)
    fuga_buff: float = 2.0              # depois vagueia a 360 px/s: dá para alcançar
    fuga_dist_ideal: float = 800        # tenta ficar a esta distância do jogador
    fuga_passo: Tuple[float, float] = (250, 550)      # distância do próximo ponto sorteado
    fuga_troca_ms: Tuple[int, int] = (600, 1400)      # muda de rumo ao acaso neste intervalo
    fuga_tentativas: int = 14
    fuga_angulo_graus: float = 60       # perto do jogador, não sorteia ponto neste cone na direção dele
    fuga_margem_mapa: float = 100
    regen_ms: int = 8000                # do escudo zerado ao cheio
    fuga_min_ms: int = 1500             # antes disso, encostar nele não o faz voltar
    fuga_dist_limite: float = 520       # jogador a esta distância: dash + cone fino, e volta ao ataque
    contra_dash_preset: str = 'zealot'
    contra_cone_preset: str = 'zealot_contra_ataque'
    contra_recuperacao_ms: int = 700

    # --- anti-stuck: some e reaparece perto do jogador ---
    antistuck: ConfigTravamento = ConfigTravamento(janela_ms=1200, caminho_min=30, dist_min=400)
    antistuck_preset: str = 'zealot_reposicao'
    antistuck_raio: Tuple[float, float] = (500, 650)
    antistuck_tentativas: int = 40

    # --- vfx ---
    cor_energia: Tuple[int, int, int] = (60, 200, 255)
    rastro_intervalo_ms: int = 25
    rastro_duracao_ms: int = 220
    rastro_alpha: int = 120
    faiscas_golpe: int = 16
    shake_golpe: float = 3
    shake_escudo: float = 4

    def __post_init__(self):
        if set(self.pesos) != {'perto', 'medio', 'longe'}:
            raise ValueError("ZealotConfig: pesos precisa ter as faixas 'perto', 'medio' e 'longe'")
        for faixa, pesos in self.pesos.items():
            if not pesos or not set(pesos) <= set(SORTEAVEIS) or not all(p > 0 for p in pesos.values()):
                raise ValueError(f'ZealotConfig: pesos de "{faixa}" inválidos: {pesos!r}')
        if 'combo' in self.pesos['longe']:
            raise ValueError('ZealotConfig: de longe ele não usa o combo de dashes')
        if set(self.cooldown) != set(self.cooldown_inicial):
            raise ValueError('ZealotConfig: cooldown e cooldown_inicial precisam ter as mesmas habilidades')
        if not 0 < self.dist_perto < self.dist_medio:
            raise ValueError('ZealotConfig: precisa ser 0 < dist_perto < dist_medio')
        if not 0 < self.fuga_dist_limite < self.fuga_dist_ideal:
            raise ValueError('ZealotConfig: precisa ser 0 < fuga_dist_limite < fuga_dist_ideal')

    @property
    def cos_fuga(self):
        return math.cos(math.radians(self.fuga_angulo_graus))


CFG = ZealotConfig()
COS_FUGA = CFG.cos_fuga
