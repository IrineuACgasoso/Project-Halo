import pygame


class MapCollision:
    def _bboxes_paredes(self):
        """Bounding box de cada parede, calculada UMA vez (antes era recalculada com min()/max()
        sobre todos os pontos de todas as paredes, mais um Rect novo por parede, a cada frame)."""
        cache = getattr(self, '_paredes_bbox_cache', None)
        if cache is None or cache[0] != len(self.paredes):
            caixas = []
            for p in self.paredes:
                xs = [pt.x for pt in p['pontos']]
                ys = [pt.y for pt in p['pontos']]
                caixas.append((min(xs), min(ys), max(xs), max(ys), p))
            cache = (len(self.paredes), caixas)
            self._paredes_bbox_cache = cache
        return cache[1]

    def get_paredes_proximas(self, entidade_pos, raio=1000):
        # O filtro antigo inflava o rect em `raio` no TOTAL, ou seja, +-raio/2 em cada lado.
        meio = raio / 2
        x, y = entidade_pos[0], entidade_pos[1]
        return [
            p for (x0, y0, x1, y1, p) in self._bboxes_paredes()
            if x0 - meio <= x <= x1 + meio and y0 - meio <= y <= y1 + meio
        ]

    @staticmethod
    def _segmentos_se_cruzam(a, b, c, d):
        """Interseção própria entre os segmentos a-b e c-d (produto vetorial)."""
        def lado(p, q, r):
            return (q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x)
        return (lado(a, b, c) * lado(a, b, d) < 0) and (lado(c, d, a) * lado(c, d, b) < 0)

    def caminho_livre(self, ponto_a, ponto_b):
        """Verifica se a linha A-B cruza alguma parede.
        (Atualmente sem chamadas no projeto. A versão antiga desenhava uma linha numa Surface 1x1
        por segmento e testava só a CAIXA do segmento -> falsos "bloqueado" em paredes diagonais.)"""
        a = pygame.math.Vector2(ponto_a)
        b = pygame.math.Vector2(ponto_b)
        min_x, max_x = min(a.x, b.x), max(a.x, b.x)
        min_y, max_y = min(a.y, b.y), max(a.y, b.y)
        for x0, y0, x1, y1, p in self._bboxes_paredes():
            if x1 < min_x or x0 > max_x or y1 < min_y or y0 > max_y:
                continue   # descarte rápido pela bounding box
            pontos = p['pontos']
            for i in range(len(pontos) - 1):
                if self._segmentos_se_cruzam(a, b, pontos[i], pontos[i + 1]):
                    return False
        return True
