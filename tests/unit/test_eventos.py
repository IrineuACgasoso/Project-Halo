"""Barramento de eventos e ordem explícita do Game.update (roteiro B4)."""

import pygame
import pytest

from helpers import DT
from source.enemies.standard.grunt import GruntRed
from source.systems.eventos import (BarramentoEventos, eventos, INIMIGO_MORREU,
                                    FASE_TROCADA)

V = pygame.math.Vector2


@pytest.fixture
def barramento():
    return BarramentoEventos()


def _gravar(barramento, nome):
    recebidos = []
    barramento.assinar(nome, lambda **dados: recebidos.append(dados))
    return recebidos


# ── Barramento ───────────────────────────────────────────────────────────────


def test_emitir_entrega_os_dados_a_todos_na_ordem_de_assinatura(barramento):
    ordem = []
    barramento.assinar(FASE_TROCADA, lambda fase: ordem.append(('a', fase)))
    barramento.assinar(FASE_TROCADA, lambda fase: ordem.append(('b', fase)))
    barramento.emitir(FASE_TROCADA, fase=3)
    assert ordem == [('a', 3), ('b', 3)]


def test_partida_nova_limpa_as_assinaturas(novo_jogo):
    from helpers import voltar_ao_menu
    recebidos = _gravar(eventos, FASE_TROCADA)
    voltar_ao_menu(novo_jogo)
    novo_jogo.iniciar_novo_jogo()
    eventos.emitir(FASE_TROCADA, fase=1)
    assert recebidos == []


# ── Ordem do update ──────────────────────────────────────────────────────────
def test_update_roda_os_passos_na_ordem(novo_jogo, monkeypatch):
    chamados = []
    passos = ['_atualizar_portal', '_checar_boss_derrotado', '_checar_portal_tocado',
              '_atualizar_spawner', '_atualizar_status', '_atualizar_entidades', '_checar_game_over']
    for nome in passos:
        monkeypatch.setattr(novo_jogo, nome, lambda *a, _n=nome: chamados.append(_n))
    monkeypatch.setattr(novo_jogo.collision_manager, 'update', lambda dt: chamados.append('colisao'))
    monkeypatch.setattr(novo_jogo.stage_manager, 'update', lambda dt: chamados.append('fase'))
    novo_jogo.update(DT)
    assert chamados == passos[:6] + ['colisao', 'fase', passos[6]]


# ── Eventos emitidos pelo jogo ───────────────────────────────────────────────


def test_inimigo_morto_emite_evento_uma_vez(novo_jogo):
    recebidos = _gravar(eventos, INIMIGO_MORREU)
    grunt = GruntRed(posicao=novo_jogo.player.posicao + V(400, 0), game=novo_jogo)
    grunt.vida = 0
    novo_jogo.collision_manager.update(DT)
    novo_jogo.collision_manager.update(DT)
    assert recebidos == [{'inimigo': grunt}]


def test_morte_adiada_nao_emite_evento(novo_jogo, monkeypatch):
    """morrer() que não tira o inimigo do mundo (ex.: consciência do Warden) não é morte."""
    recebidos = _gravar(eventos, INIMIGO_MORREU)
    grunt = GruntRed(posicao=novo_jogo.player.posicao + V(400, 0), game=novo_jogo)
    monkeypatch.setattr(grunt, 'morrer', lambda grupos=None: None)
    grunt.vida = 0
    novo_jogo.collision_manager.update(DT)
    assert recebidos == []
