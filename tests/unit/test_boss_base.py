"""Motor dos bosses (roteiro F1): BossBase, ContextoCombate, fases, cooldowns, interrupção e
anti-stuck. A equivalência com o Arbiter de antes fica em integration/test_golden_arbiter.py."""
import math

import pygame
import pytest

from helpers import DT
from source.enemies.base.boss import (BossBase, ConfigTravamento, ContextoCombate, DetectorTravamento,
                                      FaseBoss, fase_pela_vida)
from source.systems.gameclock import relogio
from source.systems.spawner.spawner_bosses import BOSS_CLASSES
from source.systems.status import IMUNIDADES_CHEFE

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
# Criação
# ------------------------------------------------------------------ #
def test_boss_nasce_pronto(boss):
    agora = relogio.agora()
    assert boss.is_boss and IMUNIDADES_CHEFE <= boss.imunidades_status
    assert (boss.fase, boss.fase_cfg, boss.transicao_pendente) == (1, FASES[0], False)
    assert (boss.rotina, boss.estado_habilidade, boss.ultima_habilidade, boss.wait) == (None, 'idle', None, 0)
    assert boss.cd == {'golpe': agora + 500}
    assert isinstance(boss.travamento, DetectorTravamento)


def test_hitbox_padrao_acompanha_o_boss(boss):
    assert boss.hitbox == boss.rect and boss.hitbox is not boss.rect
    boss.posicao += V(37, -12)
    _passar(boss, DT * 1000)
    assert boss.hitbox.center == boss.rect.center


def test_sem_antistuck_nao_ha_detector(novo_jogo):
    class SemAntistuck(BossDeTeste):
        ANTISTUCK = None
    assert SemAntistuck(novo_jogo.player.posicao + V(500, 0), novo_jogo).travamento is None


def test_boss_sem_escolher_habilidade_falha_alto(novo_jogo):
    class Incompleto(BossBase):
        pass
    b = Incompleto(novo_jogo.player.posicao + V(500, 0), 100, 1, 0, novo_jogo, 'arbiter', flip_sprite=True)
    with pytest.raises(NotImplementedError, match='Incompleto'):
        _passar(b, DT * 1000)


def test_boss_padrao_tem_uma_fase_so(novo_jogo):
    class UmaFase(BossDeTeste):
        FASES = BossBase.FASES
    b = UmaFase(novo_jogo.player.posicao + V(500, 0), novo_jogo)
    b.vida = 1
    _passar(b, DT * 1000)
    assert b.fase == 1 and b.fase_cfg.mult_cooldown == 1.0


# ------------------------------------------------------------------ #
# Cooldowns e rotinas
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


def test_agendar_habilidade_sem_faixa_e_erro(boss):
    with pytest.raises(KeyError):
        boss.agendar('nao_existe')


def test_wait_segura_a_decisao(boss):
    _passar(boss, 600)              # cooldown já venceu
    boss.interromper_rotina()
    boss.wait = 200
    _passar(boss, 150)
    assert boss.estado_habilidade == 'idle' and 0 < boss.wait <= 50 + 1e-6
    _passar(boss, 100)
    assert boss.estado_habilidade == 'golpeando'


# ------------------------------------------------------------------ #
# Interrupção
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


def test_interromper_sem_rotina_nao_faz_nada(boss):
    boss.interromper_rotina()
    assert (boss.rotina, boss.estado_habilidade) == (None, 'idle')


def test_depois_de_interrompido_volta_a_decidir(boss):
    _ate_o_estado(boss, 'golpeando')
    boss.interromper_rotina()
    _passar(boss, DT * 1000)
    assert boss.estado_habilidade == 'golpeando'          # cooldown não foi agendado: pronto de novo
    assert boss.registro == ['inicio', 'finally', 'inicio']


# ------------------------------------------------------------------ #
# Fases
# ------------------------------------------------------------------ #
@pytest.mark.parametrize('razao, atual, esperado', [
    (1.0, 1, 1), (0.61, 1, 1), (0.6, 1, 2), (0.31, 1, 2), (0.3, 1, 3),
    (0.1, 1, 3),      # pula a fase 2
    (0.9, 3, 3),      # curado não volta
    (0.0, 2, 3),
])
def test_fase_pela_vida(razao, atual, esperado):
    assert fase_pela_vida(FASES, razao, atual) == esperado


def test_subir_de_fase_troca_os_numeros_e_roda_a_transicao(boss):
    boss.habilidades_ligadas = False
    boss.vida = boss.vida_maxima * 0.5
    boss.contexto.atualizar(boss, DT)               # a fase lê a vida do contexto do frame
    boss.checar_fase()
    assert (boss.fase, boss.fase_cfg, boss.transicao_pendente) == (2, FASES[1], True)
    _passar(boss, DT * 1000)
    assert boss.transicao_pendente is False
    assert boss.ultima_habilidade == 'transicao'         # a padrão não tem ato: acaba no mesmo frame
    assert boss.estado_habilidade == 'idle'


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


@pytest.mark.parametrize('campos', [
    ('', 1.0, 1.0, 1.0), ('X', 0.0, 1.0, 1.0), ('X', 1.5, 1.0, 1.0), ('X', 1.0, 0.0, 1.0),
    ('X', 1.0, 1.0, -1.0), ('X', 1.0, math.inf, 1.0), ('X', 1.0, 1.0, math.nan), ('X', '1', 1.0, 1.0),
])
def test_fase_invalida_e_recusada(campos):
    with pytest.raises(ValueError):
        FaseBoss(*campos)


# ------------------------------------------------------------------ #
# Anti-stuck
# ------------------------------------------------------------------ #
CFG_TRAVA = ConfigTravamento(janela_ms=1000, caminho_min=40, dist_min=200)
LONGE_SQ = 300 ** 2


