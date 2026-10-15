"""Carregamento de fontes com cache e fallback, sem depender do diretório atual."""
import os
from functools import lru_cache

import pygame

from source.utils.paths import path


@lru_cache(maxsize=None)
def carregar_fonte(caminho_relativo, tamanho, fallback_sys='Consolas', fallback_tamanho=None, bold=True):
    """Devolve pygame.font.Font do arquivo (via path(), compatível com PyInstaller).
    Se o arquivo não existir/falhar, cai para SysFont. Resultado fica em cache:
    antes cada TelaDeUpgrade/OpcaoDeUpgrade relia o .ttf do disco a cada level-up."""
    try:
        caminho = path(*caminho_relativo) if isinstance(caminho_relativo, (tuple, list)) else path(caminho_relativo)
        if os.path.exists(caminho):
            return pygame.font.Font(caminho, tamanho)
    except (pygame.error, OSError):
        pass
    return pygame.font.SysFont(fallback_sys, fallback_tamanho or tamanho, bold=bold)
