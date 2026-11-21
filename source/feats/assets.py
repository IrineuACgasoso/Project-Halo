"""ASSETS: as imagens do jogo, montadas a partir de `data/manifesto_assets.py` (roteiro D1).

O import não tem efeito colateral (roteiro D3): `ASSETS` nasce vazio e só é preenchido por
`carregar_assets()`, que o `main.py`, o `conftest` e o `tools/perf.py` chamam. Os fundos das
fases são decodificados sob demanda (`MapasSobDemanda`, D2).
"""
from collections import OrderedDict
from collections.abc import Mapping

import pygame
from source.windows.settings import *
from source.windows.settings import altura_tela, largura_tela

# `path` agora vive em source/utils/paths.py (evita import circular); reexportado aqui.
from source.utils.paths import path  # noqa: E402,F401
from source.data.manifesto_assets import MANIFESTO, Imagem

COR_PLACEHOLDER = (255, 0, 255)
TAMANHO_PLACEHOLDER = (64, 64)   # para imagem sem escala no manifesto

ASSETS = {}
_arquivos_com_falha = set()      # cada arquivo ausente é logado uma vez só


def _preparar_display():
    """`convert`/`convert_alpha` exigem uma janela. Quem já abriu a sua (o `main.py`) não ganha
    outra; sem janela (testes, ferramentas), abre uma oculta."""
    if not pygame.get_init():
        pygame.init()
    if pygame.display.get_surface() is not None:
        return
    try:
        pygame.display.set_mode((largura_tela, altura_tela), pygame.HIDDEN)
    except pygame.error:
        pygame.display.set_mode((largura_tela, altura_tela))   # driver sem modo oculto


def _placeholder(imagem):
    superficie = pygame.Surface(imagem.escala or TAMANHO_PLACEHOLDER, pygame.SRCALPHA)
    superficie.fill(COR_PLACEHOLDER)
    return superficie.convert_alpha() if imagem.alpha else superficie.convert()


def carregar_imagem(imagem):
    """Surface de uma `Imagem` do manifesto. Arquivo ausente ou ilegível vira um placeholder
    magenta do tamanho pedido (e um aviso no console), em vez de derrubar o jogo."""
    caminho = path('assets', 'img', *imagem.arquivo.split('/'))
    try:
        bruta = pygame.image.load(caminho)
    except (FileNotFoundError, pygame.error) as erro:
        if imagem.arquivo not in _arquivos_com_falha:
            _arquivos_com_falha.add(imagem.arquivo)
            print(f'[Assets] Imagem ausente ou ilegível, usando placeholder: {caminho} ({erro})')
        superficie = _placeholder(imagem)
    else:
        superficie = bruta.convert_alpha() if imagem.alpha else bruta.convert()
        if imagem.escala:
            superficie = pygame.transform.scale(superficie, imagem.escala)
    if imagem.espelhar:
        superficie = pygame.transform.flip(superficie, True, False)
    return superficie


class MapasSobDemanda(Mapping):
    """`ASSETS['maps']` (roteiro D2): o fundo de uma fase só é decodificado no 1º acesso, e só os
    `limite` mais recentes ficam guardados (cada fundo grande ocupa ~56 MB).

    `in`, `len` e a iteração consultam o manifesto, sem decodificar nada. `values()`/`items()`
    decodificam todos (um por vez, respeitando o limite): evite fora de teste.
    """

    def __init__(self, manifesto, limite=2):
        if limite < 1:
            raise ValueError(f'limite precisa ser >= 1 (veio {limite})')
        self._manifesto = dict(manifesto)
        self._limite = limite
        self._cache = OrderedDict()

    def __getitem__(self, chave):
        if chave in self._cache:
            self._cache.move_to_end(chave)
            return self._cache[chave]
        superficie = carregar_imagem(self._manifesto[chave])   # chave inválida: KeyError
        self._cache[chave] = superficie
        while len(self._cache) > self._limite:
            self._cache.popitem(last=False)
        return superficie

    def __contains__(self, chave):
        return chave in self._manifesto

    def __iter__(self):
        return iter(self._manifesto)

    def __len__(self):
        return len(self._manifesto)

    @property
    def carregados(self):
        """Chaves decodificadas, da menos para a mais recente."""
        return list(self._cache)


def _montar(no):
    if isinstance(no, Imagem):
        return carregar_imagem(no)
    if isinstance(no, list):
        return [_montar(x) for x in no]
    return {chave: _montar(filho) for chave, filho in no.items()}


def carregar_assets():
    """Preenche `ASSETS` (sempre o mesmo dict) a partir do manifesto. Idempotente.
    Inicia o pygame e abre uma janela oculta se ainda não houver janela (`_preparar_display`).
    Os fundos das fases ficam sob demanda (`MapasSobDemanda`)."""
    if not ASSETS:
        _preparar_display()
        ASSETS.update({chave: MapasSobDemanda(no) if chave == 'maps' else _montar(no)
                       for chave, no in MANIFESTO.items()})
    return ASSETS
