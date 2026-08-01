import pygame
from .projetil import ProjetilUniversal

class HeavyBurst(ProjetilUniversal):
    """Projétil de precisão pesado: mais longo e mais rápido que o BurstRifle
    comum, com um núcleo super brilhante e uma cauda energética — visual de
    'tiro que dói', condizente com o dano tremendo da SniperRifle."""

    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread, piercing=1):
        super().__init__(
            posicao_inicial=posicao_inicial,
            grupos=grupos,
            game=game,
            dono=dono,
            sprite_key='heavy_burst',
            tamanho=tamanho,      # ex: (46, 14) — mais comprido que o BurstRifle padrão
            dano=dano,
            velocidade=velocidade,
            duracao=1500,
            direcao_custom=direcao_spread,
            piercing=piercing,
            rotacionar=True
        )

    def obter_imagem_base(self, sprite_key, tamanho):
        """Desenha uma vez (e cacheia) um projétil alongado: cauda energética
        translúcida + corpo amarelo-quente + núcleo branco ofuscante na
        ponta — sensação de tiro de precisão de altíssimo impacto."""
        base_key = f"base_{sprite_key}_{tamanho[0]}x{tamanho[1]}"
        if base_key not in ProjetilUniversal.GLOBAL_CACHE:
            w, h = tamanho
            surf = pygame.Surface(tamanho, pygame.SRCALPHA)
            centro_y = h / 2

            # 1. Cauda: rastro translúcido atrás do projétil, mais fino e
            #    esmaecendo em direção à origem (esquerda)
            cauda_len = int(w * 0.55)
            cauda = pygame.Surface((cauda_len, h), pygame.SRCALPHA)
            for x in range(cauda_len):
                alpha = int(140 * (x / cauda_len))
                espessura = max(1, int(h * 0.35 * (x / cauda_len)))
                pygame.draw.line(
                    cauda, (255, 200, 60, alpha),
                    (x, centro_y - espessura / 2), (x, centro_y + espessura / 2)
                )
            surf.blit(cauda, (0, 0))

            # 2. Corpo: cápsula amarelo-quente sólida, ocupando a metade
            #    frontal do projétil
            corpo_w = int(w * 0.5)
            corpo_rect = pygame.Rect(w - corpo_w, centro_y - h * 0.3, corpo_w, h * 0.6)
            pygame.draw.rect(surf, (255, 175, 40, 255), corpo_rect, border_radius=int(h * 0.3))

            # 3. Núcleo: clarão branco-quente na ponta, o "olho" do impacto
            nucleo_raio = int(h * 0.55)
            centro_nucleo = (w - nucleo_raio // 2, int(centro_y))
            glow = pygame.Surface((nucleo_raio * 2, nucleo_raio * 2), pygame.SRCALPHA)
            gc = (nucleo_raio, nucleo_raio)
            pygame.draw.circle(glow, (255, 230, 150, 90), gc, nucleo_raio)
            pygame.draw.circle(glow, (255, 255, 255, 255), gc, int(nucleo_raio * 0.45))
            surf.blit(glow, (centro_nucleo[0] - nucleo_raio, centro_nucleo[1] - nucleo_raio), special_flags=pygame.BLEND_RGBA_ADD)

            ProjetilUniversal.GLOBAL_CACHE[base_key] = surf
        return ProjetilUniversal.GLOBAL_CACHE[base_key]