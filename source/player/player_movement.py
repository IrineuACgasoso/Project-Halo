import pygame
from source.utils.collision_utils import sair_das_paredes

class PlayerMovement:    
    def mover_com_colisao(self, delta_time, grade_paredes):
        # 1. Aplicamos o movimento bruto
        dt_seguro = min(delta_time, 0.033)
        self.posicao += self.direcao * self.velocidade * dt_seguro

        # 2. Resolvemos colisões com as paredes perto do jogador. 3 iterações para garantir que,
        # em cantos apertados, um empurrão não nos jogue para dentro de outra linha.
        sair_das_paredes(self.posicao, self.hitbox.width / 2, grade_paredes, 3)

        # 3. Sincroniza Hitbox e Rect visual
        self.hitbox.center = (round(self.posicao.x), round(self.posicao.y))
        self.rect.center = self.hitbox.center
    
    def atualizar_void(self, delta_time):

        # Calcula se o player está em uma zona de Void
        forca, ponto_alvo, dist = (
            self.game.mapa.calcular_puxo_void(self.posicao)
        )
        if ponto_alvo:
            # Valores antigos eram "por frame" (2.5 px e 1 de dano a cada frame). Convertidos
            # para "por segundo" (x60) para não variar com o FPS.
            self.posicao += forca * (60 * delta_time)

            self.tomar_dano_direto(60 * delta_time)

            # Se o player chegar muito perto do VoidPoint ele morre
            if dist < 15:
                self.tomar_dano_direto(99999)