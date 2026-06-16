import pygame
from source.enemies.base.enemy_base import BaseEnemy
from source.systems.entitymanager import entity_manager

from .setup import GravemindSetup
from .states import GravemindAI
from .attacks import GravemindAttacks
from .vfx import GravePit, FloodWarning

class BaseGravemind(BaseEnemy, GravemindSetup, GravemindAI, GravemindAttacks):
    """Herança múltipla"""
    def __init__(self, posicao, game, jogador, variante, vida, dano):
        super().__init__(
            posicao, 
            vida_base=vida, 
            dano_base=dano, 
            velocidade_base=0, 
            game=game, 
            sprite_key='gravemind',
            flip_sprite=True,
            variante=variante
        )
        
        self.jogador = jogador if jogador else entity_manager.player
        self.setup_animation(estado_inicial='left', velocidade_animacao=600)
        
        # O inicializar_habilidades agora configura tudo com base no self.variante
        self.inicializar_habilidades()

    @property
    def invulneravel(self): 
        return self.is_animating_respawn

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()
        self.executar_estados(agora, delta_time)

        if not self.is_animating_respawn and self.estado_habilidade != 'acid':
            direcao_x = self.jogador.posicao.x - self.posicao.x 
            self.set_sprite_direction(direcao_x)
        
        if not self.is_animating_respawn:
            super().update(delta_time, paredes)
            self.animar()

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


class FinalGravemind(BaseGravemind):
    def __init__(self, posicao, game, jogador=None):
        self.is_minion = False
        
        super().__init__(
            posicao, game, jogador, 
            variante='final', 
            vida=8000, dano=50
        )

    def respawn_logic(self):
        self.kill() 


class ProtoGravemind(BaseGravemind):
    def __init__(self, posicao, game, jogador=None, is_minion=False):
        # Definido antes do super() para que o setup_habilidades consiga ler se é minion
        self.is_minion = is_minion
        vida_inicial = 100 if is_minion else 100

        super().__init__(
            posicao, game, jogador, 
            variante='proto', 
            vida=vida_inicial, dano=50
        )

    def update(self, delta_time, paredes=None):
        if not self.is_minion and self.vida <= self.vida_base / 6 and not self.is_animating_respawn:
            self.estado_respawn = 'desaparecendo'
            self.is_animating_respawn = True
            return
        super().update(delta_time, paredes)

    def respawn_logic(self):
        if self.game.gravemind_reborns > 1 and not self.is_minion:
            self.game.gravemind_reborns -= 1
            FloodWarning(self.jogador.posicao, self.game)
        elif self.game.gravemind_reborns == 1:
            self.game.gravemind_reborns = 0
            GravePit(self.jogador.posicao, self.game)
        self.kill()