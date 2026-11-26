"""Desenho da lentidão (sistema de status), padrão de todo alvo lento, jogador ou inimigo: o corpo
fica levemente azulado e os pés ganham a animação de "câmera lenta" dos quadrinhos (uma poça de
gosma azul, nuvenzinhas que boiam devagar e rabiscos em espiral subindo dos lados).

Sem alocação por frame: os quadros dos pés (por largura), as silhuetas e as caixas do corpo ficam em
cache. Não usa `random` (o desenho não pode mexer na simulação)."""
import math
import weakref

import pygame

from source.systems.gameclock import relogio
from source.utils.superficies import silhueta_de

QUADROS = 8
MS_POR_QUADRO = 130                     # devagar de propósito: é o efeito da lentidão
COR_TINTA = (10, 42, 105)                 # somada ao corpo (BLEND_RGB_ADD): azulado leve
LARGURAS = (40, 64, 96, 140)            # tamanhos dos pés em cache
FRACAO_LARGURA = 0.9                   # largura do efeito, em fração da largura do corpo
COR_POCA = (80, 160, 255, 95)
COR_POCA_BORDA = (150, 205, 255, 120)
COR_NUVEM = (215, 232, 255, 170)
COR_RABISCO = (150, 205, 255, 210)

_QUADROS = {}                           # largura -> [Surface]
_CORPOS = weakref.WeakKeyDictionary()   # quadro do alvo -> (largura do efeito, retângulo do corpo)


def quadros_dos_pes(largura):
    """Os QUADROS dos pés lentos com `largura` px, desenhados uma vez (a animação fecha o ciclo)."""
    quadros = _QUADROS.get(largura)
    if quadros is None:
        altura = round(largura * 0.5)
        quadros = _QUADROS[largura] = []
        for q in range(QUADROS):
            fase = 2 * math.pi * q / QUADROS
            surf = pygame.Surface((largura, altura), pygame.SRCALPHA)
            # Poça de gosma no chão (respira um pouco)
            larg_poca = largura * (0.86 + 0.06 * math.sin(fase))
            poca = pygame.Rect(0, 0, larg_poca, altura * 0.34)
            poca.midbottom = (largura / 2, altura - 1)
            pygame.draw.ellipse(surf, COR_POCA, poca)
            pygame.draw.ellipse(surf, COR_POCA_BORDA, poca, 2)
            # Nuvenzinhas boiando sobre a poça
            for i, fx in enumerate((0.25, 0.5, 0.75)):
                dy = math.sin(fase + i * 2.1) * altura * 0.08
                r = max(2, round(largura * (0.065 + 0.015 * math.sin(fase * 2 + i))))
                pygame.draw.circle(surf, COR_NUVEM, (largura * fx, altura * 0.62 + dy), r)
            # Rabiscos em espiral que sobem e somem dos dois lados
            for lado, fx in ((-1, 0.1), (1, 0.9)):
                subida = ((q / QUADROS) + (0.5 if lado > 0 else 0)) % 1.0
                cx, cy = largura * fx, altura * (0.75 - 0.55 * subida)
                r = max(3, round(largura * 0.06))
                caixa = pygame.Rect(0, 0, r * 2, r * 2)
                caixa.center = (cx, cy)
                cor = (*COR_RABISCO[:3], round(COR_RABISCO[3] * (1 - subida)))
                inicio = fase * lado
                pygame.draw.arc(surf, cor, caixa, inicio, inicio + math.pi * 1.4, 2)
            quadros.append(surf)
    return quadros


def _corpo(quadro):
    """Largura do efeito e retângulo dos pixels visíveis do `quadro`, calculados uma vez."""
    corpo = _CORPOS.get(quadro)
    if corpo is None:
        caixa = quadro.get_bounding_rect()
        largura = min(LARGURAS, key=lambda opcao: abs(opcao - caixa.width * FRACAO_LARGURA))
        corpo = _CORPOS[quadro] = (largura, caixa)
    return corpo


def desenhar_lentidao(tela, alvo, deslocamento):
    """Chamado pelo Renderer depois dos sprites, para quem está lento. Camuflado não mostra (o efeito
    denunciaria quem não pode ser mirado); no ar, só o corpo fica azulado."""
    if getattr(alvo, 'invisivel', False):
        return
    if getattr(alvo, 'in_veicule', False):
        alvo = alvo.veiculo_atual
    quadro = getattr(alvo, 'quadro_original', None) or alvo.image
    x = round(alvo.rect.centerx - quadro.get_width() / 2 - deslocamento.x)
    y = round(alvo.rect.centery - quadro.get_height() / 2 - deslocamento.y)
    if not tela.get_rect().colliderect(x, y, quadro.get_width(), quadro.get_height()):
        return
    tela.blit(silhueta_de(quadro, COR_TINTA), (x, y), special_flags=pygame.BLEND_RGB_ADD)
    if getattr(alvo, 'altura_z', 0) > 0:
        return
    largura, caixa = _corpo(quadro)
    pes = quadros_dos_pes(largura)
    imagem = pes[int(relogio.agora() // MS_POR_QUADRO) % QUADROS]
    tela.blit(imagem, (x + caixa.centerx - largura / 2, y + caixa.bottom - imagem.get_height() * 0.8))


def preparar_lentidao(quadros):
    """Pinta já a tinta e os pés de cada quadro de `quadros` (no spawn de quem deixa alguém lento:
    o jogador lento não pode criar imagem no meio da luta)."""
    for quadro in quadros:
        largura, _ = _corpo(quadro)
        silhueta_de(quadro, COR_TINTA)
        quadros_dos_pes(largura)
