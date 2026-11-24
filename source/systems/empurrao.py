"""Empurrão (knockback): desloca uma entidade por alguns instantes, respeitando as paredes.

`empurrar(alvo, origem, forca)`: para longe de `origem`; `forca` é quanto ele anda ao todo, em px (a
velocidade começa alta e cai, então o tranco é quase todo nos primeiros 200 ms). Vale para o jogador e
para os inimigos comuns; bosses (`is_boss`) não se movem.

A entidade implementa `deslocar(vetor, paredes)`."""
import math
from numbers import Real

import pygame

from source.utils.vetores import direcao_segura

DECAIMENTO = 9.0         # 1/s: velocidade(t) = forca × DECAIMENTO × e^(−DECAIMENTO·t)
VELOCIDADE_MINIMA = 15   # px/s: abaixo disso o empurrão acabou
PASSO_MAXIMO = 30        # px: mais que isso de uma vez pularia uma parede (raio do jogador: 48)

_ativos = {}             # entidade -> velocidade (Vector2, px/s)


def forca_valida(forca):
    return isinstance(forca, Real) and not isinstance(forca, bool) and math.isfinite(forca) and forca > 0


def empurrar(alvo, origem, forca):
    """Empurra `alvo` para longe de `origem`. Com outro empurrão ativo, vale o mais forte dos dois."""
    if not forca_valida(forca):
        raise ValueError(f'força de empurrão {forca!r} (precisa ser um número > 0)')
    if getattr(alvo, 'is_boss', False) or not alvo.alive():
        return
    velocidade = direcao_segura(origem, alvo.posicao) * (forca * DECAIMENTO)
    atual = _ativos.get(alvo)
    if atual is None or atual.length_squared() < velocidade.length_squared():
        _ativos[alvo] = velocidade


def atualizar_empurroes(delta_time, paredes):
    if not _ativos:
        return
    fator = math.exp(-DECAIMENTO * delta_time)
    for alvo, velocidade in list(_ativos.items()):
        if not alvo.alive():
            del _ativos[alvo]
            continue
        # Integral exata do decaimento neste passo: o total não depende do tamanho do passo
        desloc = velocidade * ((1 - fator) / DECAIMENTO)
        pedacos = max(1, math.ceil(desloc.length() / PASSO_MAXIMO))
        for _ in range(pedacos):
            alvo.deslocar(desloc / pedacos, paredes)
        velocidade *= fator
        if velocidade.length_squared() < VELOCIDADE_MINIMA ** 2:
            del _ativos[alvo]


def limpar_empurroes():
    _ativos.clear()


def empurrao_ativo(alvo):
    """Velocidade atual do empurrão de `alvo` (px/s; nula se não há)."""
    return pygame.math.Vector2(_ativos.get(alvo, (0, 0)))
