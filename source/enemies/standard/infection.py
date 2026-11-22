import pygame
from source.systems.gameclock import relogio
import random
from os.path import join
from source.enemies.base.enemy_base import BaseEnemy
from source.windows.settings import *
from source.feats.items import *
from source.feats.projetil import BurstRifle
from source.feats.effects import emitir_poeira
from source.systems.entitymanager import entity_manager
from source.data.enemy_data import INIMIGOS


class Infection(BaseEnemy):
    def __init__(self, posicao, game):
        perfil = INIMIGOS['infection']
        super().__init__(posicao, vida_base=perfil.vida, dano_base=perfil.dano, velocidade_base=perfil.velocidade,
                         game=game, sprite_key='infection', flip_sprite=True)
        self.perfil = perfil
        self.tabela_drop = perfil.drops
        
        self.setup_animation(estado_inicial='left', velocidade_animacao=150)

    def update(self, delta_time, paredes=None):
        super().update(delta_time, paredes)
        direcao_x = self.jogador.posicao.x - self.posicao.x
        self.set_sprite_direction(direcao_x)
        self.animar()

class FloodForm(BaseEnemy):
    """Classe base que dita o comportamento padrão, movimento e drops de um Flood."""
    def __init__(self, posicao, game, perfil, variante, vel_animacao=200):
        super().__init__(
            posicao=posicao,
            vida_base=perfil.vida,
            dano_base=perfil.dano,
            velocidade_base=perfil.velocidade,
            game=game, 
            sprite_key='infection', # Mantém seu padrão de sprite key
            variante=variante
        )
        self.perfil = perfil
        self.tabela_drop = perfil.drops
        self.setup_animation(estado_inicial='right', velocidade_animacao=vel_animacao)

    def update(self, delta_time, paredes=None):
        super().update(delta_time, paredes)
        # Comportamento padrão de perseguição visual
        direcao_x = self.jogador.posicao.x - self.posicao.x
        self.set_sprite_direction(direcao_x)
        self.animar()


class FloodElite(FloodForm):
    def __init__(self, posicao, game):
        super().__init__(posicao, game, INIMIGOS['flood_elite'], variante='elite', vel_animacao=120)


class FloodCarry(FloodForm):
    def __init__(self, posicao, game):
        super().__init__(posicao, game, INIMIGOS['flood_carry'], variante='carry')

    def morrer(self, grupos=None):
        """Sobrescreve a morte para dropar o dobro e estourar em Infection Forms."""
        # Drop aprimorado (perfil 'flood_carry')
        Items.spawn_drop(self.posicao, grupos, **self.tabela_drop)
        
        # Liberação das Infection Forms
        for _ in range(4):
            pos_offset = self.posicao + pygame.math.Vector2(random.randint(-50, 50), random.randint(-50, 50))
            emitir_poeira(pos_offset, entity_manager.all_sprites)
            Infection(posicao=pos_offset, game=self.game)
            
        self.kill()


class FloodMarine(FloodForm):
    def __init__(self, posicao, game):
        super().__init__(posicao, game, INIMIGOS['flood_marine'], variante='marine')
        
        # Propriedades da Arma
        self.cooldown_ataque = 2500       
        self.ultimo_ataque = relogio.agora()
        self.tiros_por_rajada = 3         
        self.tiros_dados = 0              
        self.delay_entre_tiros = 150      
        self.ultimo_tiro_rajada = 0
        self.em_rajada = False
        self.distancia_tiro = 400         

    def update(self, delta_time, paredes=None):
        super().update(delta_time, paredes)
        self.marine_burst()

    def marine_burst(self):
        agora = relogio.agora()
        distancia = (self.jogador.posicao - self.posicao).length()

        if not self.em_rajada and distancia < self.distancia_tiro and agora - self.ultimo_ataque > self.cooldown_ataque:
            self.em_rajada = True
            self.tiros_dados = 0
            self.ultimo_tiro_rajada = agora

        if self.em_rajada:
            if agora - self.ultimo_tiro_rajada > self.delay_entre_tiros:
                self.disparar()
                self.tiros_dados += 1
                self.ultimo_tiro_rajada = agora
                
                if self.tiros_dados >= self.tiros_por_rajada:
                    self.em_rajada = False
                    self.ultimo_ataque = agora
                    self.cooldown_ataque = self.novo_cooldown(*self.perfil.cooldowns['rajada'])

    def disparar(self):
        direcao_com_spread = self.calcular_direcao_tiro(0.2)
        BurstRifle(
            posicao_inicial = self.posicao.copy(),
            grupos          = (entity_manager.all_sprites,),
            jogador         = self.jogador,
            game            = self.game,
            dono            = 'INIMIGO', fonte=self,
            tamanho         = (32, 32),
            dano            = 8,
            velocidade      = 700,
            direcao_spread  = direcao_com_spread,
        )