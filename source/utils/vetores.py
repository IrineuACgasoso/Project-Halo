import pygame


def direcao_segura(origem, destino, padrao=(1, 0)):
    """Vetor unitário origem -> destino. Se os pontos coincidem devolve `padrao`
    em vez de lançar ValueError (Vector2.normalize() em vetor nulo derruba o jogo)."""
    v = pygame.math.Vector2(destino) - pygame.math.Vector2(origem)
    if v.length_squared() == 0:
        return pygame.math.Vector2(padrao)
    return v.normalize()
