import pygame
import random
from os.path import join
from source.enemies.enemies import InimigoBase
from source.player.player import *
from source.windows.settings import *
from source.feats.projetil import PlasmaGun, M50
from source.feats.items import *
from source.feats.assets import ASSETS
from source.systems.entitymanager import entity_manager


class Jackal(InimigoBase):
    def __init__(self, posicao, game):
        super().__init__(posicao, vida_base=15, dano_base=10, velocidade_base=50, game=game, sprite_key= 'jackal')

        # Sorteio do tipo
        escolhido = random.randint(1, 20)
        if escolhido < 20:
            self.tipo = random.choice(['blue', 'red'])
        else:
            self.tipo = 'sniper'

        self.sprites_escolhidas = self.get_sprites(self.tipo)

        #Animação
        self.estado_animacao = 'right'
        self.frame_atual = 0
        self.velocidade_animacao = 400
        self.ultimo_update_animacao = pygame.time.get_ticks()

        self.image = self.sprites_escolhidas[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center=posicao)

        # Habilidades
        self.plasma_cooldown = 5000
        self.escudo_quebrado = False
        self.ultimo_tiro = pygame.time.get_ticks()

        
    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites_escolhidas[self.estado_animacao])
            self.image = self.sprites_escolhidas[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, delta_time, paredes=None):
        direcao = (self.jogador.posicao - self.posicao)
        if direcao.length() > 0:
            if (direcao.length() > 400 and self.tipo == 'sniper') or not self.tipo == 'sniper':
                direcao.normalize_ip()
                self.posicao += direcao * self.velocidade * delta_time
                if paredes:
                    self.aplicar_colisao_mapa(paredes, self.raio_colisao_mapa)
                self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro >= self.plasma_cooldown:
            novo_cooldown = [6000, 8000, 10000, 11000]
            self.plasma_cooldown = random.choice(novo_cooldown)
            if self.tipo == 'sniper':
                self.sniper()
            else:
                self.plasma()
            self.ultimo_tiro = agora
        if direcao.x < 0:
            self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'
        
        self.animar()
        
        if self.vida < 0.3 * self.vida_base and not self.escudo_quebrado:
            if self.tipo in ['blue', 'red']:
                self.tipo = f"{self.tipo}_broken"
                self.sprites_escolhidas = self.get_sprites(self.tipo)
                self.frame_atual = 0
                self.escudo_quebrado = True # Trava o IF para sempre
            
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