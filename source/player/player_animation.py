import pygame

class PlayerAnimation:
    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
    
    def atualizar_animacao(self):
        if self.direcao.x < 0:
            self.estado_animacao = 'left'
        elif self.direcao.x > 0:
            self.estado_animacao = 'right'
        if self.direcao.x == 0 and self.direcao.y == 0:
            self.image = self.sprites[self.estado_animacao][0] # Usa o frame 0 da direção atual
        if self.direcao.magnitude() == 0:
            # Mantém o frame parado
            pass 
        else:
            self.animar()
