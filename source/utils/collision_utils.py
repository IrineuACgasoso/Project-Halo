import math


def empurrao_do_segmento(px, py, x1, y1, x2, y2, raio):
    """Empurrão (dx, dy) que tira o círculo de centro (px, py) de cima do segmento (x1, y1)-(x2, y2),
    ou None se não há contato. Só floats: roda centenas de vezes por frame e não aloca Vector2.
    As contas seguem a ordem das do Vector2 antigo (dot, length, normalize), então o resultado é o mesmo."""
    ax = x2 - x1
    ay = y2 - y1
    comprimento2 = ax * ax + ay * ay
    if comprimento2 == 0:
        return None   # segmento degenerado

    # Ponto do segmento mais próximo do centro (projeção limitada entre 0 e 1)
    t = ((px - x1) * ax + (py - y1) * ay) / comprimento2
    t = max(0, min(1, t))
    dx = px - (x1 + t * ax)
    dy = py - (y1 + t * ay)
    distancia = math.sqrt(dx * dx + dy * dy)

    if distancia >= raio:
        return None
    if distancia == 0:
        return (0.0, -raio)   # exatamente sobre a linha (raro): empurrão padrão para cima
    forca = raio - distancia + 0.1
    return (dx / distancia * forca, dy / distancia * forca)


def sair_das_paredes(posicao, raio, grade, iteracoes):
    """Empurra `posicao` (Vector2, alterado no lugar) para fora das paredes da `grade` perto dela.
    Várias iterações: em cantos apertados um empurrão pode jogar a entidade dentro de outra linha."""
    px, py = posicao.x, posicao.y
    segmentos = grade.perto(px, py, raio)
    if not segmentos:
        return
    for _ in range(iteracoes):
        for _, x1, y1, x2, y2 in segmentos:
            empurrao = empurrao_do_segmento(px, py, x1, y1, x2, y2, raio)
            if empurrao:
                px += empurrao[0]
                py += empurrao[1]
    posicao.update(px, py)
