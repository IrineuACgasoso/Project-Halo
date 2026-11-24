"""O corpo do Scarab em camadas: casco, canhão e cada pata são recortes separados (`recortes.py`).

Assim cada pata mostra o próprio estado (inteira ou danificada, no chão ou erguida) e o canhão gira
sozinho, sem um sprite de 1024×1024 por combinação. Três poses: 'em_pe', 'caido' (núcleo exposto, com o
canhão pintado no casco) e 'sentado' (body stomp). Três variantes: 'default', 'damaged' e 'broken'.

Nada é alocado por frame: os espelhos e as máscaras são feitos 1× (no primeiro Scarab)."""
from functools import lru_cache

import pygame

from source.feats.assets import ASSETS
from source.utils.superficies import mascara_de, silhueta_de

from .config import PATAS_VULNERAVEIS, PIVO_TORRETA, TAMANHO, TORRETA_SENTADO_DY, VARIANTES
from .recortes import CANTOS

POSES = ('em_pe', 'caido', 'sentado')
LADOS = ('left', 'right')


def espelhar_x(x, largura=0):
    """O x da borda esquerda, na arte virada para a direita, de algo que estava em `x` com `largura`."""
    return TAMANHO - x - largura


def _acelerar(imagem):
    """RLE: o alpha dos recortes é 0 ou 255, e assim o blit só copia o que é opaco (~10× mais rápido)."""
    imagem.set_alpha(255, pygame.RLEACCEL)
    return imagem


@lru_cache(maxsize=None)
def recorte(variante, nome, lado):
    """(Surface, x, y) do recorte `nome` na arte de 1024×1024 virada para `lado`."""
    imagem = ASSETS['enemies']['scarab_partes'][variante][nome]
    x, y = CANTOS[nome]
    if lado == 'right':
        x = espelhar_x(x, imagem.get_width())
        imagem = pygame.transform.flip(imagem, True, False)
    return _acelerar(imagem), x, y


@lru_cache(maxsize=None)
def recorte_torreta(variante, nome, lado, mira):
    """(Surface, x, y) do canhão: `lado` é o do casco; `mira`, o lado para onde o cano aponta."""
    imagem = ASSETS['enemies']['scarab_partes'][variante][nome]
    x, y = CANTOS[nome]
    desvio = x - PIVO_TORRETA                   # do pivô à borda esquerda, com o cano para a direita
    if mira == 'left':
        desvio = -desvio - imagem.get_width()
        imagem = pygame.transform.flip(imagem, True, False)
    return _acelerar(imagem), pivo_torreta(lado) + desvio, y


def pivo_torreta(lado):
    return PIVO_TORRETA if lado == 'left' else espelhar_x(PIVO_TORRETA)


def nome_da_pata(pose, pata, erguida, danificada):
    return f'{pose}_{pata}' + ('_alta' if erguida and pose == 'em_pe' else '') + ('_dan' if danificada else '')


@lru_cache(maxsize=None)
def mascara(pose, lado):
    """A silhueta inteira (patas e canhão inclusive) da pose, no tamanho do rect: o que os tiros acertam."""
    nomes = [f'{pose}_corpo', *(f'{pose}_{p}' for p in PATAS_VULNERAVEIS)]
    if pose == 'em_pe':
        nomes.append('em_pe_oculta')
    total = pygame.Mask((TAMANHO, TAMANHO))
    for nome in nomes:
        imagem, x, y = recorte('default', nome, lado)
        total.draw(mascara_de(imagem), (x, y))
    if pose != 'caido':
        imagem, x, y = recorte_torreta('default', 'em_pe_torreta', lado, lado)
        total.draw(mascara_de(imagem), (x, y + (TORRETA_SENTADO_DY if pose == 'sentado' else 0)))
    return total


def preparar(cor_brilho):
    """Espelhos, máscaras e o brilho das patas: tudo no spawn, nada no meio da luta."""
    for variante in VARIANTES:
        for nome in CANTOS:
            for lado in LADOS:
                recorte(variante, nome, lado)
        for nome in ('em_pe_torreta', 'em_pe_torreta_b'):
            for lado in LADOS:
                for mira in LADOS:
                    recorte_torreta(variante, nome, lado, mira)
    for pose in POSES:
        for lado in LADOS:
            mascara(pose, lado)
    for pata in PATAS_VULNERAVEIS:
        for lado in LADOS:
            silhueta_de(recorte('default', f'em_pe_{pata}', lado)[0], cor_brilho)


def desenhar(tela, x, y, scarab):
    """Desenha todas as camadas com o canto da arte em (x, y) da tela."""
    variante, lado, pose = scarab.variante_arte, scarab.animador.lado, scarab.pose
    sobe = round(scarab.impulso_y)

    def colar(nome, dy=0):
        imagem, rx, ry = recorte(variante, nome, lado)
        tela.blit(imagem, (x + rx, y + ry - dy))

    def colar_pata(pata):
        dy = sobe if pata.nome == 'centro' else 0      # a central está presa na frente do casco
        colar(nome_da_pata(pose, pata.nome, pata.erguida, pata.danificada), dy + round(pata.extra_y))

    patas = scarab.patas
    if pose == 'em_pe':
        colar('em_pe_oculta_alta' if patas['oculta'].erguida else 'em_pe_oculta', sobe)
    colar_pata(patas['frente'])
    colar_pata(patas['tras'])
    colar(f'{pose}_corpo', sobe)
    if pose != 'caido':
        nome = 'em_pe_torreta_b' if scarab.torreta_recuada else 'em_pe_torreta'
        imagem, rx, ry = recorte_torreta(variante, nome, lado, scarab.mira_torreta)
        tela.blit(imagem, (x + rx, y + ry - sobe + scarab.torreta_dy))
    colar_pata(patas['centro'])
