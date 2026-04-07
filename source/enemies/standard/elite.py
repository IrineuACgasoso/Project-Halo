import pygame
import random
from os.path import join
from source.enemies.enemies import InimigoBase
from source.player.player import *
from source.windows.settings import *
from source.feats.projetil import Carabin
from source.feats.items import *
from source.feats.assets import ASSETS
from source.systems.entitymanager import entity_manager


class Elite(InimigoBase):
    def __init__(self, posicao, game):
        super().__init__(posicao, vida_base=30,dano_base=20, velocidade_base=90, game=game, sprite_key='elite')
        self.game

        #sprites
        self.sprites = self.get_sprites('default')
        #Animação
        self.estado_animacao = 'right'
        self.frame_atual = 0
        self.velocidade_animacao = 150
        self.ultimo_update_animacao = pygame.time.get_ticks()
        self.image = self.sprites[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center=posicao)

        #Carabin
        self.cooldown_carabin = 4000
        self.intervalo_carabina = 75
        self.cronometro_carabina = 0
        self.ultima_carabina = 0
        self.carabina_restante = 0
        self.contagem_carabina = 5

        #Invisibilidade
        self.vida_critica = False

    def carabin(self):
        Carabin(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites, entity_manager.projeteis_inimigos_grupo),
            jogador=self.jogador,
            game=self.game,
            dano=10,
            velocidade=500,
            tamanho=(12, 12)
        )

    def morrer(self, grupos = None):
        Items.spawn_drop(self.posicao, grupos, 'exp_shard', 3, 100)
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 1, 2)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 1)
        self.kill()

    def animar(self):
        if self.velocidade > 0:
            agora = pygame.time.get_ticks()
            if agora - self.ultimo_update_animacao > self.velocidade_animacao:
                self.ultimo_update_animacao = agora
                self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
                self.image = self.sprites[self.estado_animacao][self.frame_atual]
                self.rect = self.image.get_rect(center=self.posicao)

    def update(self, delta_time, paredes=None):
        direcao = (self.jogador.posicao - self.posicao)
        agora = pygame.time.get_ticks()
        #Ativa invisibi
        if self.vida <= self.vida_base / 2 and self.vida_critica == False:
            self.vida_critica = True
            self.velocidade *= 2
            self.image.set_alpha(0)
        #Ativa carabina
        if agora - self.ultima_carabina >= self.cooldown_carabin:
            self.carabina_restante = self.contagem_carabina
            novo_cooldown_carabina = [3000, 4000, 5000, 6000]
            self.cooldown_carabin = random.choice(novo_cooldown_carabina)
            self.ultima_carabina = agora
        #Atira carabina
        if self.carabina_restante > 0:
            if self.vida_critica:
                self.image.set_alpha(100)
            self.cronometro_carabina += delta_time * 1000
            if self.cronometro_carabina >= self.intervalo_carabina:
                self.cronometro_carabina = 0
                self.carabina_restante -= 1
                self.carabin()
        else:
            if self.vida_critica:
                self.image.set_alpha(0)
        if direcao.length() < 350:
            self.velocidade = 0
        else:
            self.velocidade = self.velocidade_base
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * delta_time
            if paredes:
                self.aplicar_colisao_mapa(paredes, self.raio_colisao_mapa)
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        if direcao.x < 0:
            self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'
        self.animar()
