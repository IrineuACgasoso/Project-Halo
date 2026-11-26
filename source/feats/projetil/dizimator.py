import pygame

from .desenhado import ProjetilDesenhado, brilho_aditivo, pintar_perfil


class DizimatorBullet(ProjetilDesenhado):
    """Calibre grosso em brasa: cápsula curta e larga (ponta redonda, núcleo branco-quente) com rastro laranja
    que afina. Na ponta, um clarão que cintila (4 quadros: muda de força e a estrela de 4 pontas alterna
    entre + e x). O acerto é o círculo do `tamanho`. Jogador e Brute usam o mesmo."""
    QUADROS = 4
    PERIODO_MS = 45
    CINTILA = (1.0, 0.65, 1.25, 0.8)          # força do clarão por quadro
    COR_RASTRO = (255, 130, 25)
    COR_HALO = (255, 150, 40)
    COR_CLARAO = (255, 140, 40)
    # (cor, alpha, escala do raio), de fora para dentro
    CAMADAS = (((255, 120, 20), 255, 1.0), ((255, 180, 60), 255, 0.78),
               ((255, 230, 140), 255, 0.52), ((255, 255, 240), 255, 0.28))
    # proporções do tamanho: meia espessura, corpo à frente e atrás do ponto de acerto, rastro
    RAIO, FRENTE, TRAS, RASTRO = 0.22, 0.62, 0.55, 1.55
    BRILHO_A_FRENTE = FRENTE - RAIO * 0.6       # o clarão fica na ponta

    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread,
                 fonte=None):
        super().__init__(
            posicao_inicial=posicao_inicial,
            grupos=grupos,
            game=game,
            dono=dono,
            fonte=fonte,
            sprite_key='dizimator',
            tamanho=tamanho,
            dano=dano,
            velocidade=velocidade,
            duracao=1500,
            direcao_custom=direcao_spread,
        )

    @classmethod
    def desenhar_corpo(cls, tamanho):
        w = min(tamanho)
        raio, frente, tras, rastro = w * cls.RAIO, w * cls.FRENTE, w * cls.TRAS, w * cls.RASTRO
        largura = round(2 * (rastro + 4))
        altura = round(2 * raio * 2.1) + 4
        surf = pygame.Surface((largura, altura), pygame.SRCALPHA)
        cx, cy = largura / 2, altura / 2
        # Rastro: linhas finas e transparentes atrás do corpo, ficando mais grossas e fortes perto dele
        inicio = cx - rastro
        for i in range(24):
            t = i / 23
            x = inicio + (cx - tras - inicio) * t
            meia = max(0.5, raio * 0.75 * t)
            pygame.draw.line(surf, (*cls.COR_RASTRO, round(20 + 120 * t * t)), (x, cy - meia), (x, cy + meia), 2)
        # Brilho em volta do corpo e a cápsula (perfil constante; as pontas redondas vêm dos círculos)
        pintar_perfil(surf, cx - tras + raio, cx + frente - raio, cy, lambda t: raio * 2.0,
                      ((cls.COR_HALO, 45, 1.0), (cls.COR_HALO, 80, 0.75)), passos=14)
        pintar_perfil(surf, cx - tras + raio, cx + frente - raio, cy, lambda t: raio, cls.CAMADAS, passos=16)
        return surf

    @classmethod
    def desenhar_brilho(cls, tamanho, quadro):
        forca = cls.CINTILA[quadro % len(cls.CINTILA)]
        raio = min(tamanho) * cls.RAIO
        braco = raio * (1.8 + 1.4 * forca)
        imagem = brilho_aditivo(raio * 2.3 * forca, cls.COR_CLARAO, forca=min(1.0, forca), lado=round(braco * 2) + 4)
        centro = pygame.math.Vector2(imagem.get_width() / 2, imagem.get_height() / 2)
        giro = 45 * (quadro % 2)
        for k in range(4):                     # estrela: braço laranja e miolo branco
            ponta = pygame.math.Vector2(braco, 0).rotate(giro + 90 * k)
            pygame.draw.line(imagem, (190, 120, 40), centro, centro + ponta, 2)
            pygame.draw.line(imagem, (255, 245, 210), centro, centro + ponta * 0.45, 2)
        pygame.draw.circle(imagem, (255, 255, 230), centro, max(1.0, raio * 0.35 * forca))
        return imagem

