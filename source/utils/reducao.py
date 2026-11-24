"""Redução do mundo para a tela (zoom da câmera), sem alocar por frame.

`transform.scale` (vizinho mais próximo) e não `smoothscale`: de 2276×1280 para 1280×720 custa ~2 ms
contra ~7 ms (mesmo com 4 threads), e na arte do jogo a diferença mal aparece."""
import pygame

_mundos = {}      # tamanho -> Surface em que o mundo é desenhado


def superficie_do_mundo(tamanho, destino):
    """Superfície opaca de `tamanho`, no formato de `destino`, reaproveitada entre frames."""
    mundo = _mundos.get(tamanho)
    if mundo is None:
        _mundos.clear()       # só uma por vez: o tamanho muda quando o zoom alvo muda
        mundo = _mundos[tamanho] = pygame.Surface(tamanho, 0, destino)
    return mundo


def reduzir(origem, area, destino):
    """Cola em `destino` (inteiro) o canto superior esquerdo de `origem`, de tamanho `area`, reduzido."""
    if area != origem.get_size():
        origem = origem.subsurface((0, 0, *area))     # no meio da transição de zoom
    pygame.transform.scale(origem, destino.get_size(), destino)
