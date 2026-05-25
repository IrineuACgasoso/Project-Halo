import pygame

def projetar_fora_da_linha(pos_player, p1, p2, raio):
        # Vetor do segmento de linha
        aresta = p2 - p1
        if aresta.length_squared() == 0: return None

        # Acha o ponto mais próximo do centro do player no segmento (p1-p2)
        # Isso usa projeção escalar limitada entre 0 e 1
        t = max(0, min(1, (pos_player - p1).dot(aresta) / aresta.length_squared()))
        ponto_mais_proximo = p1 + t * aresta

        # Vetor do ponto mais próximo até o centro do player
        diff = pos_player - ponto_mais_proximo
        distancia = diff.length()

        if distancia < raio:
            # Se o player está "atravessando" a linha, calculamos o empurrão
            # Se distancia for 0, o player está exatamente sobre a linha (raro, mas tratamos)
            if distancia == 0:
                return pygame.math.Vector2(0, -1) * raio # Empurrão padrão para cima
            
            push_mag = raio - distancia + 0.1
            return diff.normalize() * push_mag
        
        return None