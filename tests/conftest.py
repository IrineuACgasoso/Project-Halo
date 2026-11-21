"""Configuração global da suíte.

O jogo carrega TODOS os assets no import de `source.feats.assets` (pygame.init + set_mode
oculto + ~120 MB de imagens, ~13 s). Por isso:
  - os drivers SDL são forçados para `dummy` ANTES de qualquer import de pygame;
  - o cwd vira a raiz do repo, porque `source.utils.paths.path()` resolve relativo ao cwd;
  - o `Game` é criado uma única vez por sessão (fixture `game`) e cada teste que precisa
    de uma partida chama `novo_jogo`, que reseta os singletons via `iniciar_novo_jogo()`.
"""
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.pop('MCE_DEBUG', None)   # hacks de debug (L/P/B) desligados nos testes
os.chdir(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame  # noqa: E402
import pytest  # noqa: E402

import source.feats.assets  # noqa: E402,F401  (carrega assets uma vez)
from source.windows.settings import largura_tela, altura_tela  # noqa: E402


@pytest.fixture(scope='session')
def tela():
    return pygame.display.set_mode((largura_tela, altura_tela))


@pytest.fixture(scope='session')
def game(tela):
    from source.game import Game
    return Game(tela)


@pytest.fixture
def novo_jogo(game):
    """Partida nova e determinística (fase 0, AssaultRifle, sem bosses)."""
    random.seed(1234)
    game.iniciar_novo_jogo()
    game.renderer._erros_logados.clear()
    yield game
    game.estado_do_jogo = 'menu_principal'
    game.tela_de_upgrade_ativa = None


@pytest.fixture
def player(novo_jogo):
    return novo_jogo.player
