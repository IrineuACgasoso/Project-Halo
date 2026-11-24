"""Entrada desacoplada (roteiro E3): ComandoJogador, Teclado, Roteiro e quem consome o comando."""
import pathlib

import pygame
import pytest

from helpers import DT
from source.systems.entrada import PARADO, ComandoJogador, FonteEntrada, Roteiro, Teclado
from source.systems.status import Atordoamento, aplicar

V = pygame.math.Vector2
DIREITA = ComandoJogador(direcao=(1, 0))


class _TeclasFalsas:
    """Imita o ScancodeWrapper de pygame.key.get_pressed()."""
    def __init__(self, *teclas):
        self.teclas = set(teclas)

    def __getitem__(self, tecla):
        return tecla in self.teclas


def _apertar(monkeypatch, *teclas):
    monkeypatch.setattr(pygame.key, 'get_pressed', lambda: _TeclasFalsas(*teclas))


# ── Teclado ─────────────────────────────────────────────────────────────────
@pytest.mark.parametrize('teclas, direcao', [
    ((), (0, 0)),
    ((pygame.K_d,), (1, 0)),
    ((pygame.K_a,), (-1, 0)),
    ((pygame.K_w,), (0, -1)),
    ((pygame.K_s,), (0, 1)),
    ((pygame.K_w, pygame.K_a), (-1, -1)),
    ((pygame.K_s, pygame.K_d), (1, 1)),
    ((pygame.K_a, pygame.K_d), (0, 0)),   # opostas se anulam
    ((pygame.K_w, pygame.K_s), (0, 0)),
])
def test_teclado_mapeia_wasd(monkeypatch, teclas, direcao):
    _apertar(monkeypatch, *teclas)
    assert Teclado(cheats=False).ler().direcao == direcao


def test_ninguem_mais_le_o_teclado_direto():
    """Só a fonte Teclado chama get_pressed: o resto do jogo lê o comando (bot e replay
    trocam a fonte sem tocar em mais nada)."""
    raiz = pathlib.Path('source')
    leitores = sorted(str(p) for p in raiz.rglob('*.py')
                      if 'get_pressed' in p.read_text(encoding='utf-8'))
    assert leitores == [str(raiz / 'systems' / 'entrada.py')]


# ── Consumidores: jogador, veículo, hacks ───────────────────────────────────
def test_game_entrega_um_comando_por_passo(novo_jogo, monkeypatch):
    lidos = []

    class Contadora(FonteEntrada):
        def ler(self):
            lidos.append(1)
            return DIREITA

    monkeypatch.setattr(novo_jogo, 'entrada', Contadora())
    x = novo_jogo.player.posicao.x
    for _ in range(10):
        novo_jogo.update(DT)
    assert len(lidos) == 10
    assert novo_jogo.player.comando is DIREITA
    assert novo_jogo.player.posicao.x > x


def test_diagonal_nao_anda_mais_rapido(player):
    paredes = player.game.mapa.grade_paredes
    player.comando = ComandoJogador(direcao=(1, 1))
    pos = V(player.posicao)
    player.update(DT, paredes)
    assert player.direcao.length() == pytest.approx(1)
    assert player.posicao.distance_to(pos) == pytest.approx(player.velocidade * DT)


def test_atordoado_ignora_a_direcao_do_comando(player):
    aplicar(player, Atordoamento(1000))
    player.comando = DIREITA
    pos = V(player.posicao)
    player.update(DT, player.game.mapa.grade_paredes)
    assert player.posicao == pos


def test_veiculo_alterna_uma_vez_por_aperto(novo_jogo, monkeypatch):
    """Segurar V não alterna 60x/s: entra no 1º passo, sai só depois de soltar e apertar."""
    novo_jogo.event_manager._aplicar_escolha_de_upgrade('warhog')
    veiculo = novo_jogo.player.armas['warhog'].sprite_veiculo
    v = ComandoJogador(veiculo=True)
    monkeypatch.setattr(novo_jogo, 'entrada', Roteiro([(5, v), (2, PARADO), (1, v)]))
    estados = []
    for _ in range(8):
        novo_jogo.update(DT)
        estados.append(veiculo.embarcado)
    assert estados == [True] * 5 + [True, True] + [False]


# ── Cheats pelo botão da pausa ──────────────────────────────────────────────
def _tecla(tecla):
    return pygame.event.Event(pygame.KEYDOWN, key=tecla, mod=0)


def _ir_para_pausa_e_escolher_cheats(game):
    from source.systems.estados import PAUSA
    game.telas[game.estado_do_jogo].evento(_tecla(pygame.K_ESCAPE))
    assert game.estado_do_jogo == PAUSA
    menu = game.menu_pausa
    menu.selecionada = 0
    game.telas[PAUSA].evento(_tecla(pygame.K_s))       # RESUME -> CHEATS
    assert menu.opcoes[menu.selecionada] == 'CHEATS'
    game.telas[PAUSA].evento(_tecla(pygame.K_RETURN))


def test_botao_da_pausa_liga_e_desliga_os_cheats(novo_jogo, monkeypatch):
    from source.systems.estados import PAUSA
    monkeypatch.setattr(novo_jogo.teclado, 'cheats', False)   # o Game vive a sessão de testes toda
    menu = novo_jogo.menu_pausa
    assert menu.rotulo('CHEATS') == 'ATIVAR CHEATS'

    _ir_para_pausa_e_escolher_cheats(novo_jogo)
    assert novo_jogo.cheats is True
    assert novo_jogo.estado_do_jogo == PAUSA          # fica na pausa, mostrando as teclas
    assert menu.rotulo('CHEATS') == 'DESATIVAR CHEATS'
    menu.draw(novo_jogo.tela)                          # com a dica das teclas

    novo_jogo.telas[PAUSA].evento(_tecla(pygame.K_RETURN))
    assert novo_jogo.cheats is False
    assert menu.rotulo('CHEATS') == 'ATIVAR CHEATS'
    menu.draw(novo_jogo.tela)


def test_cheats_ligados_na_pausa_valem_no_jogo(novo_jogo, monkeypatch):
    """Do botão até o efeito: com o L apertado, o jogador sobe de nível no passo seguinte."""
    from source.systems.estados import JOGANDO
    monkeypatch.setattr(novo_jogo.teclado, 'cheats', False)
    _apertar(monkeypatch, pygame.K_l)
    nivel = novo_jogo.player.contador_niveis
    novo_jogo.update(DT)
    assert novo_jogo.player.contador_niveis == nivel   # desligado: L não faz nada

    _ir_para_pausa_e_escolher_cheats(novo_jogo)
    novo_jogo.mudar_estado(JOGANDO)
    novo_jogo.update(DT)
    assert novo_jogo.player.contador_niveis == nivel + 1
