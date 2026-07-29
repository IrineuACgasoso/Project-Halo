import pygame
from .projetil import ProjetilUniversal

class PlasmaGun(ProjetilUniversal):
    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread, vai_rotacionar):
        # Plasma é uma bola/glow, não precisa de rotação 360 (rotacionar=False)
        super().__init__(
            posicao_inicial=posicao_inicial, 
            grupos=grupos, 
            game=game, 
            dono=dono, 
            sprite_key='plasma', 
            tamanho=tamanho, 
            dano=dano, 
            velocidade=velocidade, 
            duracao=3000, 
            direcao_custom=direcao_spread, 
            rotacionar=vai_rotacionar
            )

    def obter_imagem_base(self, sprite_key, tamanho):
        """Desenha o glow verde-limão neon uma única vez e cacheia no
        GLOBAL_CACHE compartilhado, substituindo o asset original de 'plasma'."""
        base_key = f"base_{sprite_key}_{tamanho[0]}x{tamanho[1]}"
        if base_key not in ProjetilUniversal.GLOBAL_CACHE:
            surf = pygame.Surface(tamanho, pygame.SRCALPHA)
            centro = (tamanho[0] // 2, tamanho[1] // 2)
            pygame.draw.circle(surf, (170, 255, 0, 235), centro, tamanho[0] // 2)   # verde-limão neon
            pygame.draw.circle(surf, (255, 255, 255, 255), centro, tamanho[0] // 4)  # núcleo branco
            ProjetilUniversal.GLOBAL_CACHE[base_key] = surf
        return ProjetilUniversal.GLOBAL_CACHE[base_key]
    