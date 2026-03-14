import pygame
import random
import math
from os.path import join
from enemies.enemies import InimigoBase
from feats.effects import ContinuousBeam
from feats.assets import ASSETS
from systems.entitymanager import entity_manager

class Sentinel(InimigoBase):
    def __init__(self, posicao, game):
        super().__init__(posicao, vida_base=20, dano_base=10, velocidade_base=90, game=game, sprite_key='sentinel')
        self.game = game
        self.estado_ia = 'chase'
        
        # Sprites
        self.sprites = {}
        # Right
        self.sprites = self.get_sprites('default')
        self.estado_animacao = 'left'
        self.indice_animacao = 0
        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center=self.posicao)

        # Configurações de Órbita
        self.distancia_gatilho_orbita = 350 
        self.distancia_minima_seguranca = 300 # Se estiver mais perto que isso, ela se afasta
        self.raio_orbita_atual = 300
        self.angulo_atual = 0
        self.centro_orbita_fixo = pygame.math.Vector2(0, 0)
        
        # Laser
        self.beam_ativo = False
        self.duracao_beam = 2000
        self.cooldown_pos_ataque = 2000 
        self.timer_estado = 0
        
        self.laser = ContinuousBeam(self, color=(255, 255, 180), largura_base=3, dano_por_segundo=10, suavizacao=0.05)
        self.velocidade_mira = 0.05


    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()
        vetor_player = self.jogador.posicao - self.posicao
        distancia = vetor_player.length()
        
        if self.estado_ia == 'chase':
            self.indice_animacao = 0
            # Lógica de movimentação
            if distancia > self.distancia_gatilho_orbita:
                direcao = vetor_player.normalize()
                self.posicao += direcao * self.velocidade * delta_time
            elif distancia < self.distancia_minima_seguranca:
                if distancia > 0:
                    direcao_fuga = -vetor_player.normalize()
                    self.posicao += direcao_fuga * self.velocidade * delta_time
            
            # Troca para órbita/ataque
            if agora - self.timer_estado >= self.cooldown_pos_ataque:
                if self.distancia_minima_seguranca <= distancia <= self.distancia_gatilho_orbita:
                    self.estado_ia = 'orbiting'
                    self.timer_estado = agora
                    self.beam_ativo = True
                    self.indice_animacao = 1
                    self.centro_orbita_fixo = pygame.math.Vector2(self.jogador.posicao)
                    self.raio_orbita_atual = (self.posicao - self.centro_orbita_fixo).length()
                    self.angulo_atual = math.atan2(self.posicao.y - self.centro_orbita_fixo.y, 
                                                 self.posicao.x - self.centro_orbita_fixo.x)

        elif self.estado_ia == 'orbiting':
            self.angulo_atual += 0.3 * delta_time 
            self.posicao.x = self.centro_orbita_fixo.x + math.cos(self.angulo_atual) * self.raio_orbita_atual
            self.posicao.y = self.centro_orbita_fixo.y + math.sin(self.angulo_atual) * self.raio_orbita_atual
            
            # O LASER ATUALIZA A MIRA AQUI DENTRO:
            self.laser.update(delta_time, self.jogador.posicao)

            if agora - self.timer_estado >= self.duracao_beam:
                self.estado_ia = 'chase'
                self.timer_estado = agora
                self.beam_ativo = False
                self.indice_animacao = 0

        if (self.jogador.posicao.x - self.posicao.x) < 0: 
            self.estado_animacao = 'left'
        else: 
            self.estado_animacao = 'right'

        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        self.animar()

    # MUDE o draw_laser para usar o objeto self.laser:
    def draw_laser(self, superficie, deslocamento):
        if self.beam_ativo:
            # Agora usa a classe nova, mantendo o padrão do Scarab
            self.laser.draw(superficie, deslocamento)
        
    def animar(self):
        self.image = self.sprites[self.estado_animacao][self.indice_animacao]