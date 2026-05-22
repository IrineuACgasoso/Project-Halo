import pygame

class MapCollision:
    def get_paredes_proximas(self, entidade_pos, raio=1000):
        paredes_proximas = []
        for p_dict in self.paredes:
            # Criamos um retângulo que envolve toda a polilinha (Bounding Box)
            pontos = p_dict['pontos']
            min_x = min(p.x for p in pontos)
            max_x = max(p.x for p in pontos)
            min_y = min(p.y for p in pontos)
            max_y = max(p.y for p in pontos)
            
            # Criamos um Rect temporário para facilitar a checagem
            rect_da_parede = pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
            
            # Inflamos o rect para o filtro ser "generoso"
            rect_da_parede.inflate_ip(raio, raio)

            if rect_da_parede.collidepoint(entidade_pos):
                paredes_proximas.append(p_dict)
                
        return paredes_proximas
    
    def caminho_livre(self, ponto_a, ponto_b):
        """Verifica se uma linha entre A e B cruza alguma parede."""
        for p_dict in self.paredes:
            pontos = p_dict['pontos']
            # Checa cada segmento da polilinha
            for i in range(len(pontos) - 1):
                p1 = pontos[i]
                p2 = pontos[i+1]
                # Pygame clipline retorna os pontos de intersecção se houver colisão
                if pygame.draw.line(pygame.Surface((1,1)), (0,0,0), p1, p2, 1).clipline(ponto_a, ponto_b):
                    return False
        return True