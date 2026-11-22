"""Entrada desacoplada (roteiro E3): ComandoJogador, Teclado, Roteiro e quem consome o comando."""
import math
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


def _roteiro_fixo(comando):
    return Roteiro([(10 ** 6, comando)])


# ── ComandoJogador ──────────────────────────────────────────────────────────
def test_comando_padrao_e_parado():
    c = ComandoJogador()
    assert c == PARADO
    assert c.direcao == (0, 0)
    assert not (c.veiculo or c.hack_nivel or c.hack_portal or c.hack_boss)


def test_comando_aceita_direcao_analogica():
    assert ComandoJogador(direcao=(0.3, -0.8)).direcao == (0.3, -0.8)


@pytest.mark.parametrize('direcao', [[1, 0], (1,), (1, 0, 0), (math.nan, 0), (0, math.inf),
                                     ('1', 0), (True, 0), None])
def test_comando_rejeita_direcao_invalida(direcao):
    with pytest.raises(ValueError):
        ComandoJogador(direcao=direcao)


@pytest.mark.parametrize('campo', ['veiculo', 'hack_nivel', 'hack_portal', 'hack_boss'])
def test_comando_rejeita_acao_que_nao_e_bool(campo):
    with pytest.raises(TypeError):
        ComandoJogador(**{campo: 1})


def test_comando_e_imutavel():
    with pytest.raises(AttributeError):
        DIREITA.veiculo = True


def test_fonte_base_exige_ler():
    with pytest.raises(NotImplementedError):
        FonteEntrada().ler()


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


def test_teclado_mapeia_v_para_o_veiculo(monkeypatch):
    _apertar(monkeypatch, pygame.K_v)
    assert Teclado(cheats=False).ler() == ComandoJogador(veiculo=True)


def test_teclado_sem_cheats_nao_produz_hacks(monkeypatch):
    _apertar(monkeypatch, pygame.K_l, pygame.K_p, pygame.K_b)
    assert Teclado(cheats=False).ler() == PARADO


def test_teclado_com_cheats_mapeia_os_hacks(monkeypatch):
    _apertar(monkeypatch, pygame.K_l, pygame.K_p, pygame.K_b)
    c = Teclado(cheats=True).ler()
    assert c.hack_nivel and c.hack_portal and c.hack_boss and not c.veiculo


def test_teclado_ignora_outras_teclas(monkeypatch):
    _apertar(monkeypatch, pygame.K_UP, pygame.K_SPACE, pygame.K_e)
    assert Teclado(cheats=True).ler() == PARADO


def test_ninguem_mais_le_o_teclado_direto():
    """Só a fonte Teclado chama get_pressed: o resto do jogo lê o comando (bot e replay
    trocam a fonte sem tocar em mais nada)."""
    raiz = pathlib.Path('source')
    leitores = sorted(str(p) for p in raiz.rglob('*.py')
                      if 'get_pressed' in p.read_text(encoding='utf-8'))
    assert leitores == [str(raiz / 'systems' / 'entrada.py')]


# ── Roteiro ─────────────────────────────────────────────────────────────────
def test_roteiro_toca_os_segmentos_em_ordem_e_termina_parado():
    esquerda = ComandoJogador(direcao=(-1, 0))
    r = Roteiro([(2, DIREITA), (1, esquerda)])
    assert [r.ler() for _ in range(5)] == [DIREITA, DIREITA, esquerda, PARADO, PARADO]
    assert r.terminou


def test_roteiro_reiniciar_volta_ao_comeco():
    r = Roteiro([(1, DIREITA)])
    r.ler()
    assert r.terminou
    r.reiniciar()
    assert not r.terminou and r.ler() == DIREITA


def test_roteiro_vazio_e_parado():
    r = Roteiro([])
    assert r.terminou and r.ler() == PARADO


@pytest.mark.parametrize('passos', [0, -1, 1.5, True, '3'])
def test_roteiro_rejeita_passos_invalidos(passos):
    with pytest.raises(ValueError):
        Roteiro([(passos, DIREITA)])


def test_roteiro_rejeita_comando_que_nao_e_comando():
    with pytest.raises(TypeError):
        Roteiro([(3, (1, 0))])


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


def test_jogo_comeca_com_o_teclado(game):
    assert isinstance(game.entrada, Teclado)


def test_diagonal_nao_anda_mais_rapido(player):
    paredes = player.game.mapa.grade_paredes
    player.comando = ComandoJogador(direcao=(1, 1))
    pos = V(player.posicao)
    player.update(DT, paredes)
    assert player.direcao.length() == pytest.approx(1)
    assert player.posicao.distance_to(pos) == pytest.approx(player.velocidade * DT)


def test_parado_nao_anda(player):
    player.comando = PARADO
    pos = V(player.posicao)
    player.update(DT, player.game.mapa.grade_paredes)
    assert player.posicao == pos and player.direcao == (0, 0)


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


def test_hack_de_nivel_pelo_comando(novo_jogo, monkeypatch):
    player = novo_jogo.player
    monkeypatch.setattr(novo_jogo, 'entrada', Roteiro([(1, ComandoJogador(hack_nivel=True))]))
    nivel = player.contador_niveis
    novo_jogo.update(DT)
    assert player.contador_niveis == nivel + 1


def test_hack_de_portal_pelo_comando(novo_jogo, monkeypatch):
    monkeypatch.setattr(novo_jogo, 'entrada', Roteiro([(3, ComandoJogador(hack_portal=True))]))
    novo_jogo.update(DT)
    portal = novo_jogo.sessao.portal_atual
    assert portal is not None
    novo_jogo.update(DT)
    assert novo_jogo.sessao.portal_atual is portal   # segurar P não cria outro


def test_hack_de_boss_pelo_comando(novo_jogo, monkeypatch):
    chamadas = []
    monkeypatch.setattr(novo_jogo.spawner, 'forcar_proximo_boss', lambda: chamadas.append(1))
    monkeypatch.setattr(novo_jogo, 'entrada', Roteiro([(1, ComandoJogador(hack_boss=True))]))
    novo_jogo.update(DT)
    assert chamadas == [1]


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


def test_jogo_comeca_sem_cheats_e_a_entrada_padrao_e_o_teclado(game):
    assert game.cheats is False                       # o conftest remove MCE_DEBUG
    assert game.entrada is game.teclado


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


def test_rotulo_das_outras_opcoes_e_o_proprio_id(game):
    assert [game.menu_pausa.rotulo(o) for o in ('RESUME', 'EXIT TO MENU')] == ['RESUME', 'EXIT TO MENU']
