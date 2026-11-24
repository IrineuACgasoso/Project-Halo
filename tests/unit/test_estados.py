"""Estados formalizados (roteiro B2): tabela de transições, mudar_estado e o registro de telas."""
import os
import re

import pygame
import pytest

from helpers import voltar_ao_menu
from source.systems import estados
from source.systems.estados import (ESTADOS, TRANSICOES, TransicaoInvalida, MENU_PRINCIPAL, JOGANDO, PAUSA, LEVEL_UP, CONFIGURACOES,
                                    COLABORADORES, RANKING, GAME_OVER)

RAIZ_SOURCE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), 'source')


def _tecla(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode='')


def _escolher(monkeypatch, tela, escolha):
    """A próxima chamada de `tela.handle_event` devolve `escolha` (simula a navegação do menu)."""
    monkeypatch.setattr(tela, 'handle_event', lambda evento: escolha)


def _evento(game):
    """Entrega um evento ao handler do estado atual, como o EventManager faz."""
    game.telas[game.estado_do_jogo].evento(_tecla(pygame.K_RETURN))


# ── Registro de telas ────────────────────────────────────────────────────────
def test_registro_de_telas_cobre_todos_os_estados(game):
    assert set(game.telas) == ESTADOS
    for estado, tela in game.telas.items():
        assert callable(tela.evento) and callable(tela.desenhar), estado


# ── mudar_estado ─────────────────────────────────────────────────────────────


def test_transicao_invalida_lanca_excecao_no_modo_estrito(novo_jogo):
    with pytest.raises(TransicaoInvalida, match="'jogando' -> 'menu_principal'"):
        novo_jogo.mudar_estado(MENU_PRINCIPAL)
    assert novo_jogo.estado_do_jogo == JOGANDO   # não aplicou


# ── Código ───────────────────────────────────────────────────────────────────
def _arquivos_source():
    for pasta, _, arquivos in os.walk(RAIZ_SOURCE):
        for nome in arquivos:
            if nome.endswith('.py'):
                caminho = os.path.join(pasta, nome)
                with open(caminho, encoding='utf-8') as f:
                    yield os.path.relpath(caminho, RAIZ_SOURCE), f.read()


def test_codigo_so_troca_estado_por_mudar_estado_com_constante():
    """Nenhuma atribuição direta ao estado e nenhum nome de estado escrito à mão."""
    for nome, texto in _arquivos_source():
        assert not re.search(r'estado_do_jogo\s*=[^=]', texto), nome
        for argumento in re.findall(r'\.mudar_estado\(([^)]*)\)', texto):   # chamadas
            assert argumento.isupper() and getattr(estados, argumento, None) in ESTADOS, \
                f'{nome}: mudar_estado({argumento})'


# ── Fluxos reais: toda transição usada está na tabela e todo par da tabela é usado ──
def test_fluxos_do_jogo_percorrem_exatamente_a_tabela(game, monkeypatch):
    """Percorre cada fluxo pelos handlers reais (modo estrito: transição fora da tabela lança
    exceção) e confere que o conjunto de transições feitas é a tabela inteira."""
    feitas = set()
    mudar_original = game.mudar_estado

    def registrar(novo):
        anterior = game.estado_do_jogo
        mudar_original(novo)
        feitas.add((anterior, novo))
    monkeypatch.setattr(game, 'mudar_estado', registrar)
    monkeypatch.setattr(game.ranking, 'start_name_input', lambda pontos: None)
    voltar_ao_menu(game)

    # Menu -> telas secundárias -> menu
    for escolha, estado, tela, saida in [
        ('RANKING', RANKING, game.ranking, 'exit_to_menu'),
        ('SETTINGS', CONFIGURACOES, game.tela_configuracoes, 'sair'),
        ('CREATORS', COLABORADORES, game.tela_colaboradores, 'sair'),
    ]:
        _escolher(monkeypatch, game.menu_principal, escolha)
        _evento(game)
        assert game.estado_do_jogo == estado
        _escolher(monkeypatch, tela, saida)
        _evento(game)
        assert game.estado_do_jogo == MENU_PRINCIPAL

    # Menu -> jogo -> pausa -> jogo -> pausa -> menu
    _escolher(monkeypatch, game.menu_principal, 'START GAME')
    _evento(game)
    assert game.estado_do_jogo == JOGANDO
    game.telas[JOGANDO].evento(_tecla(pygame.K_ESCAPE))
    assert game.estado_do_jogo == PAUSA
    _escolher(monkeypatch, game.menu_pausa, 'RESUME')
    _evento(game)
    assert game.estado_do_jogo == JOGANDO
    game.telas[JOGANDO].evento(_tecla(pygame.K_ESCAPE))
    _escolher(monkeypatch, game.menu_pausa, 'EXIT TO MENU')
    _evento(game)
    assert game.estado_do_jogo == MENU_PRINCIPAL

    # Level-up (dois acumulados: a tela fecha, volta ao jogo e abre a próxima) e game over
    game.menu_principal.handle_event = lambda evento: 'START GAME'
    _evento(game)
    p = game.player
    p.ganhar_xp(p.experiencia_level_up + p.experiencia_level_up_base + 10 * (p.contador_niveis + 1))
    assert game.estado_do_jogo == LEVEL_UP and len(p.fila_upgrades) == 1
    game.telas[LEVEL_UP].evento(_tecla(pygame.K_RETURN))
    assert game.estado_do_jogo == LEVEL_UP and not p.fila_upgrades
    game.telas[LEVEL_UP].evento(_tecla(pygame.K_RETURN))
    assert game.estado_do_jogo == JOGANDO
    p.vida_atual = 0
    game.update(1 / 60)
    assert game.estado_do_jogo == GAME_OVER

    # Game over -> RESTART -> jogo; sobe de nível e morre no mesmo update -> game over -> menu
    _escolher(monkeypatch, game.tela_game_over, 'RESTART MISSION')
    _evento(game)
    assert game.estado_do_jogo == JOGANDO
    game.player.ganhar_xp(game.player.experiencia_level_up)
    game.player.vida_atual = 0
    game._encerrar_partida()
    assert game.estado_do_jogo == GAME_OVER
    _escolher(monkeypatch, game.tela_game_over, 'EXIT TO MENU')
    _evento(game)
    assert game.estado_do_jogo == MENU_PRINCIPAL

    todas = {(o, d) for o, destinos in TRANSICOES.items() for d in destinos}
    assert feitas == todas
