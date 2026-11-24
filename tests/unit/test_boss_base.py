"""Motor dos bosses (roteiro F1): BossBase, ContextoCombate, fases, cooldowns, interrupção e
anti-stuck. A equivalência com o Arbiter de antes fica em integration/test_golden_arbiter.py."""

import pygame
import pytest

from helpers import DT
from source.enemies.base.boss import (BossBase, ConfigTravamento, ContextoCombate, DetectorTravamento,
                                      FaseBoss, fase_pela_vida)
from source.systems.gameclock import relogio
from source.systems.spawner.spawner_bosses import BOSS_CLASSES

V = pygame.math.Vector2
FASES = (FaseBoss('A', 1.0, 1.0, 1.0), FaseBoss('B', 0.6, 0.5, 1.2), FaseBoss('C', 0.3, 0.25, 1.5))


class BossDeTeste(BossBase):
    """Parado (velocidade 0), com uma habilidade de 300 ms e cooldown fixo de 1000 ms."""
    FASES = FASES
    COOLDOWNS = {'golpe': (1000, 1000)}
    COOLDOWN_INICIAL = {'golpe': 500}
    ESTADOS = {**BossBase.ESTADOS, 'golpe': 'golpeando'}
    ANTISTUCK = ConfigTravamento(janela_ms=1000, caminho_min=40, dist_min=200)

    def __init__(self, posicao, game):
        super().__init__(posicao, vida_base=1000, dano_base=10, velocidade_base=0, game=game,
                         sprite_key='arbiter', flip_sprite=True)
        self.registro = []
        self.habilidades_ligadas = True

    def escolher_habilidade(self, agora):
        return 'golpe' if self.habilidades_ligadas and self.pronto('golpe') else None

    def rotina_golpe(self):
        self.registro.append('inicio')
        try:
            yield from self._esperar(300)
            self.registro.append('fim')
        finally:
            self.registro.append('finally')
        self.agendar('golpe')

    def rotina_antistuck(self):
        self.registro.append('antistuck')
        yield


@pytest.fixture
def boss(novo_jogo):
    b = BossDeTeste(novo_jogo.player.posicao + V(1000, 0), novo_jogo)
    b.invencivel = False
    return b


def _passar(boss, ms):
    """Avança o relógio e o boss, frame a frame (só o boss: o resto do jogo não roda)."""
    for _ in range(round(ms / (DT * 1000))):
        relogio.avancar(DT)
        boss.update(DT)


def _ate_o_estado(boss, estado, limite_ms=5000):
    passou = 0
    while boss.estado_habilidade != estado:
        assert passou < limite_ms, f'não chegou em {estado!r} em {limite_ms} ms'
        _passar(boss, DT * 1000)
        passou += DT * 1000


# ------------------------------------------------------------------ #
def test_habilidade_espera_o_cooldown_inicial(boss):
    _passar(boss, 450)
    assert boss.estado_habilidade == 'idle' and boss.registro == []
    _passar(boss, 100)
    assert boss.estado_habilidade == 'golpeando' and boss.ultima_habilidade == 'golpe'
    assert boss.registro == ['inicio']


def test_rotina_termina_volta_a_idle_e_agenda_o_cooldown(boss):
    _ate_o_estado(boss, 'golpeando')
    _ate_o_estado(boss, 'idle')
    assert boss.registro == ['inicio', 'fim', 'finally']
    assert boss.rotina is None
    assert boss.cd['golpe'] == boss._agora + 1000


def test_cooldown_escala_com_a_fase(boss):
    boss.vida = boss.vida_maxima * 0.5
    _passar(boss, DT * 1000)
    assert boss.fase == 2
    boss.agendar('golpe')
    assert boss.cd['golpe'] == boss._agora + 500   # 1000 × mult_cooldown 0.5


def test_wait_segura_a_decisao(boss):
    _passar(boss, 600)              # cooldown já venceu
    boss.interromper_rotina()
    boss.wait = 200
    _passar(boss, 150)
    assert boss.estado_habilidade == 'idle' and 0 < boss.wait <= 50 + 1e-6
    _passar(boss, 100)
    assert boss.estado_habilidade == 'golpeando'


# ------------------------------------------------------------------ #
def test_interromper_fecha_a_rotina_sem_agendar(boss):
    _ate_o_estado(boss, 'golpeando')
    cd_antes = boss.cd['golpe']
    boss.travamento.caminho = 99
    boss.interromper_rotina()
    assert boss.registro == ['inicio', 'finally']          # o finally rodou; o resto não
    assert (boss.rotina, boss.estado_habilidade) == (None, 'idle')
    assert boss.cd['golpe'] == cd_antes
    assert boss.travamento.caminho == 0 and boss.travamento.ultimo_check == boss._agora
    assert boss.ultima_habilidade == 'golpe'


