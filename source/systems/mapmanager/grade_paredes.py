TAMANHO_CELULA = 128   # px
# px: a célula da entidade traz todo segmento a menos de MARGEM_GRADE dela. A folga além do raio
# (jogador 48 → 80 px; inimigo 15 → 113 px) cobre o deslocamento dos empurrões em sequência num canto.
# Com 64 a folga do jogador era 16 px, e um canto fundo o levava a paredes que a consulta não trouxe.
MARGEM_GRADE = 128


class GradeParedes:
    """Segmentos de parede (tuplas de float) indexados numa grade uniforme (roteiro C1).

    Cada segmento entra em todas as células que a sua caixa, inflada de `margem`, toca. Assim, a
    célula onde a entidade está já contém todo segmento a menos de `margem` dela: para raio <= margem
    a consulta é um acesso a dict, sem alocar nada.
    Os segmentos saem na ordem do mapa (`indice`), a mesma ordem em que o código antigo aplicava os
    empurrões. A ordem importa, porque os empurrões são sequenciais.
    """

    def __init__(self, paredes, celula=TAMANHO_CELULA, margem=MARGEM_GRADE):
        if celula <= 0 or margem < 0:
            raise ValueError('celula deve ser > 0 e margem >= 0')
        self.celula = celula
        self.margem = margem

        segmentos = []
        for parede in paredes:
            pontos = parede['pontos']
            for a, b in zip(pontos, pontos[1:]):
                if a[0] == b[0] and a[1] == b[1]:
                    continue   # segmento degenerado nunca empurra
                segmentos.append((len(segmentos), float(a[0]), float(a[1]), float(b[0]), float(b[1])))
        self.segmentos = tuple(segmentos)

        celulas = {}
        for seg in self.segmentos:
            _, x1, y1, x2, y2 = seg
            cx0, cy0 = self._celula_de(min(x1, x2) - margem, min(y1, y2) - margem)
            cx1, cy1 = self._celula_de(max(x1, x2) + margem, max(y1, y2) + margem)
            for cx in range(cx0, cx1 + 1):
                for cy in range(cy0, cy1 + 1):
                    celulas.setdefault((cx, cy), []).append(seg)
        self._celulas = {chave: tuple(lista) for chave, lista in celulas.items()}

    def _celula_de(self, x, y):
        return int(x // self.celula), int(y // self.celula)

    def perto(self, x, y, raio):
        """Segmentos `(indice, x1, y1, x2, y2)` que podem estar a menos de `raio` de (x, y), em ordem."""
        if raio <= self.margem:
            return self._celulas.get(self._celula_de(x, y), ())
        # Raio maior que a margem (ex.: hitbox de veículo): junta as células que cobrem o círculo.
        cx0, cy0 = self._celula_de(x - raio, y - raio)
        cx1, cy1 = self._celula_de(x + raio, y + raio)
        juntos = set()
        for cx in range(cx0, cx1 + 1):
            for cy in range(cy0, cy1 + 1):
                juntos.update(self._celulas.get((cx, cy), ()))
        return sorted(juntos)
