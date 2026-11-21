"""Estados do jogo e as transições permitidas entre eles (roteiro B2).

Toda troca de estado passa por `Game.mudar_estado`, que confere esta tabela. Estado
novo precisa entrar em `ESTADOS`, em `TRANSICOES` e no registro de telas (`Game.telas`):
os testes de `test_estados.py` verificam os três.
"""
from typing import Callable, NamedTuple

MENU_PRINCIPAL = 'menu_principal'
JOGANDO = 'jogando'
PAUSA = 'pausa'
LEVEL_UP = 'level_up'
CONFIGURACOES = 'configuracoes'
COLABORADORES = 'colaboradores'
RANKING = 'ranking'
GAME_OVER = 'game_over'

ESTADOS = frozenset({MENU_PRINCIPAL, JOGANDO, PAUSA, LEVEL_UP, CONFIGURACOES,
                     COLABORADORES, RANKING, GAME_OVER})

# origem -> destinos permitidos (cada par é usado em algum ponto do código)
TRANSICOES = {
    MENU_PRINCIPAL: frozenset({JOGANDO, RANKING, CONFIGURACOES, COLABORADORES}),
    JOGANDO:        frozenset({PAUSA, LEVEL_UP, GAME_OVER}),
    PAUSA:          frozenset({JOGANDO, MENU_PRINCIPAL}),
    # → GAME_OVER: o jogador pode subir de nível e morrer no mesmo update (a tela fica aberta,
    # mas a partida acaba). → LEVEL_UP não existe: a fila espera a tela atual fechar.
    LEVEL_UP:       frozenset({JOGANDO, GAME_OVER}),
    CONFIGURACOES:  frozenset({MENU_PRINCIPAL}),
    COLABORADORES:  frozenset({MENU_PRINCIPAL}),
    RANKING:        frozenset({MENU_PRINCIPAL}),
    GAME_OVER:      frozenset({JOGANDO, MENU_PRINCIPAL}),
}


class TransicaoInvalida(ValueError):
    """Troca de estado fora de `TRANSICOES`, ou para um estado que não existe."""


def transicao_valida(atual, novo):
    return novo in TRANSICOES.get(atual, ())


class Tela(NamedTuple):
    """O que o loop faz num estado: `evento(ev)` trata cada evento pygame; `desenhar()` pinta o frame."""
    evento: Callable
    desenhar: Callable
