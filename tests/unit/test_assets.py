"""Assets: equivalência com o carregamento antigo (roteiro D1).

`tests/golden/assets.json` foi gravado com as 251 linhas literais, ANTES da troca pelo manifesto:
cada superfície vira 'LxA bits alpha|opaco crc32-dos-pixels-RGBA'.
Regravar (só quando a arte muda de propósito):
    .venv\\Scripts\\python.exe -m pytest tests/unit/test_assets.py --atualizar-golden
"""
import json
import os
import zlib

import pygame
import pytest

from source.data.manifesto_assets import MANIFESTO, Imagem, folhas, numerados, quadros
from source.feats import assets as modulo_assets
from source.feats.assets import ASSETS, carregar_assets, carregar_imagem
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
