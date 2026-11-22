"""Desenho da cegueira (sistema de status): fora de um círculo em volta do jogador, preto total.

Sem alocação por frame: o "buraco" (preto, com o centro transparente e um degradê curto até o
preto) fica em cache por raio, e o resto da tela é pintado com `fill` direto na tela. Os inimigos
continuam no mundo; só não aparecem. O HUD é desenhado depois, por cima.
"""
import pygame

FRACAO_DEGRADE = 0.25   # largura do degradê, em fração do raio
DEGRADE_MINIMO = 16     # px
MAX_BURACOS = 8         # raios diferentes guardados (o mais antigo sai)

_PRETO = (0, 0, 0)
_buracos = {}           # raio (int) -> Surface SRCALPHA


def _buraco(raio):
    buraco = _buracos.get(raio)
    if buraco is not None:
        return buraco
    faixa = max(DEGRADE_MINIMO, int(raio * FRACAO_DEGRADE))
    externo = raio + faixa
    buraco = pygame.Surface((2 * externo, 2 * externo), pygame.SRCALPHA)
    buraco.fill((0, 0, 0, 255))
    centro = (externo, externo)
    # draw.circle numa superfície SRCALPHA grava o alpha (não mistura): de fora para dentro,
    # cada anel mais transparente que o anterior, até o centro todo transparente.
    for r in range(externo, raio, -1):
        pygame.draw.circle(buraco, (0, 0, 0, round(255 * (r - raio) / faixa)), centro, r)
    pygame.draw.circle(buraco, (0, 0, 0, 0), centro, raio)
    if len(_buracos) >= MAX_BURACOS:
        del _buracos[next(iter(_buracos))]
    _buracos[raio] = buraco
    return buraco


def desenhar_cegueira(tela, centro, raio):
    """Escurece a tela fora do círculo de `raio` px em volta de `centro` (coordenadas de tela)."""
    buraco = _buraco(max(1, int(raio)))
    lado = buraco.get_width()
    x = round(centro[0]) - lado // 2
    y = round(centro[1]) - lado // 2
    tela.blit(buraco, (x, y))
    largura, altura = tela.get_size()
    # As 4 faixas em volta do buraco; o fill recorta pela borda da tela sozinho.
    tela.fill(_PRETO, (0, 0, largura, max(0, y)))
    tela.fill(_PRETO, (0, y + lado, largura, max(0, altura - y - lado)))
    tela.fill(_PRETO, (0, y, max(0, x), lado))
    tela.fill(_PRETO, (x + lado, y, max(0, largura - x - lado), lado))
