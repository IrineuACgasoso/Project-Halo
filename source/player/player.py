import pygame

from source.windows.settings import *
from .player_input import PlayerInput
from .player_movement import PlayerMovement
from .player_animation import PlayerAnimation
from .player_combat import PlayerCombat
from .player_scaling import PlayerScaling
from .player_setup import PlayerSetup   


class Player(
    pygame.sprite.Sprite,
    PlayerInput,
    PlayerMovement,
    PlayerAnimation,
    PlayerCombat,
    PlayerScaling,
    PlayerSetup,
    ):

    def __init__(self, posicao_inicial, grupos, game):
        """
        Inicia o jogador.
        sheet_player: Imagem.
        grupos: grupos de sprite
        """
        super().__init__(grupos)
        self.game = game
        self.setup_movimento()

        self.setup_animacao(posicao_inicial)

        self.setup_hitbox()

        self.setup_armas()

        self.setup_shield()

        self.setup_status()

        self.setup_xp()

        self.setup_invencibilidade()

        self.setup_ranking()

    def update(self, delta_time, paredes=None):

        self.input()

        self.atualizar_escudo(delta_time)

        if paredes is not None:
            self.mover_com_colisao(delta_time, paredes)

        self.atualizar_void()

        self.atualizar_buff(delta_time)

        self.atualizar_invencibilidade()

        self.atualizar_animacao()

        self.debug_hacks()
            
            