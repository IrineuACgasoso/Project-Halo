import pygame
from source.enemies.base.enemy_base import BaseEnemy
from source.systems.entitymanager import entity_manager

from .setup import GravemindSetup
from .animation import GravemindAnimation
from .states import GravemindAI
from .attacks import GravemindAttacks
from .vfx import GravePit, FloodWarning

class BaseGravemind(BaseEnemy, GravemindSetup, GravemindAI, GravemindAttacks, GravemindAnimation):
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


class FinalGravemind(BaseGravemind):
    def __init__(self, posicao, game, jogador=None):
        self.is_minion = False
        self.is_boss = True
        
        super().__init__(posicao, game, jogador, variante='final', vida=5000, dano=50
        )

    def respawn_logic(self):
        self.kill() 


class ProtoGravemind(BaseGravemind):
    def __init__(self, posicao, game, jogador=None, is_minion=False):
        # Definido antes do super() para que o setup_habilidades consiga ler se é minion
        self.is_minion = is_minion
        vida_inicial = 500 if is_minion else 1000

        super().__init__(posicao, game, jogador, variante='proto', vida=vida_inicial, dano=50)

        self.is_boss = False

    def update(self, delta_time, paredes=None):
        if not self.is_minion and self.vida <= self.vida_base / 6 and not self.is_animating_respawn:
            self.estado_respawn = 'desaparecendo'
            self.is_animating_respawn = True
            return
        super().update(delta_time, paredes)

    def respawn_logic(self):
        if self.game.gravemind_reborns > 1 and not self.is_minion:
            self.game.gravemind_reborns -= 1
            novo_aviso = FloodWarning(self.jogador.posicao, self.game)
            self.game.boss_atual = novo_aviso
        elif self.game.gravemind_reborns == 1:
            self.game.gravemind_reborns = 0
            novo_pit = GravePit(self.jogador.posicao, self.game)
            self.game.boss_atual = novo_pit
        self.kill()