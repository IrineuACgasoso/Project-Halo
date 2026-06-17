import pygame
import random
from os.path import join
from source.enemies.base.enemy_base import BaseEnemy
from source.windows.settings import *
from source.feats.items import *
from source.feats.projetil import BurstRifle
from source.feats.effects import DustParticle
from source.systems.entitymanager import entity_manager


class Infection(BaseEnemy):
    def __init__(self, posicao, game):
        super().__init__(posicao, vida_base=1, dano_base=5, velocidade_base=120, game=game, sprite_key='infection')
        
        self.setup_animation(estado_inicial='left', velocidade_animacao=150)

    def update(self, delta_time, paredes=None):
        super().update(delta_time, paredes)
        direcao_x = self.jogador.posicao.x - self.posicao.x
        self.set_sprite_direction(direcao_x)
        self.animar()

class FloodForm(BaseEnemy):
    """Classe base que dita o comportamento padrão, movimento e drops de um Flood."""
    def __init__(self, posicao, game, vida, dano, velocidade, variante, vel_animacao=200):
        super().__init__(
            posicao=posicao, 
            vida_base=vida, 
            dano_base=dano, 
            velocidade_base=velocidade, 
            game=game, 
            sprite_key='infection', # Mantém seu padrão de sprite key
            variante=variante
        )
        self.setup_animation(estado_inicial='right', velocidade_animacao=vel_animacao)

    def update(self, delta_time, paredes=None):
        super().update(delta_time, paredes)
        # Comportamento padrão de perseguição visual
        direcao_x = self.jogador.posicao.x - self.posicao.x
        self.set_sprite_direction(direcao_x)
        self.animar()

    def morrer(self, grupos=None):
        """Drop de itens padrão para as formas comuns (Elite e Marine)."""
        Items.spawn_drop(self.posicao, grupos, 'exp_shard', 1, 100)
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 1, 2)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 1)
        self.kill()


class FloodElite(FloodForm):
    def __init__(self, posicao, game):
        super().__init__(posicao, game, vida=20, dano=20, velocidade=200, variante='elite', vel_animacao=120)


class FloodCarry(FloodForm):
    def __init__(self, posicao, game):
        super().__init__(posicao, game, vida=100, dano=5, velocidade=50, variante='carry')

    def morrer(self, grupos=None):
        """Sobrescreve a morte para dropar o dobro e estourar em Infection Forms."""
        # Drop aprimorado
        Items.spawn_drop(self.posicao, grupos, 'exp_shard', 2, 100)
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 1, 2)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 1)
        
        # Liberação das Infection Forms
        for _ in range(4):
            pos_offset = self.posicao + pygame.math.Vector2(random.randint(-50, 50), random.randint(-50, 50))
            DustParticle(posicao=pos_offset, grupos=entity_manager.all_sprites)
            Infection(posicao=pos_offset, game=self.game)
            
        self.kill()


class FloodMarine(FloodForm):
    def __init__(self, posicao, game):
        super().__init__(posicao, game, vida=20, dano=10, velocidade=100, variante='marine')
        
        # Propriedades da Arma
        self.cooldown_ataque = 2500       
        self.ultimo_ataque = pygame.time.get_ticks()
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
        agora = pygame.time.get_ticks()
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
                    self.cooldown_ataque = self.novo_cooldown(4000, 9000)

    def disparar(self):
        direcao_com_spread = self.calcular_direcao_tiro(0.2)
        BurstRifle(
            posicao_inicial = self.posicao.copy(),
            grupos          = (entity_manager.all_sprites,),
            jogador         = self.jogador,
            game            = self.game,
            dono            = 'INIMIGO',
            tamanho         = (32, 32),
            dano            = 8,
            velocidade      = 700,
            direcao_spread  = direcao_com_spread,
        )