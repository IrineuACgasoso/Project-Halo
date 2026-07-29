import pygame
from .projetil import ProjetilUniversal

class Carabin(ProjetilUniversal):
    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread, duracao=2000, is_Banished=False):
        s_key = 'bcarabin' if is_Banished else 'carabin'
        # Agora é um projétil circular (glow), não precisa mais de rotação
        super().__init__(
            posicao_inicial = posicao_inicial,
            grupos = grupos,
            game = game,
            dono=dono, 
            sprite_key = s_key,
            tamanho = tamanho,
            dano = dano,
            velocidade = velocidade,
            duracao = duracao,
            direcao_custom = direcao_spread, # Garanta que 'direcao' seja passado aqui
            rotacionar = False,
            )

    def obter_imagem_base(self, sprite_key, tamanho):
        """Desenha o glow azul-claro/branco uma única vez e cacheia no
        GLOBAL_CACHE compartilhado, substituindo o asset original de
        'carabin'/'bcarabin'."""
        base_key = f"base_{sprite_key}_{tamanho[0]}x{tamanho[1]}"
        if base_key not in ProjetilUniversal.GLOBAL_CACHE:
            if sprite_key == 'bcarabin':
                cor_glow = (255, 45, 50, 240)
                cor_nucleo = (255, 225, 225, 255)
            else:
                cor_glow = (120, 200, 255, 235)   # azul-claro
                cor_nucleo = (255, 255, 255, 255)

            surf = pygame.Surface(tamanho, pygame.SRCALPHA)
            centro = (tamanho[0] // 2, tamanho[1] // 2)
            pygame.draw.circle(surf, cor_glow, centro, tamanho[0] // 2)   # azul-claro
            pygame.draw.circle(surf, cor_nucleo, centro, tamanho[0] // 4)   # núcleo branco
            ProjetilUniversal.GLOBAL_CACHE[base_key] = surf
        return ProjetilUniversal.GLOBAL_CACHE[base_key]