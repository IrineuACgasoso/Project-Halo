import pygame
import random
from os.path import join
from source.enemies.base.enemy_base import BaseEnemy
from source.windows.settings import *
from source.feats.projetil import Carabin
from source.feats.items import *
from source.feats.assets import ASSETS
from source.systems.entitymanager import entity_manager


class Elite(BaseEnemy):
    def __init__(self, posicao, game):
        super().__init__(posicao, vida_base=30,dano_base=20, velocidade_base=40, game=game, sprite_key='elite', flip_sprite=True)
        
        self.setup_animation(
            estado_inicial='right',
            velocidade_animacao=150
        )

        #Carabin
        self.cooldown_carabin = 4000
        self.intervalo_carabina = 75

        self.cronometro_carabina = 0
        self.ultima_carabina = 0

        self.carabina_restante = 0
        self.contagem_carabina = 5

        # Invisi
        self.vida_critica = False

    def carabin(self):
        # Calculamos a direção para o jogador
        direcao_tiro = self.calcular_direcao_tiro(0.02)

        self.trigger_flash(duracao=35,bonus_alpha=60)

        Carabin(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites,), # A base adiciona o grupo de inimigos sozinha agora
            jogador=self.jogador,
            game=self.game,
            dono = 'INIMIGO',
            tamanho=(16, 16), 
            dano=10,
            velocidade=600,
            direcao_spread=direcao_tiro
        )

    def morrer(self, grupos = None):
        Items.spawn_drop(self.posicao, grupos, 'exp_shard', 3, 100)
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 1, 2)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 1)
        self.kill()

    def update(self, delta_time, paredes=None):
        direcao = (self.jogador.posicao - self.posicao)
        agora = pygame.time.get_ticks()
        #Ativa carabina
        if agora - self.ultima_carabina >= self.cooldown_carabin:
            self.carabina_restante = self.contagem_carabina
            self.cooldown_carabin = self.novo_cooldown(3000, 7000)
            self.ultima_carabina = agora
        #Atira carabina
        if self.carabina_restante > 0:
            self.cronometro_carabina += delta_time * 1000
            if self.cronometro_carabina >= self.intervalo_carabina:
                self.cronometro_carabina = 0
                self.carabina_restante -= 1
                self.carabin()

        # Ativa invisibilidade
        if self.vida <= self.vida_base / 1.1 and not self.vida_critica:
            self.vida_critica = True
            self.velocidade_base *= 2

            self.iniciar_invisibilidade(
                alpha_alvo=0,
                fade_out=800,
                fade_in=800,
                duracao=99000,
                flashing=True
            )

        if direcao.length_squared() >= 122500:
            self.velocidade = self.velocidade_base
        else:
            self.velocidade = 0

        super().update(delta_time, paredes)
        
        direcao_x = self.jogador.posicao.x - self.posicao.x
        
        self.set_sprite_direction(direcao_x)

        self.atualizar_invisibilidade(delta_time * 1000)

        if self.velocidade > 0:
            self.animar()


