import pygame
import random
import math
from enemies.enemies import InimigoBase
from feats.projetil import *
from feats.items import *
from player import *
from entitymanager import entity_manager


class Jega(InimigoBase):
    def __init__(self, posicao, game):
        valor_vida = 5000
        super().__init__(posicao, vida_base=valor_vida, dano_base=100, velocidade_base= 50, game=game)

        self.titulo = "JEGA 'RDOMNAI, O Matador de Spartans"
        self.game= game
        self.vida = valor_vida     
        self.vida_base = valor_vida
        #sprites
        self.sprites = {}
        #left
        self.sprites['left'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'jega', 'jega1.png')).convert_alpha(), (256, 256)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'jega', 'jega2.png')).convert_alpha(), (256, 256)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'jega', 'jega3.png')).convert_alpha(), (256, 256)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'jega', 'jega4.png')).convert_alpha(), (256, 256)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'jega', 'jega5.png')).convert_alpha(), (256, 256)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'jega', 'jega6.png')).convert_alpha(), (256, 256)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'jega', 'jega7.png')).convert_alpha(), (256, 256))
        ]

        #right
        self.sprites['right'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites['left']
        ]

        # Animação
        self.frame_atual = 0  
        self.estado_animacao = 'left'
        self.indice_animacao = 0
        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center=self.posicao)
        self.velocidade_animacao = 180
        self.ultimo_update_animacao = pygame.time.get_ticks()

        #hitbox
        nova_largura = self.rect.width / 1.3
        self.hitbox = pygame.Rect(0, 0, nova_largura, self.rect.height)
        self.hitbox.center = self.rect.center

        # Estados 
        self.estado = 'perseguindo'
        self.alpha_atual = 255 
        self.ultima_habilidade = pygame.time.get_ticks()
        self.tempo_inicio_estado = pygame.time.get_ticks() # Variável para controlar duração de estados
        self.cooldown_habilidade = 5000   

        # Configurações da Órbita 
        self.angulo_orbita = 0
        self.raio_orbita = 400
        self.velocidade_orbita = 1.3  # Velocidade angular
        self.sentido_orbita = 1     # 1 para horário, -1 para anti-horário
        self.duracao_orbita = 3000  # 4 segundos invisível
        
        # Configurações do Bote 
        self.velocidade_bote = self.velocidade_base * 8
        self.duracao_bote = 1500    # 1 segundo de investida

    
    def morrer(self, grupos = None):
        alvo_grupos = (entity_manager.all_sprites, entity_manager.item_group)
        chance= randint(1,1000)

        # Drop garantido de Shards grandes por ser Boss
        qtd_shards = 2
        if chance > 800: qtd_shards = 4
        elif chance > 600: qtd_shards = 3

        for _ in range(qtd_shards):
            pos_offset = self.posicao + pygame.math.Vector2(random.randint(-30, 30), random.randint(-30, 30))
            Items(posicao=pos_offset, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=alvo_grupos)
        self.kill()

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]

    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        direcao_ao_jogador = (self.jogador.posicao - self.posicao)
        distancia = direcao_ao_jogador.length()

        if self.estado == 'perseguindo':
            self.alpha_atual = 255 
            if distancia > 0:
                self.posicao += direcao_ao_jogador.normalize() * self.velocidade * delta_time
            
            # Se chegar perto, começa a orbitar
            if agora - self.ultima_habilidade > self.cooldown_habilidade and distancia < 600:
                self.estado = 'orbitando'
                self.tempo_inicio_estado = agora
                self.sentido_orbita = random.choice([1, -1])
                self.angulo_orbita = math.atan2(self.posicao.y - self.jogador.posicao.y, 
                                               self.posicao.x - self.jogador.posicao.x)

        elif self.estado == 'orbitando':
            self.hitbox.center = (-1000, -1000) # invulnerável enquanto orbita
            if self.alpha_atual > 0:
                self.alpha_atual -= 20
                if self.alpha_atual < 0: self.alpha_atual = 0
            # Atualiza o ângulo da órbita
            self.angulo_orbita += self.sentido_orbita * self.velocidade_orbita * delta_time
            
            # Define a nova posição ao redor do jogador
            nova_x = self.jogador.posicao.x + math.cos(self.angulo_orbita) * self.raio_orbita
            nova_y = self.jogador.posicao.y + math.sin(self.angulo_orbita) * self.raio_orbita
            self.posicao = pygame.math.Vector2(nova_x, nova_y)

            if agora - self.tempo_inicio_estado > self.duracao_orbita:
                alpha_atual = 255
                self.estado = 'bote'
                self.tempo_inicio_estado = agora

        elif self.estado == 'bote':
            if self.alpha_atual < 255:
                self.alpha_atual += 25
            self.velocidade_animacao = 100
            self.hitbox.center = self.rect.center
            
            # Corre em linha reta na direção que o jogador estava no início do bote
            if distancia > 10:
                self.posicao += direcao_ao_jogador.normalize() * self.velocidade_bote * delta_time
            
            if agora - self.tempo_inicio_estado > self.duracao_bote:
                self.velocidade_animacao = 180
                self.estado = 'perseguindo'
                self.ultima_habilidade = agora 
                self.cooldown_habilidade = random.choice([8000, 9000, 10000])

        # Atualização de Rect e Animação
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        
        if direcao_ao_jogador.x < 0:
            self.estado_animacao = 'left'
        else:
            self.estado_animacao = 'right'
            
        self.animar()
        self.image.set_alpha(self.alpha_atual)
