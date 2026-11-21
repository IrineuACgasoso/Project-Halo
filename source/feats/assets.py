"""ASSETS: as imagens do jogo, montadas a partir de `data/manifesto_assets.py` (roteiro D1).

Ainda carrega tudo no import (pygame.init + janela oculta + `carregar_assets()`): a D3 tira
esse efeito colateral.
"""
import pygame
from source.windows.settings import *

# `path` agora vive em source/utils/paths.py (evita import circular); reexportado aqui.
from source.utils.paths import path  # noqa: E402,F401
from source.data.manifesto_assets import MANIFESTO, Imagem

# Inicialização segura para o Executável
pygame.init()

# Criar uma tela oculta evita que o convert_alpha() dê erro
# e resolve o erro de "Embedded Interpreter" em alguns sistemas
try:
    screen = pygame.display.set_mode((1280, 720), pygame.HIDDEN)
except pygame.error:
    # Caso o driver de vídeo não suporte modo oculto
    screen = pygame.display.set_mode((1280, 720))

COR_PLACEHOLDER = (255, 0, 255)
TAMANHO_PLACEHOLDER = (64, 64)   # para imagem sem escala no manifesto

ASSETS = {}
_arquivos_com_falha = set()      # cada arquivo ausente é logado uma vez só


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


def _montar(no):
    if isinstance(no, Imagem):
        return carregar_imagem(no)
    if isinstance(no, list):
        return [_montar(x) for x in no]
    return {chave: _montar(filho) for chave, filho in no.items()}


def carregar_assets():
    """Preenche `ASSETS` (sempre o mesmo dict) a partir do manifesto. Idempotente."""
    if not ASSETS:
        ASSETS.update(_montar(MANIFESTO))
    return ASSETS


carregar_assets()
