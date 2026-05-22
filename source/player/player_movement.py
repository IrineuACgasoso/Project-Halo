import pygame

class PlayerMovement:
    def projetar_fora_da_linha(self, pos_player, p1, p2, raio):
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
    
    def mover_com_colisao(self, delta_time, paredes_ativas):
        # 1. Aplicamos o movimento bruto
        dt_seguro = min(delta_time, 0.033)
        self.posicao += self.direcao * self.velocidade * dt_seguro
        
        # 2. Resolvemos colisões com Polilinhas (e Polígonos, que viram linhas)
        # Fazemos isso 2 ou 3 vezes (iterações) para garantir que em cantos apertados 
        # um empurrão não nos jogue para dentro de outra linha.
        raio = self.hitbox.width / 2
        
        for _ in range(3): # Iteraçoes de segurança
            for p in paredes_ativas:
                # Pegamos os pontos da polilinha ou polígono
                pontos = p['pontos']
                for i in range(len(pontos) - 1):
                    p1 = pontos[i]
                    p2 = pontos[i+1]
                    
                    push = self.projetar_fora_da_linha(self.posicao, p1, p2, raio)
                    if push:
                        self.posicao += push

        # 3. Sincroniza Hitbox e Rect visual
        self.hitbox.center = (round(self.posicao.x), round(self.posicao.y))
        self.rect.center = self.hitbox.center
    
    def atualizar_void(self):

        # Calcula se o player está em uma zona de Void
        forca, ponto_alvo, dist = (
            self.game.mapa.calcular_puxo_void(self.posicao)
        )
        if ponto_alvo:
            self.posicao += forca

            self.tomar_dano_direto(1)

            # Se o player chegar muito perto do VoidPoint ele morre
            if dist < 15:
                self.tomar_dano_direto(99999)