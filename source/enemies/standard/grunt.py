import pygame
from source.systems.gameclock import relogio
import random

from source.enemies.base.enemy_base import BaseEnemy
from source.feats.projetil import PlasmaGun
from source.systems.entitymanager import entity_manager
from source.data.enemy_data import INIMIGOS


class GruntBase(BaseEnemy):
    def __init__(self, posicao, game, perfil, variante, vel_animacao=150):
        super().__init__(
            posicao=posicao,
            vida_base=perfil.vida,
            dano_base=perfil.dano,
            velocidade_base=perfil.velocidade,
            game=game,
            sprite_key='grunt', # Mantém seu padrão de sprite key
            variante=variante
        )
        self.perfil = perfil
        self.tabela_drop = perfil.drops
        self.setup_animation(estado_inicial='right', velocidade_animacao=vel_animacao)

        # Plasma
        self.plasma_cooldown = self.novo_cooldown(*perfil.cooldowns['plasma'])
        self.ultimo_tiro = relogio.agora()

    def update(self, delta_time, paredes=None):
        super().update(delta_time, paredes)
        agora = relogio.agora()
        if agora - self.ultimo_tiro >= self.plasma_cooldown:
            self.plasma_cooldown = self.novo_cooldown(*self.perfil.cooldowns['plasma'])
            self.plasma()
            self.ultimo_tiro = agora

        direcao_x = self.jogador.posicao.x - self.posicao.x
        self.set_sprite_direction(direcao_x)
        self.animar()

    def plasma(self):
        direcao_tiro = self.calcular_direcao_tiro(0.1)

        PlasmaGun(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites,),
            jogador=self.jogador,
            game=self.game,
            dono = 'INIMIGO', fonte=self,
            tamanho=(24, 24),
            dano=5,
            velocidade=450,
            direcao_spread=direcao_tiro,
            vai_rotacionar = False
        )    


class GruntRed(GruntBase):
    def __init__(self, posicao, game):
        super().__init__(posicao, game, INIMIGOS['grunt_red'], variante='red', vel_animacao=200)

class GruntBlue(GruntBase):
    def __init__(self, posicao, game):
        super().__init__(posicao, game, INIMIGOS['grunt_blue'], variante='blue', vel_animacao=200)

class SpaceGrunt(GruntBase):
    def __init__(self, posicao, game):
        super().__init__(posicao, game, INIMIGOS['space_grunt'], variante='space', vel_animacao=200)
