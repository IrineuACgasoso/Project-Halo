"""Assets: manifesto e equivalência com o carregamento antigo (roteiro D1); mapas sob demanda (D2);
import sem efeito colateral (D3).

`tests/golden/assets.json` foi gravado com as 251 linhas literais, ANTES da troca pelo manifesto:
cada superfície vira 'LxA bits alpha|opaco crc32-dos-pixels-RGBA'.
Regravar (só quando a arte muda de propósito):
    .venv\\Scripts\\python.exe -m pytest tests/unit/test_assets.py --atualizar-golden
"""
import json
import os
import subprocess
import sys
import zlib

import pygame
import pytest

from source.data.manifesto_assets import MANIFESTO, Imagem, folhas, numerados, quadros
from source.feats import assets as modulo_assets
from source.feats.assets import ASSETS, MapasSobDemanda, carregar_assets, carregar_imagem
from source.utils.paths import path

CAMINHO_REGISTRO = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'golden', 'assets.json')


def descrever(no):
    """A árvore de ASSETS com cada Surface trocada pela sua assinatura."""
    if isinstance(no, pygame.Surface):
        alpha = bool(no.get_flags() & pygame.SRCALPHA)
        crc = zlib.crc32(pygame.image.tobytes(no, 'RGBA'))
        return (f'{no.get_width()}x{no.get_height()} {no.get_bitsize()}b '
                f'{"alpha" if alpha else "opaco"} {crc:08x}')
    if isinstance(no, list):
        return [descrever(x) for x in no]
    return {str(k): descrever(no[k]) for k in no}


def test_assets_equivalentes_ao_registro(request):
    obtido = descrever(ASSETS)
    if request.config.getoption('--atualizar-golden'):
        with open(CAMINHO_REGISTRO, 'w', encoding='utf-8') as f:
            json.dump(obtido, f, indent=1, sort_keys=True)
        pytest.skip(f'registro regravado em {CAMINHO_REGISTRO}: registre o motivo em docs/log.md')
    with open(CAMINHO_REGISTRO, encoding='utf-8') as f:
        esperado = json.load(f)
    assert obtido == esperado


# ------------------------------------------------------------------ #
# Manifesto
# ------------------------------------------------------------------ #
def test_todo_arquivo_do_manifesto_existe():
    faltando = sorted({img.arquivo for img in folhas()
                       if not os.path.isfile(path('assets', 'img', *img.arquivo.split('/')))})
    assert not faltando


def test_manifesto_so_tem_imagens_validas():
    for img in folhas():
        assert isinstance(img, Imagem)
        assert '\\' not in img.arquivo and not img.arquivo.startswith('/')
        if img.escala is not None:
            largura, altura = img.escala
            assert largura > 0 and altura > 0, img


def test_folhas_percorre_dicts_e_listas_em_ordem():
    arvore = {'a': Imagem('x.png'), 'b': [Imagem('y.png'), {'c': Imagem('z.png')}]}
    assert [i.arquivo for i in folhas(arvore)] == ['x.png', 'y.png', 'z.png']


def test_ajudantes_de_quadros():
    assert numerados('tp', 3) == ['tp1.png', 'tp2.png', 'tp3.png']
    assert numerados('red', 6, inicio=5) == ['red5.png', 'red6.png']
    assert numerados('x', 0) == []
    assert quadros('p', ['a.png'], (1, 2), espelhar=True) == [Imagem('p/a.png', (1, 2), espelhar=True)]


def test_estrutura_de_assets_espelha_o_manifesto():
    def forma(no):
        if isinstance(no, (Imagem, pygame.Surface)):
            return 'folha'
        if isinstance(no, MapasSobDemanda):   # sem decodificar os fundos
            return {k: 'folha' for k in no}
        if isinstance(no, list):
            return [forma(x) for x in no]
        return {k: forma(v) for k, v in no.items()}
    assert forma(ASSETS) == forma(MANIFESTO)


# ------------------------------------------------------------------ #
# Carregador
# ------------------------------------------------------------------ #
def test_carregar_assets_e_idempotente(monkeypatch):
    chamadas = []
    monkeypatch.setattr(pygame.image, 'load', lambda *a: chamadas.append(a))
    assert carregar_assets() is ASSETS
    assert chamadas == []


def test_espelhar_inverte_na_horizontal():
    normal = carregar_imagem(Imagem('player/player1.png', (144, 144)))
    espelhada = carregar_imagem(Imagem('player/player1.png', (144, 144), espelhar=True))
    assert espelhada.get_at((0, 50)) == normal.get_at((143, 50))
    assert espelhada.get_at((143, 70)) == normal.get_at((0, 70))


def test_imagem_opaca_nao_tem_alpha_por_pixel():
    opaca = carregar_imagem(Imagem('ranking.jpg', (32, 18), alpha=False))
    assert not opaca.get_flags() & pygame.SRCALPHA
    assert opaca.get_size() == (32, 18)


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


def test_falha_e_logada_uma_vez_por_arquivo(sem_falhas_logadas, capsys):
    img = Imagem('nao/existe.png')
    for _ in range(3):
        assert carregar_imagem(img).get_size() == modulo_assets.TAMANHO_PLACEHOLDER
    saida = capsys.readouterr().out
    assert saida.count('[Assets]') == 1 and 'existe.png' in saida


def test_placeholder_respeita_espelhar(sem_falhas_logadas):
    assert carregar_imagem(Imagem('nao/existe.png', (10, 4), espelhar=True)).get_size() == (10, 4)