def _detector():
    return DetectorTravamento(CFG_TRAVA, 0, V(0, 0))


def test_parado_e_longe_trava_so_depois_da_janela():
    d = _detector()
    assert d.travou(1000, LONGE_SQ) is False      # janela ainda não passou (<=)
    assert d.travou(1001, LONGE_SQ) is True


def test_andou_o_bastante_nao_trava():
    d = _detector()
    for x in range(0, 50, 10):
        d.registrar(V(x, 0), livre=True)
    assert d.caminho == 40
    assert d.travou(1001, LONGE_SQ) is False


def test_vai_e_volta_conta_como_caminho():
    """Deslocamento líquido zero, mas andou: não é travamento (era o falso positivo do strafe)."""
    d = _detector()
    for x in (30, 0, 30, 0):
        d.registrar(V(x, 0), livre=True)
    assert d.travou(1001, LONGE_SQ) is False


def test_perto_do_jogador_nao_trava():
    assert _detector().travou(1001, 200 ** 2) is False


def test_dentro_de_rotina_o_caminho_nao_conta():
    d = _detector()
    d.registrar(V(500, 0), livre=False)            # teleporte/investida da rotina
    assert d.caminho == 0
    d.registrar(V(510, 0), livre=True)            # a referência foi atualizada mesmo assim
    assert d.caminho == 10


def test_conferir_recomeca_a_janela():
    d = _detector()
    d.registrar(V(100, 0), livre=True)
    assert d.travou(1001, LONGE_SQ) is False
    assert (d.ultimo_check, d.caminho) == (1001, 0)
    assert d.travou(1500, LONGE_SQ) is False      # janela nova
    assert d.travou(2002, LONGE_SQ) is True


@pytest.mark.parametrize('campos', [(0, 40, 200), (1000, -1, 200), (1000, 40, 0), (1000, math.inf, 200),
                                    (1000, 40, math.nan), ('1000', 40, 200)])
def test_config_de_travamento_invalida(campos):
    with pytest.raises(ValueError):
        ConfigTravamento(*campos)


def test_boss_parado_e_longe_dispara_a_rotina_antistuck(boss):
    boss.habilidades_ligadas = False
    _ate_o_estado(boss, 'antistuck_combat', limite_ms=1200)
    assert boss.registro == ['antistuck'] and boss.ultima_habilidade == 'antistuck'
    _ate_o_estado(boss, 'idle')
    assert boss.travamento.caminho == 0


def test_boss_perto_do_jogador_nao_dispara_o_antistuck(novo_jogo):
    b = BossDeTeste(novo_jogo.player.posicao + V(100, 0), novo_jogo)
    b.habilidades_ligadas = False
    _passar(b, 3000)
    assert 'antistuck' not in b.registro


# ------------------------------------------------------------------ #
# Contexto
# ------------------------------------------------------------------ #
class _Falso:
    def __init__(self, pos_jogador, pos_boss, vida=50, vida_maxima=100):
        self.jogador = type('J', (), {'posicao': V(pos_jogador)})()
        self.posicao = V(pos_boss)
        self.vida, self.vida_maxima = vida, vida_maxima


def test_contexto_mede_distancia_e_vida():
    b = _Falso((300, 400), (0, 0))
    ctx = ContextoCombate(b.jogador.posicao)
    ctx.atualizar(b, DT)
    assert ctx.dist_sq == 250000 and ctx.dist == 500 and ctx.razao_vida == 0.5


def test_contexto_sem_vida_maxima_nao_divide_por_zero():
    b = _Falso((0, 0), (0, 0), vida=0, vida_maxima=0)
    ctx = ContextoCombate(b.jogador.posicao)
    ctx.atualizar(b, DT)
    assert ctx.razao_vida == 1.0


def test_contexto_suaviza_a_velocidade_do_jogador():
    b = _Falso((0, 0), (500, 0))
    ctx = ContextoCombate(b.jogador.posicao)
    b.jogador.posicao.x += 600 * DT                # 600 px/s
    ctx.atualizar(b, DT)
    assert ctx.vel_jogador.x == pytest.approx(150)   # 25% da amostra nova
    for _ in range(60):
        b.jogador.posicao.x += 600 * DT
        ctx.atualizar(b, DT)
    assert ctx.vel_jogador.x == pytest.approx(600, rel=1e-3)


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


def test_contexto_nao_divide_o_vetor_do_jogador():
    b = _Falso((0, 0), (500, 0))
    ctx = ContextoCombate(b.jogador.posicao)
    b.jogador.posicao.x += 5
    assert ctx._pos_jogador_ant == V(0, 0)


def test_mira_antecipada_tem_teto(boss):
    boss.contexto.vel_jogador = V(10000, 0)
    ponto = boss.ponto_antecipado(vel_projetil=100, fator=1.0, max_desloc=250)
    assert ponto.distance_to(boss.jogador.posicao) == pytest.approx(250)
    boss.contexto.vel_jogador = V(0, 0)
    assert boss.ponto_antecipado(500, 1.0) == boss.jogador.posicao


def test_direcao_para_o_jogador_em_cima_dele_nao_e_zero(boss):
    boss.posicao.update(boss.jogador.posicao)
    assert boss.dir_jogador() == V(1, 0)
    assert boss.direcao_antecipada(500, 1.0).length() == pytest.approx(1)


# ------------------------------------------------------------------ #
# Bosses reais sobre a BossBase
# ------------------------------------------------------------------ #
BOSSES_NO_MOTOR = sorted(n for n, c in BOSS_CLASSES.items() if issubclass(c, BossBase))


def test_arbiter_esta_no_motor():
    assert 'arbiter' in BOSSES_NO_MOTOR


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