def test_depois_de_interrompido_volta_a_decidir(boss):
    _ate_o_estado(boss, 'golpeando')
    boss.interromper_rotina()
    _passar(boss, DT * 1000)
    assert boss.estado_habilidade == 'golpeando'          # cooldown não foi agendado: pronto de novo
    assert boss.registro == ['inicio', 'finally', 'inicio']


# ------------------------------------------------------------------ #
@pytest.mark.parametrize('razao, atual, esperado', [
    (1.0, 1, 1), (0.61, 1, 1), (0.6, 1, 2), (0.31, 1, 2), (0.3, 1, 3),
    (0.1, 1, 3),      # pula a fase 2
    (0.9, 3, 3),      # curado não volta
    (0.0, 2, 3),
])
def test_fase_pela_vida(razao, atual, esperado):
    assert fase_pela_vida(FASES, razao, atual) == esperado


def test_golpe_grande_pula_direto_para_a_ultima_fase(boss):
    boss.vida = boss.vida_maxima * 0.1
    _passar(boss, DT * 1000)
    assert (boss.fase, boss.fase_cfg) == (3, FASES[2])


def test_transicao_espera_a_rotina_ativa(boss):
    _ate_o_estado(boss, 'golpeando')
    boss.vida = boss.vida_maxima * 0.5
    _passar(boss, DT * 1000)
    assert boss.fase == 2 and boss.transicao_pendente and boss.estado_habilidade == 'golpeando'
    _ate_o_estado(boss, 'idle')                       # o golpe acabou neste frame...
    assert boss.transicao_pendente
    _passar(boss, DT * 1000)                          # ...e a transição vem na decisão seguinte
    assert boss.ultima_habilidade == 'transicao' and not boss.transicao_pendente


# ------------------------------------------------------------------ #
CFG_TRAVA = ConfigTravamento(janela_ms=1000, caminho_min=40, dist_min=200)
LONGE_SQ = 300 ** 2


def _detector():
    return DetectorTravamento(CFG_TRAVA, 0, V(0, 0))


def test_parado_e_longe_trava_so_depois_da_janela():
    d = _detector()
    assert d.travou(1000, LONGE_SQ) is False      # janela ainda não passou (<=)
    assert d.travou(1001, LONGE_SQ) is True


def test_boss_parado_e_longe_dispara_a_rotina_antistuck(boss):
    boss.habilidades_ligadas = False
    _ate_o_estado(boss, 'antistuck_combat', limite_ms=1200)
    assert boss.registro == ['antistuck'] and boss.ultima_habilidade == 'antistuck'
    _ate_o_estado(boss, 'idle')
    assert boss.travamento.caminho == 0


# ------------------------------------------------------------------ #
class _Falso:
    def __init__(self, pos_jogador, pos_boss, vida=50, vida_maxima=100):
        self.jogador = type('J', (), {'posicao': V(pos_jogador)})()
        self.posicao = V(pos_boss)
        self.vida, self.vida_maxima = vida, vida_maxima


def test_contexto_ignora_teleporte_e_dt_zero():
    b = _Falso((0, 0), (500, 0))
    ctx = ContextoCombate(b.jogador.posicao)
    b.jogador.posicao.x += 1000                   # 60000 px/s em um frame
    ctx.atualizar(b, DT)
    assert ctx.vel_jogador == V(0, 0)
    b.jogador.posicao.x += 10
    ctx.atualizar(b, 0)
    assert ctx.vel_jogador == V(0, 0)
    b.jogador.posicao.x += 10                     # a referência andou junto: só 10 px aqui
    ctx.atualizar(b, DT)
    assert ctx.vel_jogador.x == pytest.approx(0.25 * 10 / DT)


# ------------------------------------------------------------------ #
BOSSES_NO_MOTOR = sorted(n for n, c in BOSS_CLASSES.items() if issubclass(c, BossBase))


@pytest.mark.parametrize('nome', BOSSES_NO_MOTOR)
def test_todo_estado_tem_rotina(nome):
    classe = BOSS_CLASSES[nome]
    faltando = [e for e in classe.ESTADOS if not callable(getattr(classe, f'rotina_{e}', None))]
    assert faltando == []
    assert set(classe.COOLDOWNS) <= set(classe.ESTADOS)


@pytest.mark.parametrize('nome', BOSSES_NO_MOTOR)
def test_boss_real_decide_algo(novo_jogo, nome):
    novo_jogo.spawner.spawnar(nome)
    boss = novo_jogo.sessao.boss_atual
    usadas = set()
    for _ in range(round(20 / DT)):
        relogio.avancar(DT)
        boss.update(DT)
        usadas.add(boss.ultima_habilidade)
    assert usadas - {None}, 'em 20 s o boss não usou nenhuma habilidade'