def test_arquivo_ilegivel_vira_placeholder(sem_falhas_logadas, monkeypatch, tmp_path, capsys):
    (tmp_path / 'quebrada.png').write_bytes(b'isto nao e um png')
    monkeypatch.setattr(modulo_assets, 'path', lambda *partes: str(tmp_path / partes[-1]))
    superficie = carregar_imagem(Imagem('quebrada.png', (8, 8)))
    assert superficie.get_at((4, 4))[:3] == modulo_assets.COR_PLACEHOLDER
    assert 'quebrada.png' in capsys.readouterr().out


# ------------------------------------------------------------------ #
# Mapas sob demanda (roteiro D2)
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


def test_assets_maps_e_sob_demanda_com_as_chaves_do_manifesto():
    assert isinstance(ASSETS['maps'], MapasSobDemanda)
    assert list(ASSETS['maps']) == list(MANIFESTO['maps'])


def test_consultar_chaves_nao_decodifica(decodificados):
    mapas = _mapas()
    assert '0' in mapas and '9' not in mapas and 0 not in mapas
    assert len(mapas) == 4 and list(mapas) == ['0', '1', '2', '3']
    assert mapas.get('9') is None
    assert decodificados == [] and mapas.carregados == []


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


def test_limite_um_guarda_so_o_atual(decodificados):
    mapas = _mapas(limite=1)
    mapas['0'], mapas['1']
    assert mapas.carregados == ['1']


@pytest.mark.parametrize('limite', [0, -1])
def test_limite_invalido_e_erro(limite):
    with pytest.raises(ValueError):
        _mapas(limite)


def test_chave_inexistente_e_keyerror(decodificados):
    with pytest.raises(KeyError):
        _mapas()['9']
    assert decodificados == []


def test_mapa_ausente_vira_placeholder(sem_falhas_logadas):
    mapas = MapasSobDemanda({'0': Imagem('map/nao_existe.jpg', alpha=False)})
    assert mapas['0'].get_size() == modulo_assets.TAMANHO_PLACEHOLDER


def test_partida_decodifica_so_o_mapa_usado(novo_jogo, monkeypatch):
    from helpers import voltar_ao_menu
    mapas = MapasSobDemanda(MANIFESTO['maps'])
    monkeypatch.setitem(ASSETS, 'maps', mapas)
    voltar_ao_menu(novo_jogo)
    novo_jogo.iniciar_novo_jogo()
    assert mapas.carregados == ['0']
    assert novo_jogo.existe_proxima_fase() and mapas.carregados == ['0']

    sm = novo_jogo.stage_manager
    sm._trocar_dados_fase()
    assert novo_jogo.sessao.fase_atual == 1 and mapas.carregados == ['0', '1']
    sm._trocar_dados_fase()
    assert mapas.carregados == ['1', '2']
    fundo = novo_jogo.mapa.background
    assert fundo is mapas['2']
    assert (novo_jogo.mapa.largura_mapa_pixels, novo_jogo.mapa.altura_mapa_pixels) == fundo.get_size()


# ------------------------------------------------------------------ #
# Import sem efeito colateral (roteiro D3)
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
        'import importlib, sys, pygame\n'
        'sys.path.insert(0, "tests")\n'
        'from unit.test_imports import MODULOS\n'
        'for m in MODULOS: importlib.import_module(m)\n'
        'from source.feats.assets import ASSETS\n'
        'print(len(MODULOS), pygame.get_init(), pygame.display.get_init(), len(ASSETS))')
    quantos, pygame_iniciado, display_iniciado, assets = saida.split()
    assert int(quantos) > 200
    assert (pygame_iniciado, display_iniciado, assets) == ('False', 'False', '0')


def test_carregar_sem_janela_abre_uma_oculta():
    saida = rodar_em_processo_novo(
        'import pygame\n'
        'from source.feats.assets import ASSETS, carregar_assets\n'
        'carregar_assets()\n'
        'tela = pygame.display.get_surface()\n'
        'print(tela.get_size(), bool(pygame.display.get_window_size()), len(ASSETS) > 0)')
    assert saida == '(1280, 720) True True'


def test_carregar_com_janela_aberta_usa_a_janela_do_jogo():
    # O caminho do main.py: a janela vem primeiro e carregar_assets não abre outra.
    saida = rodar_em_processo_novo(
        'import pygame\n'
        'pygame.init()\n'
        'tela = pygame.display.set_mode((640, 360))\n'
        'from source.feats.assets import ASSETS, carregar_assets\n'
        'carregar_assets()\n'
        'print(pygame.display.get_surface() is tela, len(ASSETS) > 0)')
    assert saida == 'True True'


def test_driver_sem_modo_oculto_abre_janela_comum(monkeypatch):
    chamadas = []

    def set_mode(tamanho, flags=0):
        chamadas.append(flags)
        if flags & pygame.HIDDEN:
            raise pygame.error('sem modo oculto')
    monkeypatch.setattr(pygame.display, 'get_surface', lambda: None)
    monkeypatch.setattr(pygame.display, 'set_mode', set_mode)
    modulo_assets._preparar_display()
    assert chamadas == [pygame.HIDDEN, 0]


def test_preparar_display_nao_troca_a_janela_existente(monkeypatch):
    monkeypatch.setattr(pygame.display, 'set_mode', lambda *a: pytest.fail('abriu outra janela'))
    modulo_assets._preparar_display()
