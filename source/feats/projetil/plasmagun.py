import pygame

from .desenhado import ProjetilDesenhado, brilho_aditivo, pintar_perfil


class PlasmaGun(ProjetilDesenhado):
    """Tiro de plasma verde-limão: cabeça redonda com núcleo branco, cauda curta que afina e um halo que
    pulsa (4 quadros). O acerto continua o círculo do `tamanho`."""
    QUADROS = 4
    PERIODO_MS = 70
    PULSO = (0.8, 1.0, 1.15, 1.0)
    # (cor, alpha, escala do raio), de fora para dentro
    CAMADAS = (((110, 255, 30), 90, 1.35), ((170, 255, 0), 240, 1.0),
               ((215, 255, 120), 255, 0.68), ((250, 255, 230), 255, 0.38))
    COR_HALO = (95, 210, 20)

    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread,
                 vai_rotacionar=False, fonte=None):
        # `vai_rotacionar` fica por compatibilidade: a cauda já gira com o tiro
        super().__init__(
            posicao_inicial=posicao_inicial,
            grupos=grupos,
            game=game,
            dono=dono,
            fonte=fonte,
            sprite_key='plasma',
            tamanho=tamanho,
            dano=dano,
            velocidade=velocidade,
            duracao=3000,
            direcao_custom=direcao_spread,
        )

    @classmethod
    def desenhar_corpo(cls, tamanho):
        w = min(tamanho)
        raio, cauda = w * 0.42, w * 1.2
        largura = round(2 * (cauda + raio * 1.4)) + 4
        altura = round(2 * raio * 1.4) + 4
        surf = pygame.Surface((largura, altura), pygame.SRCALPHA)
        cx, cy = largura / 2, altura / 2
        pintar_perfil(surf, cx - cauda, cx, cy, lambda t: raio * (0.15 + 0.85 * t ** 1.5), cls.CAMADAS)
        pygame.draw.circle(surf, (255, 255, 255, 255), (cx + raio * 0.2, cy), max(1.0, raio * 0.3))
        return surf

    @classmethod
    def desenhar_brilho(cls, tamanho, quadro):
        pulso = cls.PULSO[quadro % len(cls.PULSO)]
        return brilho_aditivo(min(tamanho) * 0.85 * pulso, cls.COR_HALO, forca=0.6 + 0.4 * pulso)
