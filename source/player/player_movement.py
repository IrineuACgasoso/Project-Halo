import pygame
from source.utils.collision_utils import projetar_fora_da_linha

class PlayerMovement:    
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
                    
                    push = projetar_fora_da_linha(self.posicao, p1, p2, raio)
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