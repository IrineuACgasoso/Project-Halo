"""Assets: placeholder no arquivo ausente, mapas sob demanda e import sem efeito colateral."""
import os
import subprocess
import sys

import pygame
import pytest

from source.data.manifesto_assets import Imagem
from source.feats import assets as modulo_assets
from source.feats.assets import MapasSobDemanda, carregar_imagem


# ------------------------------------------------------------------ #


@pytest.fixture
def sem_falhas_logadas(monkeypatch):
    monkeypatch.setattr(modulo_assets, '_arquivos_com_falha', set())


@pytest.mark.parametrize('alpha', [True, False])
def test_arquivo_ausente_vira_placeholder_magenta(sem_falhas_logadas, capsys, alpha):
    img = Imagem('nao/existe.png', (30, 20), alpha=alpha)
    superficie = carregar_imagem(img)
    assert superficie.get_size() == (30, 20)
    assert superficie.get_at((15, 10))[:3] == modulo_assets.COR_PLACEHOLDER
    assert bool(superficie.get_flags() & pygame.SRCALPHA) == alpha
    assert 'existe.png' in capsys.readouterr().out


# ------------------------------------------------------------------ #
@pytest.fixture
def decodificados(monkeypatch):
    """Troca o decodificador por um falso que anota cada arquivo pedido."""
    pedidos = []

    def falso(imagem):
        pedidos.append(imagem.arquivo)
        return pygame.Surface((4, 4))
    monkeypatch.setattr(modulo_assets, 'carregar_imagem', falso)
    return pedidos


def _mapas(limite=2):
    return MapasSobDemanda({str(n): Imagem(f'map/{n}/map{n}.jpg', alpha=False) for n in range(4)},
                           limite=limite)


def test_decodifica_no_primeiro_acesso_e_reaproveita(decodificados):
    mapas = _mapas()
    primeira = mapas['1']
    assert mapas['1'] is primeira
    assert decodificados == ['map/1/map1.jpg'] and mapas.carregados == ['1']


def test_guarda_so_os_mais_recentes(decodificados):
    mapas = _mapas(limite=2)
    for chave in '012':
        mapas[chave]
    assert mapas.carregados == ['1', '2']
    mapas['1']                       # volta a ser o mais recente
    mapas['3']
    assert mapas.carregados == ['1', '3']
    mapas['0']                       # foi descartado: decodifica de novo
    assert decodificados == ['map/0/map0.jpg', 'map/1/map1.jpg', 'map/2/map2.jpg',
                             'map/3/map3.jpg', 'map/0/map0.jpg']


def test_mapa_ausente_vira_placeholder(sem_falhas_logadas):
    mapas = MapasSobDemanda({'0': Imagem('map/nao_existe.jpg', alpha=False)})
    assert mapas['0'].get_size() == modulo_assets.TAMANHO_PLACEHOLDER


# ------------------------------------------------------------------ #
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def rodar_em_processo_novo(codigo):
    """Roda `codigo` num Python novo (este processo já carregou os assets) e devolve o stdout."""
    ambiente = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
                    PYGAME_HIDE_SUPPORT_PROMPT='1')
    ambiente.pop('MCE_DEBUG', None)
    feito = subprocess.run([sys.executable, '-c', codigo], cwd=RAIZ, env=ambiente,
                           capture_output=True, text=True, timeout=120)
    assert feito.returncode == 0, feito.stderr
    return feito.stdout.strip()


def test_importar_todo_o_jogo_nao_inicia_pygame_nem_carrega_assets():
    saida = rodar_em_processo_novo(
        'import sys, pygame\n'
        'sys.path.insert(0, "tests")\n'
        'from unit.test_imports import test_todo_modulo_importa\n'
        'test_todo_modulo_importa()\n'
        'from source.feats.assets import ASSETS\n'
        'print(pygame.get_init(), pygame.display.get_init(), len(ASSETS))')
    pygame_iniciado, display_iniciado, assets = saida.split()
    assert (pygame_iniciado, display_iniciado, assets) == ('False', 'False', '0')
