import pygame
import random

from source.enemies.base.enemy_base import BaseEnemy
from source.feats.projetil import PlasmaGun, M50
from source.systems.entitymanager import entity_manager


class Jackal(BaseEnemy): 
    def __init__(self, posicao, game):
        # Sorteio do tipo
        escolhido = random.randint(1, 20)
        if escolhido < 20:
            self.tipo = random.choice(['blue', 'red'])
        else:
            self.tipo = 'sniper'
        if self.tipo in ['blue', 'sniper']:
            self.flip = True
        else:
            self.flip = False
        super().__init__(posicao, vida_base=15, dano_base=10, velocidade_base=50, game=game, sprite_key= 'jackal', flip_sprite=self.flip, variante=self.tipo)

        self.setup_animation(
            estado_inicial='right',
            velocidade_animacao=400
        )

        # Habilidades
        self.plasma_cooldown = self.novo_cooldown(4500, 6000)
        self.escudo_quebrado = False
        self.ultimo_tiro = pygame.time.get_ticks()

    def update(self, delta_time, paredes=None):
        direcao = (self.jogador.posicao - self.posicao)
        mover = (
            direcao.length() > 400
            if self.tipo == 'sniper'
            else True
        )

        if mover:
            self.mover(delta_time)
            if paredes:
                self.aplicar_colisao_mapa(paredes)

        direcao_x = self.jogador.posicao.x - self.posicao.x

        self.set_sprite_direction(direcao_x)

        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro >= self.plasma_cooldown:
            self.plasma_cooldown = self.novo_cooldown(6000, 11000)
            if self.tipo == 'sniper':
                self.sniper()
            else:
                self.plasma()
            self.ultimo_tiro = agora
        
        if self.vida < 0.3 * self.vida_base and not self.escudo_quebrado:
            if self.tipo in ['blue', 'red']:
                self.tipo = f"{self.tipo}_broken"
                self.trocar_variante(self.tipo)
                self.escudo_quebrado = True # Trava o IF para sempre
        self.sync_rect()
        self.animar()
        
    def plasma(self):
        direcao_tiro = self.jogador.posicao - self.posicao
        if direcao_tiro.length() > 0:
            direcao_tiro = direcao_tiro.normalize()
        else:
            direcao_tiro = pygame.math.Vector2(1, 0)
        # Cria uma instância do PlasmaGun
        PlasmaGun(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites,),
            jogador=self.jogador,
            game=self.game,
            dono = 'INIMIGO',
            tamanho=(28,28),
            dano=4,
            velocidade=250,
            direcao_spread = direcao_tiro,
            vai_rotacionar = False
        )

    def sniper(self):
        direcao_tiro = (self.jogador.posicao - self.posicao)
        # Cria uma instância do PlasmaGun
        M50(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites,),
            jogador=self.jogador,
            game=self.game,
            dono = 'INIMIGO',
            tamanho=(45,45),
            dano=50,
            velocidade=750,
            direcao_spread=direcao_tiro
        )