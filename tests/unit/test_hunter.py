"""Hunter reformulado: armadura (Defesa) × costas, virar com atraso, IA por distância, dash, slam e vfx."""
import random

import pygame
import pytest

from helpers import DT, blindar_jogador
from source.enemies.minibosses.hunter.config import CFG
from source.systems.dano import PROJETIL, Dano
from source.systems.gameclock import relogio
from source.systems.status import Defesa

V = pygame.math.Vector2
CENTRO = V(1500, 1500)


@pytest.fixture
def hunter(novo_jogo):
    novo_jogo.spawner.spawnar('hunter')
    h = novo_jogo.sessao.boss_atual
    h.posicao.update(CENTRO)
    h.sync_rect()
    h.escudo_atual, h.vida = 0, 10 ** 6
    h.invencivel = False
    blindar_jogador(novo_jogo.player)
    _jogador_em(h, V(300, 0))
    return h


def _jogador_em(h, deslocamento):
    h.jogador.posicao.update(h.posicao + deslocamento)


def _parar_ia(h):
    """Sem pensar nem andar: só orientação, vulnerabilidade e animação."""
    h.livre_em = float('inf')
    h.movimento_livre = False


def _passos(h, segundos):
    for _ in range(round(segundos / DT)):
        relogio.avancar(DT)
        h.update(DT)


def _olhando_para(h, lado):
    h.virar_para(lado)
    h.virar_em = None
    h.atualizar_vulnerabilidade()


def _vida_tirada(h, valor=100):
    antes = h.vida
    h.receber_dano(Dano(valor, PROJETIL))
    return antes - h.vida


# ── Armadura e costas ────────────────────────────────────────────────────────
COSTAS = V(-300, 0)
@pytest.mark.parametrize('lado, deslocamento, vulneravel', [
    (1, V(300, 0), False),                                # olhando para a direita, jogador na frente
    (1, COSTAS, True),                                    # costas, no eixo
    (1, COSTAS.rotate(CFG.costas_graus - 1), True),       # costas, 1° dentro da borda do cone
    (1, COSTAS.rotate(-(CFG.costas_graus - 1)), True),
    (1, COSTAS.rotate(CFG.costas_graus + 1), False),      # costas, 1° fora do cone
    (1, COSTAS.rotate(-(CFG.costas_graus + 1)), False),
    (1, V(0, 300), False),                                # de lado
    (-1, V(300, 0), True),                                # olhando para a esquerda: costas = +x
    (-1, V(-300, 0), False),
])
def test_vulneravel_so_nas_costas_dentro_do_cone(hunter, lado, deslocamento, vulneravel):
    _parar_ia(hunter)
    _jogador_em(hunter, deslocamento)
    _olhando_para(hunter, lado)
    assert hunter.vulneravel is vulneravel
    assert hunter.status.tem(Defesa) is (not vulneravel)
    assert _vida_tirada(hunter) == pytest.approx(100 if vulneravel else 100 * (1 - CFG.defesa))


def test_sair_das_costas_devolve_a_defesa(hunter):
    _parar_ia(hunter)
    _olhando_para(hunter, 1)
    _jogador_em(hunter, V(-200, 0))
    hunter.atualizar_vulnerabilidade()
    assert hunter.vulneravel and hunter.status.mult_dano_recebido == 1.0
    _jogador_em(hunter, V(-200, 200))
    hunter.atualizar_vulnerabilidade()
    assert not hunter.vulneravel and hunter.status.mult_dano_recebido == pytest.approx(0.1)
    assert len([e for e, _, _ in hunter.status.ativos() if type(e) is Defesa]) == 1


# ── Virar com atraso ─────────────────────────────────────────────────────────
def test_vira_so_depois_do_atraso(hunter):
    _parar_ia(hunter)
    _olhando_para(hunter, 1)
    _jogador_em(hunter, V(-300, 0))
    _passos(hunter, CFG.atraso_virar_ms / 1000 - 0.1)
    assert hunter.lado == 1 and hunter.estado_animacao == 'right'
    assert hunter.vulneravel                          # enquanto não vira, o jogador está nas costas
    _passos(hunter, 0.2)
    assert hunter.lado == -1 and hunter.estado_animacao == 'left'
    assert not hunter.vulneravel


def test_spam_de_lado_nao_reinicia_o_timer_e_vale_o_lado_no_vencimento(hunter):
    _parar_ia(hunter)
    _olhando_para(hunter, 1)
    lados = [V(-300, 0), V(300, 0)]
    for i in range(7):                                # 7 × 0,2 s = 1,4 s trocando de lado
        _jogador_em(hunter, lados[i % 2])
        _passos(hunter, 0.2)
    _jogador_em(hunter, V(-300, 0))
    _passos(hunter, 0.2)                              # vence aos 1,5 s com o jogador à esquerda
    assert hunter.lado == -1


# ── Dash ─────────────────────────────────────────────────────────────────────
def _iniciar(h, nome):
    h.ultima_habilidade = nome
    h.rotina = getattr(h, f'rotina_{nome}')()
    h.livre_em = float('inf')


def test_dash_corre_olhando_para_o_lado_da_corrida_e_depois_fica_parado(hunter):
    _olhando_para(hunter, 1)
    _jogador_em(hunter, V(-300, 0))
    _iniciar(hunter, 'dash')
    _passos(hunter, DT)
    assert hunter.lado == -1 and not hunter.is_inofensivo
    _passos(hunter, 2.0)
    assert hunter.posicao.x == pytest.approx(CENTRO.x - 500 * 2.0, abs=1)   # passou do jogador
    assert hunter.is_inofensivo and hunter.animacao_congelada and hunter.estado_habilidade == 'stun'
    parado = V(hunter.posicao)
    frame = hunter.frame_atual
    _passos(hunter, CFG.atraso_virar_pos_dash_ms / 1000 - 0.1)
    assert hunter.posicao == parado and hunter.frame_atual == frame
    assert hunter.lado == -1                          # o jogador ficou nas costas: ainda não virou
    assert hunter.vulneravel
    _passos(hunter, 0.2)
    assert hunter.lado == 1 and not hunter.is_inofensivo and hunter.rotina is None
    assert hunter.cd['dash'] > relogio.agora()


# ── Shield slam ──────────────────────────────────────────────────────────────
def test_slam_so_com_o_jogador_colado_e_na_frente(hunter):
    _olhando_para(hunter, 1)
    for deslocamento, pode in [(V(150, 0), True), (V(150, 140), True), (V(150, 160), False),
                               (V(-150, 0), False), (V(400, 0), False)]:
        _jogador_em(hunter, deslocamento)
        assert hunter.pode_slam() is pode, deslocamento


# ── IA ───────────────────────────────────────────────────────────────────────


def test_luta_de_20_segundos_usa_as_habilidades_sem_quebrar(novo_jogo, hunter):
    """Loop real (com paredes e colisão): o jogador parado perto dele."""
    from helpers import simular
    random.seed(3)
    _jogador_em(hunter, V(350, 0))
    usadas = set()
    for _ in range(20):
        simular(novo_jogo, 1)
        usadas.add(hunter.ultima_habilidade)
    assert hunter.alive() and {'dash'} <= usadas
