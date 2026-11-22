"""Entrada do jogador desacoplada do teclado (roteiro E3).

O `Game` lê a fonte (`Game.entrada`) uma vez por passo de simulação e entrega o `ComandoJogador`
ao jogador (`player.comando`). Ninguém mais lê o teclado durante a partida: trocar a fonte por
um `Roteiro` (replay) ou por um bot (F4) não muda nada no resto do jogo.

O comando descreve o que está **pressionado** neste passo (não o que acabou de ser apertado):
quem precisa de borda (a tecla V dos veículos) guarda o estado anterior, como antes.
"""
import math
from dataclasses import dataclass

import pygame

from source.debug import DEBUG


@dataclass(frozen=True)
class ComandoJogador:
    """O que o jogador quer fazer neste passo.
    direcao: (x, y) com y para baixo; o jogador normaliza (diagonal não anda mais rápido).
    veiculo: tecla de entrar/sair do veículo pressionada.
    hack_*: atalhos de depuração pressionados (o `Teclado` só os produz com MCE_DEBUG=1)."""
    direcao: tuple = (0, 0)
    veiculo: bool = False
    hack_nivel: bool = False
    hack_portal: bool = False
    hack_boss: bool = False

    def __post_init__(self):
        if not isinstance(self.direcao, tuple) or len(self.direcao) != 2:
            raise ValueError(f'direcao precisa ser uma tupla (x, y), veio {self.direcao!r}')
        for v in self.direcao:
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise ValueError(f'direcao precisa de 2 números finitos, veio {self.direcao!r}')
        for nome in ('veiculo', 'hack_nivel', 'hack_portal', 'hack_boss'):
            if not isinstance(getattr(self, nome), bool):
                raise TypeError(f'{nome} precisa ser bool, veio {getattr(self, nome)!r}')


PARADO = ComandoJogador()


class FonteEntrada:
    """Contrato de toda fonte de entrada: `ler()` devolve o comando do passo atual."""

    def ler(self):
        raise NotImplementedError


class Teclado(FonteEntrada):
    """WASD anda, V entra/sai do veículo; L/P/B são os hacks (só com `debug`)."""

    def __init__(self, debug=DEBUG):
        self.debug = debug

    def ler(self):
        t = pygame.key.get_pressed()
        hacks = self.debug
        return ComandoJogador(
            direcao=(int(t[pygame.K_d]) - int(t[pygame.K_a]),
                     int(t[pygame.K_s]) - int(t[pygame.K_w])),
            veiculo=bool(t[pygame.K_v]),
            hack_nivel=hacks and bool(t[pygame.K_l]),
            hack_portal=hacks and bool(t[pygame.K_p]),
            hack_boss=hacks and bool(t[pygame.K_b]),
        )


class Roteiro(FonteEntrada):
    """Replay: segmentos `(passos, comando)` tocados em ordem, um `ler()` por passo.
    Terminado o roteiro, devolve `PARADO`."""

    def __init__(self, segmentos):
        self.segmentos = []
        for passos, comando in segmentos:
            if isinstance(passos, bool) or not isinstance(passos, int) or passos <= 0:
                raise ValueError(f'passos precisa ser um inteiro > 0, veio {passos!r}')
            if not isinstance(comando, ComandoJogador):
                raise TypeError(f'comando precisa ser ComandoJogador, veio {comando!r}')
            self.segmentos.append((passos, comando))
        self.reiniciar()

    def reiniciar(self):
        self._segmento = 0
        self._passo = 0

    @property
    def terminou(self):
        return self._segmento >= len(self.segmentos)

    def ler(self):
        if self.terminou:
            return PARADO
        passos, comando = self.segmentos[self._segmento]
        self._passo += 1
        if self._passo >= passos:
            self._segmento += 1
            self._passo = 0
        return comando
