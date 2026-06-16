import pygame
import math

from source.enemies.base.enemy_base import BaseEnemy
from source.feats.effects import ContinuousBeam
from source.feats.auras import EnergyAura

class Sentinel(BaseEnemy):
    def __init__(self, posicao, game, variante='default'):
        super().__init__(posicao, vida_base=20, dano_base=10, velocidade_base=90, game=game, sprite_key='sentinel', variante=variante)
        self.setup_animation(
            estado_inicial='left',
            velocidade_animacao=200
        )

        self.indice_animacao = 0

        self.estado_ia = 'chase'
        
        # Configurações de Órbita
        self.distancia_gatilho_orbita = 350 
        self.distancia_minima_seguranca = 300 # Se estiver mais perto que isso, ele se afasta
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

    def animar(self):
        self.set_image(self.sprites[self.estado_animacao][self.indice_animacao])

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
                    self.angulo_atual = math.atan2(
                        self.posicao.y - self.centro_orbita_fixo.y, 
                        self.posicao.x - self.centro_orbita_fixo.x
                        )

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

        direcao_x = (self.jogador.posicao.x - self.posicao.x)

        self.set_sprite_direction(direcao_x)

        if paredes:
            self.aplicar_colisao_mapa(paredes)
        
        self.sync_rect()

        self.animar()

    # MUDE o draw_laser para usar o objeto self.laser:
    def draw_laser(self, superficie, deslocamento):
        if self.beam_ativo:
            # Agora usa a classe nova, mantendo o padrão do Scarab
            self.laser.draw(superficie, deslocamento)
        

class SentinelMajor(Sentinel):
    def __init__(self, posicao, game):
        # Inicia como um Sentinel normal
        super().__init__(posicao, game, variante='major')
        self.titulo = "MAJOR SENTINEL"
        # SOBRESCREVE OS ATRIBUTOS PARA A VERSÃO ELITE
        self.laser.dano_por_segundo *= 4 # Laser do Major machuca mais!
        self.adicionar_escudo(self.vida_base * 2)
        
        # AURA AMARELA (Não empurra, mas dá dano se encostar)
        self.aura = EnergyAura(
            owner=self, 
            raio=60,               # Ajuste o tamanho da aura da sentinela aqui
            dano_contato=5, 
            game=self.game, 
            cor_base=(255, 200, 0), # Amarelão dourado
            impenetravel=False      # Permite que o jogador atravesse a aura
        )

    def update(self, delta_time, paredes=None):
        super().update(delta_time, paredes)

        # 2. Verifica se o escudo quebrou
        if hasattr(self, 'escudo_atual') and self.escudo_atual <= 0:
            # Se a aura ainda estiver viva no grupo de sprites, nós a destruímos
            if self.aura and self.aura.alive():
                self.aura.kill()