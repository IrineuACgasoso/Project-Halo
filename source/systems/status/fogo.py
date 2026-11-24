"""Desenho da queimadura (sistema de status): o corpo pisca entre laranja e amarelo, com chamas por cima.

Vale para o jogador e para todo inimigo. Sem alocação por frame: quadros de chama, silhuetas e caixas
do corpo ficam em cache. Não usa `random` (o desenho não pode mexer na simulação).
"""
import math
import weakref

import pygame

from source.systems.gameclock import relogio
from source.utils.superficies import mascara_de, silhueta_de

QUADROS = 8
MS_POR_QUADRO = 65
CAMADAS = (((215, 45, 10, 170), 1.0), ((255, 115, 15, 215), 0.78), ((255, 200, 45, 235), 0.54),
           ((255, 250, 190, 245), 0.28))            # (cor, escala), de fora para dentro
LARGURAS = (16, 22, 30, 42)                         # tamanhos de chama em cache
FRACAO_LARGURA = 0.36                               # largura da chama, em fração da largura do corpo

# Base de cada chama na caixa do corpo (x, y em fração), do fundo para a frente
PONTOS = ((0.50, 0.30), (0.22, 0.52), (0.78, 0.50), (0.48, 0.68), (0.16, 0.88), (0.84, 0.86), (0.50, 0.98))
CHAMAS_POR_PX = 1 / 20                              # nº de chamas pela largura do corpo
MINIMO_CHAMAS = 3

# Cores somadas ao corpo (BLEND_RGB_ADD: bem mais barato que um blit com alpha), num vaivém do laranja
# ao amarelo
CORES_PISQUE = ((125, 35, 0), (85, 30, 0), (60, 35, 0), (95, 70, 8), (140, 110, 18))
MS_POR_COR = 55

_QUADROS = {}                                       # largura -> [Surface]
_BASES = weakref.WeakKeyDictionary()                # quadro do alvo -> (largura da chama, [base de cada uma])


def quadros_da_chama(largura):
    """Os QUADROS de uma chama com `largura` px, desenhados uma vez (a animação fecha o ciclo)."""
    quadros = _QUADROS.get(largura)
    if quadros is None:
        altura = round(largura * 1.7)
        quadros = _QUADROS[largura] = []
        for q in range(QUADROS):
            fase = 2 * math.pi * q / QUADROS
            surf = pygame.Surface((largura, altura), pygame.SRCALPHA)
            for cor, escala in CAMADAS:
                corpo = altura * escala * (0.86 + 0.14 * math.sin(fase))
                meia = largura / 2 * escala * 0.92
                esquerda, direita = [], []
                for i in range(11):                  # da base (t=0) à ponta (t=1), com a ponta balançando
                    t = i / 10
                    largo = meia * math.sin(math.pi * t ** 0.55)     # gota: base redonda, ponta fina
                    x = largura / 2 + math.sin(fase + t * 4) * largura * 0.13 * t
                    y = altura - 1 - corpo * t
                    esquerda.append((x - largo, y))
                    direita.append((x + largo, y))
                pygame.draw.polygon(surf, cor, esquerda + direita[::-1])
            quadros.append(surf.convert_alpha())
    return quadros


def _bases_das_chamas(quadro):
    """Largura e bases das chamas no `quadro`, calculadas uma vez: sempre sobre o corpo (um ponto que
    cai no vazio é puxado para o centro da massa)."""
    bases = _BASES.get(quadro)
    if bases is None:
        corpo, mascara = quadro.get_bounding_rect(), mascara_de(quadro)
        largura = min(LARGURAS, key=lambda opcao: abs(opcao - corpo.width * FRACAO_LARGURA))
        quantas = max(MINIMO_CHAMAS, min(len(PONTOS), round(corpo.width * CHAMAS_POR_PX)))
        centro = pygame.math.Vector2(mascara.centroid())
        pontos = []
        for fx, fy in PONTOS[-quantas:]:            # com poucas, ficam as de baixo
            alvo = pygame.math.Vector2(corpo.x + (corpo.width - 1) * fx, corpo.y + (corpo.height - 1) * fy)
            pontos.append(next((p for p in (alvo.lerp(centro, i / 10) for i in range(11))
                                if mascara.get_at((int(p.x), int(p.y)))), centro))
        bases = _BASES[quadro] = (largura, pontos)
    return bases


def desenhar_fogo(tela, alvo, deslocamento):
    """Chamado pelo Renderer depois dos sprites, para quem está com queimadura. Camuflado não queima à
    vista (o fogo denunciaria quem não pode ser mirado)."""
    if getattr(alvo, 'invisivel', False):
        return
    if getattr(alvo, 'in_veicule', False):
        alvo = alvo.veiculo_atual           # o veículo cobre o jogador e é ele quem leva o dano
    quadro = getattr(alvo, 'quadro_original', None) or alvo.image
    x = round(alvo.rect.centerx - quadro.get_width() / 2 - deslocamento.x)
    y = round(alvo.rect.centery - quadro.get_height() / 2 - deslocamento.y)
    if not tela.get_rect().colliderect(x, y, quadro.get_width(), quadro.get_height()):
        return
    agora = relogio.agora()
    volta = 2 * len(CORES_PISQUE) - 2
    passo = int(agora // MS_POR_COR) % volta
    silhueta = silhueta_de(quadro, CORES_PISQUE[min(passo, volta - passo)])
    tela.blit(silhueta, (x, y), special_flags=pygame.BLEND_RGB_ADD)

    largura, bases = _bases_das_chamas(quadro)
    chamas = quadros_da_chama(largura)
    subida = chamas[0].get_height() * 0.8           # a base da chama afunda um pouco no corpo
    for i, base in enumerate(bases):
        chama = chamas[(int(agora // MS_POR_QUADRO) + i * 3) % QUADROS]
        tela.blit(chama, (x + base.x - largura / 2, y + base.y - subida))
