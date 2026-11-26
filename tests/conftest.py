"""Configuração global da suíte.

Os assets são carregados uma vez, aqui, com `carregar_assets()` (pygame.init + janela oculta +
as imagens do manifesto, ~1,5 s; o import do jogo não carrega nada desde a D3). Por isso:
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

from source.feats.assets import carregar_assets  # noqa: E402
from source.windows.settings import largura_tela, altura_tela  # noqa: E402

carregar_assets()   # antes da coleta: os módulos de teste leem ASSETS no nível do módulo


def pytest_addoption(parser):
    parser.addoption('--atualizar-golden', action='store_true', default=False,
                     help='regrava tests/golden/*.json. Só em mudança de comportamento '
                          'declarada (roteiro §2, regra 5), com o motivo em docs/log.md')


@pytest.fixture(scope='session')
def tela():
    return pygame.display.set_mode((largura_tela, altura_tela))


@pytest.fixture(scope='session')
def game(tela):
    from source.game import Game
    game = Game(tela)
    game.estados_estritos = True   # transição de estado fora da tabela vira exceção (roteiro B2)
    return game


@pytest.fixture
def novo_jogo(game):
    """Partida nova e determinística (fase 0, AssaultRifle, sem bosses)."""
    from helpers import voltar_ao_menu
    voltar_ao_menu(game)   # um teste anterior pode ter terminado em qualquer estado
    random.seed(1234)
    game.iniciar_novo_jogo()
    game.renderer._erros_logados.clear()
    yield game
    voltar_ao_menu(game)


@pytest.fixture
def player(novo_jogo):
    """O jogador sem o escudo de fábrica: os testes de dano leem a vida direto (quem testa escudo o põe)."""
    novo_jogo.player.adicionar_escudo(0)
    return novo_jogo.player
