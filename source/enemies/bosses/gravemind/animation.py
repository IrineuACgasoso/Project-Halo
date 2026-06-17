import pygame
import random
from source.feats.effects import DustParticle
from source.systems.entitymanager import entity_manager


class GravemindAnimation:
    def animar(self):
        agora = pygame.time.get_ticks()
        direcao = self.estado_animacao if self.estado_animacao in ['left', 'right'] else 'left'

        if self.estado_habilidade == 'acid':
            try:
                self.image = self.sprites[direcao][2]
            except IndexError:
                self.image = self.sprites[direcao][0]
        else:
            if agora - self.ultimo_update_animacao > self.velocidade_animacao_loop:
                self.ultimo_update_animacao = agora
                self.frame_atual = (self.frame_atual + 1) % 2
            try:
                self.image = self.sprites[direcao][self.frame_atual]
            except IndexError:
                self.image = self.sprites[direcao][0]

        self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))
        self.mask = pygame.mask.from_surface(self.image)

    
    def atualizar_animacao_respawn(self, delta_time, agora):
        """Mantém sua lógica original de renderização de máscara intacta"""
        sprite_base = self.sprites['left'][0]
        if self.estado_respawn == 'reaparecendo':
            self.altura_atual += 300 * delta_time
            if agora - self.timer_particula > 50:
                self.timer_particula = agora
                for _ in range(3):
                    off_x = random.randint(-self.tamanho_sprite[0]//4, self.tamanho_sprite[0]//4)
                    DustParticle((self.posicao_chao.x + off_x, self.posicao_chao.y), (entity_manager.all_sprites,))
            if self.altura_atual >= self.tamanho_sprite[1]:
                self.altura_atual = self.tamanho_sprite[1]
                self.is_animating_respawn = False
                self.estado_respawn = None    
        elif self.estado_respawn == 'desaparecendo':
            self.altura_atual -= 300 * delta_time
            if self.altura_atual <= 0: 
                self.respawn_logic()
                return
        self.game.camera.shake(intensidade=self.intensidade_shake)
        h = int(max(1, self.altura_atual))
        self.image = pygame.Surface((self.tamanho_sprite[0], h), pygame.SRCALPHA).convert_alpha()
        area_recorte = pygame.Rect(0, self.tamanho_sprite[1] - h, self.tamanho_sprite[0], h)
        self.image.blit(sprite_base, (0, 0), area_recorte)
        self.rect = self.image.get_rect(centerx=self.posicao_chao.x, bottom=self.posicao_chao.y)
        self.posicao = pygame.math.Vector2(self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)