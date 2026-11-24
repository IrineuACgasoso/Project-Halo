"""Distorção do ambiente em volta de um inimigo camuflado (como a camuflagem ativa do Halo).

O cenário que já está na tela, atrás da silhueta dele, é recolado em faixas horizontais ondulando
alguns pixels, com um véu claro bem fraco por cima (em fundo liso só a ondulação não aparece).
É o que denuncia quem não pode ser mirado. Tudo em superfícies reaproveitadas: zero alocação por
frame (`rascunho`, `silhueta_de`)."""
import math

import pygame

from source.systems.gameclock import relogio
from source.utils.superficies import rascunho, silhueta_de

FAIXA = 8             # altura de cada faixa (px)
AMPLITUDE = 9         # deslocamento máximo de uma faixa (px)
PERIODO_MS = 900      # uma ondulação completa no tempo
ONDULACAO = 0.11      # radianos por px de altura
VEU_COR = (190, 225, 255)
VEU_ALPHA = (18, 42)  # o véu pulsa entre estes valores
_BRANCO = (255, 255, 255)


def desenhar_distorcao(tela, inimigo, deslocamento):
    """Chamado pelo Renderer depois dos sprites, para todo inimigo com a skill ativa."""
    forca = inimigo.invisibilidade.intensidade
    if forca <= 0:
        return
    quadro = inimigo.quadro_original
    largura, altura = quadro.get_size()
    x = int(inimigo.rect.x - deslocamento.x)
    y = int(inimigo.rect.y - deslocamento.y)
    if not tela.get_rect().colliderect(x, y, largura, altura):
        return

    camada = rascunho((largura, altura))
    fase = relogio.agora() * 2 * math.pi / PERIODO_MS
    for topo in range(0, altura, FAIXA):
        dx = round(AMPLITUDE * forca * math.sin(fase + topo * ONDULACAO))
        camada.blit(tela, (0, topo), (x + dx, y + topo, largura, FAIXA))
    camada.blit(silhueta_de(quadro, _BRANCO), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)   # recorta
    tela.blit(camada, (x, y))

    veu = silhueta_de(quadro, VEU_COR)
    minimo, maximo = VEU_ALPHA
    veu.set_alpha(round(forca * (minimo + (maximo - minimo) * (0.5 + 0.5 * math.sin(fase * 0.7)))))
    tela.blit(veu, (x, y))
