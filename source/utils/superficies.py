"""Superfícies e máscaras reaproveitadas entre frames (roteiro C3: nada de alocar por frame).

- `mascara_de(superficie)`: máscara em cache por superfície. Só para superfícies que não mudam
  de pixel (frames de sprite em cache); `set_alpha` não afeta a máscara.
- `camada_alpha(tela, caixa)`: buffer SRCALPHA do tamanho da tela, para efeitos translúcidos
  desenhados em coordenadas de tela. Substitui a `Surface` temporária criada a cada `draw`.
- `rascunho(tamanho)`: SRCALPHA local reaproveitada por tamanho, para quem precisa desenhar em
  coordenadas locais (ex.: `draw.polygon`, que muda pixels da aresta quando recortado).
- `SUPERFICIE_VAZIA`: imagem 1×1 transparente para sprites que se desenham sozinhos (`draw`
  próprio) e só precisam de `image`/`rect`. Compartilhada: não desenhe nela.
"""
import weakref

import pygame

# Chave fraca: a superfície que sai de uso some do cache junto com a máscara.
_MASCARAS = weakref.WeakKeyDictionary()
_CAMADAS = {}   # tamanho da tela -> buffer SRCALPHA
_RASCUNHOS = {}  # tamanho -> SRCALPHA

SUPERFICIE_VAZIA = pygame.Surface((1, 1), pygame.SRCALPHA)


def mascara_de(superficie):
    """Máscara de colisão de `superficie`, criada uma vez. A máscara é compartilhada:
    não a modifique."""
    mascara = _MASCARAS.get(superficie)
    if mascara is None:
        mascara = _MASCARAS[superficie] = pygame.mask.from_surface(superficie)
    return mascara


def camada_alpha(tela, caixa):
    """Devolve `(camada, area)` para desenhar um efeito translúcido em coordenadas de tela.

    `area` é `caixa` recortada pela tela; a camada vem limpa e com clip nela. Depois de
    desenhar, cole com `tela.blit(camada, area.topleft, area)`, antes de pedir outra camada
    (o buffer é um só por tamanho de tela). Efeito todo fora da tela: `(None, area_vazia)`.
    """
    area = pygame.Rect(caixa).clip(tela.get_rect())
    if not area.width or not area.height:
        return None, area
    tamanho = tela.get_size()
    camada = _CAMADAS.get(tamanho)
    if camada is None:
        camada = _CAMADAS[tamanho] = pygame.Surface(tamanho, pygame.SRCALPHA)
    camada.set_clip(area)
    camada.fill((0, 0, 0, 0), area)
    return camada, area


def rascunho(tamanho):
    """SRCALPHA transparente de `tamanho`, reaproveitada entre frames (uma por tamanho).
    Só para tamanhos de um conjunto pequeno e fixo (ex.: raio de preset): o cache não esvazia.
    Desenhe e cole antes de pedir outro rascunho do mesmo tamanho."""
    tamanho = (int(tamanho[0]), int(tamanho[1]))
    if tamanho[0] <= 0 or tamanho[1] <= 0:
        raise ValueError(f'tamanho de rascunho inválido: {tamanho}')
    superficie = _RASCUNHOS.get(tamanho)
    if superficie is None:
        superficie = _RASCUNHOS[tamanho] = pygame.Surface(tamanho, pygame.SRCALPHA)
    else:
        superficie.fill((0, 0, 0, 0))
    return superficie
