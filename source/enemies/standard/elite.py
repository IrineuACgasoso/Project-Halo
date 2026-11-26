import pygame
from source.systems.gameclock import relogio
import random
from os.path import join
from source.enemies.base.enemy_base import BaseEnemy
from source.windows.settings import *
from source.feats.projetil import Carabin
from source.feats.items import *
from source.feats.assets import ASSETS
from source.systems.entitymanager import entity_manager
from source.data.enemy_data import INIMIGOS


class EliteBase(BaseEnemy):
    """Classe base que dita o comportamento padrão, movimento e drops de um Elite."""
    def __init__(self, posicao, game, perfil, variante, vel_animacao=200):
        super().__init__(
            posicao=posicao,
            vida_base=perfil.vida,
            dano_base=perfil.dano,
            velocidade_base=perfil.velocidade,  
            game=game, 
            sprite_key='elite', # Mantém seu padrão de sprite key
            variante=variante
        )
        self.perfil = perfil
        self.tabela_drop = perfil.drops
        self.setup_animation(estado_inicial='right', velocidade_animacao=vel_animacao)

        #Carabin
        self.cooldown_carabin = 4000
        self.intervalo_carabina = 75

        self.cronometro_carabina = 0
        self.ultima_carabina = 0

        self.carabina_restante = 0
        self.contagem_carabina = 5

        # Metade da vida vira escudo; quando ele quebra, a camuflagem liga (ao_quebrar_escudo)
        metade = self.vida_base / 2
        self.vida_maxima = self.vida = self.vida_base - metade
        self.adicionar_escudo(metade)
        self.vida_critica = False

    def ao_quebrar_escudo(self):
        """Escudo quebrado: camuflagem ativa e o dobro da velocidade (uma vez só)."""
        super().ao_quebrar_escudo()
        if not self.vida_critica:
            self.vida_critica = True
            self.velocidade_base *= 2
            self.iniciar_invisibilidade('elite')

    def carabin(self):
        # Calculamos a direção para o jogador
        direcao_tiro = self.calcular_direcao_tiro(0.02)

        self.trigger_flash(duracao=35,bonus_alpha=60)

        Carabin(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites,), # A base adiciona o grupo de inimigos sozinha agora
            jogador=self.jogador,
            game=self.game,
            dono = 'INIMIGO', fonte=self,
            tamanho=(42, 42), 
            dano=10,
            velocidade=600,
            direcao_spread=direcao_tiro
        )

    def update(self, delta_time, paredes=None):
        direcao = (self.jogador.posicao - self.posicao)
        agora = relogio.agora()
        #Ativa carabina
        if agora - self.ultima_carabina >= self.cooldown_carabin:
            self.carabina_restante = self.contagem_carabina
            self.cooldown_carabin = self.novo_cooldown(*self.perfil.cooldowns['carabina'])
            self.ultima_carabina = agora
        #Atira carabina
        if self.carabina_restante > 0:
            self.cronometro_carabina += delta_time * 1000
            if self.cronometro_carabina >= self.intervalo_carabina:
                self.cronometro_carabina = 0
                self.carabina_restante -= 1
                self.carabin()

        if direcao.length_squared() >= 122500:
            self.velocidade = self.velocidade_base
        else:
            self.velocidade = 0

        super().update(delta_time, paredes)
        
        direcao_x = self.jogador.posicao.x - self.posicao.x
        
        self.set_sprite_direction(direcao_x)

        self.atualizar_invisibilidade(delta_time)

        if self.velocidade > 0:
            self.animar()


class Elite(EliteBase):
    def __init__(self, posicao, game):
        super().__init__(posicao, game, INIMIGOS['elite'], variante='default', vel_animacao=200)


class ReachElite(EliteBase):
    def __init__(self, posicao, game):
        super().__init__(posicao, game, INIMIGOS['reach_elite'], variante='reach', vel_animacao=120)


class Halo4Elite(EliteBase):
    def __init__(self, posicao, game):
        super().__init__(posicao, game, INIMIGOS['halo4_elite'], variante='h4', vel_animacao=180)


