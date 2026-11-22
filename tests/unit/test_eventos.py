"""Barramento de eventos e ordem explícita do Game.update (roteiro B4)."""
import random

import pygame
import pytest

from helpers import DT, blindar_jogador
from source.enemies.standard.grunt import GruntRed
from source.systems.entitymanager import entity_manager
from source.systems.eventos import (BarramentoEventos, eventos, EVENTOS, INIMIGO_MORREU,
                                    DANO_CAUSADO, BOSS_DERROTADO, FASE_TROCADA)

V = pygame.math.Vector2


@pytest.fixture
def barramento():
    return BarramentoEventos()


def _gravar(barramento, nome):
    recebidos = []
    barramento.assinar(nome, lambda **dados: recebidos.append(dados))
    return recebidos


# ── Barramento ───────────────────────────────────────────────────────────────
def test_eventos_conhecidos():
    assert EVENTOS == {INIMIGO_MORREU, DANO_CAUSADO, BOSS_DERROTADO, FASE_TROCADA}


def test_emitir_entrega_os_dados_a_todos_na_ordem_de_assinatura(barramento):
    ordem = []
    barramento.assinar(FASE_TROCADA, lambda fase: ordem.append(('a', fase)))
    barramento.assinar(FASE_TROCADA, lambda fase: ordem.append(('b', fase)))
    barramento.emitir(FASE_TROCADA, fase=3)
    assert ordem == [('a', 3), ('b', 3)]


def test_emitir_sem_assinantes_nao_faz_nada(barramento):
    barramento.emitir(BOSS_DERROTADO, boss=None, fase=0)


def test_evento_so_chega_a_quem_assinou_ele(barramento):
    mortes = _gravar(barramento, INIMIGO_MORREU)
    barramento.emitir(FASE_TROCADA, fase=1)
    assert mortes == []


def test_evento_desconhecido_e_erro(barramento):
    with pytest.raises(ValueError, match='inimigo_morreuu'):
        barramento.assinar('inimigo_morreuu', lambda **d: None)
    with pytest.raises(ValueError):
        barramento.emitir('inimigo_morreuu')


def test_assinante_precisa_ser_chamavel(barramento):
    with pytest.raises(TypeError):
        barramento.assinar(FASE_TROCADA, 'nao_e_funcao')


def test_quem_assina_durante_a_emissao_so_recebe_a_proxima(barramento):
    tardios = []

    def assina_outro(fase):
        barramento.assinar(FASE_TROCADA, lambda fase: tardios.append(fase))
    barramento.assinar(FASE_TROCADA, assina_outro)
    barramento.emitir(FASE_TROCADA, fase=1)
    assert tardios == []
    barramento.emitir(FASE_TROCADA, fase=2)
    assert tardios == [2]


def test_excecao_do_assinante_sobe(barramento):
    def quebrado(fase):
        raise RuntimeError('bug do assinante')
    barramento.assinar(FASE_TROCADA, quebrado)
    with pytest.raises(RuntimeError):
        barramento.emitir(FASE_TROCADA, fase=1)


def test_limpar_remove_todas_as_assinaturas(barramento):
    recebidos = _gravar(barramento, FASE_TROCADA)
    barramento.limpar()
    barramento.emitir(FASE_TROCADA, fase=1)
    assert recebidos == []


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
def test_boss_derrotado_emite_evento_com_boss_e_fase(novo_jogo):
    recebidos = _gravar(eventos, BOSS_DERROTADO)
    novo_jogo.spawner.spawnar('hunter')
    boss = novo_jogo.sessao.boss_atual
    boss.kill()
    novo_jogo.update(DT)
    assert recebidos == [{'boss': boss, 'fase': 0}]


def test_troca_de_fase_emite_evento_com_a_fase_nova(novo_jogo):
    recebidos = _gravar(eventos, FASE_TROCADA)
    novo_jogo.stage_manager.iniciar_transicao()
    for _ in range(200):
        novo_jogo.stage_manager.update(DT)
    assert recebidos == [{'fase': 1}]


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


@pytest.mark.integration
def test_eventos_de_morte_batem_com_as_mortes_reais(novo_jogo):
    """60 s da fase 0 (as do golden): cada inimigo que saiu do mundo gerou exatamente um inimigo_morreu."""
    random.seed(1234)
    blindar_jogador(novo_jogo.player)
    recebidos = _gravar(eventos, INIMIGO_MORREU)
    vistos = set()
    for _ in range(round(60 / DT)):
        vistos.update(entity_manager.inimigos_grupo)
        novo_jogo.update(DT)
    mortos = {inimigo for inimigo in vistos if not inimigo.alive()}
    emitidos = [dados['inimigo'] for dados in recebidos]
    assert len(mortos) >= 10, 'a simulação precisa ter mortes para o teste valer'
    assert len(emitidos) == len(set(emitidos)) == len(mortos)
    assert set(emitidos) == mortos
