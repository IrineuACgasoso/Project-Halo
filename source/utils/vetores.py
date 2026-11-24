import pygame


def direcao_segura(origem, destino, padrao=(1, 0)):
    """Vetor unitário origem -> destino. Se os pontos coincidem devolve `padrao`
    em vez de lançar ValueError (Vector2.normalize() em vetor nulo derruba o jogo)."""
    v = pygame.math.Vector2(destino) - pygame.math.Vector2(origem)
    if v.length_squared() == 0:
        return pygame.math.Vector2(padrao)
    return v.normalize()


def no_cone(origem, eixo, ponto, cos_meio_angulo):
    """`ponto` está no cone com vértice em `origem`, eixo `eixo` (UNITÁRIO) e meia-abertura θ,
    dado `cos_meio_angulo` = cos(θ) (calcule uma vez, fora do laço)? A borda conta; o próprio
    vértice também.

    Só multiplicações, sem raiz nem trigonometria: o ângulo entre eixo e v é <= θ quando
    eixo·v >= cos(θ)·|v|; com cos(θ) >= 0, isso é eixo·v >= 0 e (eixo·v)² >= cos²(θ)·|v|².
    """
    vx = ponto[0] - origem[0]
    vy = ponto[1] - origem[1]
    escalar = eixo[0] * vx + eixo[1] * vy
    comparado = cos_meio_angulo * cos_meio_angulo * (vx * vx + vy * vy)
    if cos_meio_angulo >= 0:
        return escalar >= 0 and escalar * escalar >= comparado
    return escalar >= 0 or escalar * escalar <= comparado   # meia-abertura > 90°


def no_retangulo(origem, eixo, ponto, comprimento, meia_largura):
    """`ponto` está no retângulo que sai de `origem` na direção `eixo` (UNITÁRIO), com `comprimento`
    à frente e `meia_largura` para cada lado? As bordas contam. Só multiplicações."""
    vx = ponto[0] - origem[0]
    vy = ponto[1] - origem[1]
    frente = eixo[0] * vx + eixo[1] * vy
    lado = eixo[0] * vy - eixo[1] * vx
    return 0 <= frente <= comprimento and -meia_largura <= lado <= meia_largura
