import pygame
from .projetil import ProjetilUniversal

class ProjetilShotgun(ProjetilUniversal):
    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread):
        super().__init__(
            posicao_inicial=posicao_inicial, 
            grupos=grupos, 
            game=game, 
            dono=dono, 
            sprite_key='shotgun_shard', 
            tamanho=tamanho, 
            dano=dano, 
            velocidade=velocidade, 
            duracao=600,  # Curto alcance: some rápido após o disparo estourar
            direcao_custom=direcao_spread, 
            rotacionar=True
        )

    def obter_imagem_base(self, sprite_key, tamanho):
        """Desenha um estilhaço aerodinâmico com gradiente de brilho térmico 
        (Laranja, Amarelo e Clarão Branco) e guarda no cache de texturas."""
        base_key = f"base_{sprite_key}_{tamanho[0]}x{tamanho[1]}"
        if base_key not in ProjetilUniversal.GLOBAL_CACHE:
            w, h = tamanho
            surf = pygame.Surface(tamanho, pygame.SRCALPHA)
            
            # 1. Camada Externa: Estilhaço Base / Glow Térmico (Laranja Vivo)
            pts_laranja = [
                (0, h // 2),            # Cauda/Origem
                (w // 4, h // 6),       # Dorso superior
                (w, h // 2),            # Ponta perfurante (Direita)
                (w // 4, 5 * h // 6)    # Dorso inferior
            ]
            pygame.draw.polygon(surf, (255, 90, 0, 240), pts_laranja)
            
            # 2. Camada Interna: Núcleo de Superaquecimento (Amarelo)
            pts_amarelo = [
                (w // 6, h // 2), 
                (w // 3, h // 4), 
                (w * 0.85, h // 2), 
                (w // 3, 3 * h // 4)
            ]
            pygame.draw.polygon(surf, (255, 220, 0, 255), pts_amarelo)
            
            # 3. Núcleo Interno: Clarão Crítico/Incandescente (Branco Puro)
            pts_branco = [
                (w // 3, h // 2), 
                (w // 2, h // 2 - 2), 
                (w * 0.65, h // 2), 
                (w // 2, h // 2 + 2)
            ]
            pygame.draw.polygon(surf, (255, 255, 255, 255), pts_branco)
            
            ProjetilUniversal.GLOBAL_CACHE[base_key] = surf
        return ProjetilUniversal.GLOBAL_CACHE[base_key]

