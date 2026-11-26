import pygame

from .desenhado import ProjetilDesenhado, brilho_aditivo, pintar_perfil


class M50(ProjetilDesenhado):
    """Tiro do rifle do Jackal sniper: um espinho de cristal magenta como o da Needler, só que mais grosso e
    bem mais brilhante (núcleo branco, rastro fino e um halo forte perto da ponta que cintila em 3 quadros).
    O acerto é o círculo do `tamanho`."""
    QUADROS = 3
    PERIODO_MS = 55
    BRILHO = (1.0, 1.3, 0.8)
    COR_HALO = (220, 50, 200)
    COR_RASTRO = (230, 70, 255)
    # (cor, alpha, escala do raio), de fora para dentro
    CAMADAS = (((215, 60, 255), 70, 2.1), ((240, 100, 255), 130, 1.45), ((255, 120, 235), 245, 1.0),
               ((255, 200, 250), 255, 0.6), ((255, 255, 255), 255, 0.3))
    # proporções do tamanho: meia espessura máxima, ponta e cauda em volta do ponto de acerto, rastro
    RAIO, PONTA, CAUDA, RASTRO = 0.16, 0.8, 1.25, 2.2
    BRILHO_A_FRENTE = PONTA * 0.45

    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread,
                 fonte=None):
        super().__init__(
            posicao_inicial=posicao_inicial,
            grupos=grupos,
            game=game,
            dono=dono,
            fonte=fonte,
            sprite_key='m50',
            tamanho=tamanho,
            dano=dano,
            velocidade=velocidade,
            duracao=2500,
            direcao_custom=direcao_spread,
        )

    @classmethod
    def desenhar_corpo(cls, tamanho):
        w = min(tamanho)
        raio, ponta, cauda, rastro = w * cls.RAIO, w * cls.PONTA, w * cls.CAUDA, w * cls.RASTRO
        largura = round(2 * (rastro + 4))
        altura = round(2 * raio * 2.2) + 6
        surf = pygame.Surface((largura, altura), pygame.SRCALPHA)
        cx, cy = largura / 2, altura / 2
        inicio = cx - rastro                    # rastro fino, apagando para trás
        for i in range(20):
            t = i / 19
            x = inicio + (cx - cauda - inicio) * t
            pygame.draw.line(surf, (*cls.COR_RASTRO, round(15 + 110 * t * t)), (x, cy - 1), (x, cy + 1), 2)
        # O espinho: largo no terço da frente, fino na cauda, agudo na ponta
        pintar_perfil(surf, cx - cauda, cx + ponta, cy,
                      lambda t: raio * (0.18 + 0.82 * t ** 0.7) * min(1.0, (1 - t) * 3.2), cls.CAMADAS, passos=90)
        return surf

    @classmethod
    def desenhar_brilho(cls, tamanho, quadro):
        brilho = cls.BRILHO[quadro % len(cls.BRILHO)]
        raio = min(tamanho) * cls.RAIO
        imagem = brilho_aditivo(raio * 2.8 * brilho, cls.COR_HALO, forca=min(1.0, 0.75 * brilho))
        centro = (imagem.get_width() / 2, imagem.get_height() / 2)
        pygame.draw.circle(imagem, (255, 235, 255), centro, max(1.0, raio * 0.45 * brilho))
        return imagem
