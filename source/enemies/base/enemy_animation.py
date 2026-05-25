import pygame

class EnemyAnimation:
    def setup_animation(self, estado_inicial='right', velocidade_animacao=150):
        self.frame_atual = 0
        self.estado_animacao = estado_inicial
        self.velocidade_animacao = velocidade_animacao
        self.ultimo_update_animacao = pygame.time.get_ticks()

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.set_image(self.get_current_sprite())

    def set_sprite_direction(self, direcao_x):
        novo_estado = self.estado_animacao

        if direcao_x < 0:
            novo_estado = 'left'

        elif direcao_x > 0:
            novo_estado = 'right'

        if novo_estado != self.estado_animacao:
            self.estado_animacao = novo_estado
            self.set_image(self.get_current_sprite())