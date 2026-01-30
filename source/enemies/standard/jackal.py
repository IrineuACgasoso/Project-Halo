import pygame
import random
from os.path import join
from enemies.enemies import InimigoBase
from player import *
from settings import *
from feats.projetil import PlasmaGun, M50
from feats.items import *
from entitymanager import entity_manager


class Jackal(InimigoBase):
    def __init__(self, posicao, game):
        super().__init__(posicao, vida_base=15, dano_base=10, velocidade_base=50, game=game)

        # Sprites

        # ==========
        # RED JACKAL
        # ==========

        self.is_Red = False
        self.sprites_red = {}
        self.sprites_red['right'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'red', 'red1.png')).convert_alpha(), (160,160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'red', 'red2.png')).convert_alpha(), (160,160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'red', 'red3.png')).convert_alpha(), (160,160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'red', 'red4.png')).convert_alpha(), (160,160))
            ]
        self.sprites_red['left'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites_red['right']
        ]

        # RED BROKEN SHIELD

        self.sprites_red_broken = {}
        self.sprites_red_broken['right'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'red', 'red5.png')).convert_alpha(), (160,160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'red', 'red6.png')).convert_alpha(), (160,160)),            
        ]

        self.sprites_red_broken['left'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites_red_broken['right']
        ]


        # ===========
        # BLUE JACKAL
        # ===========

        self.is_Blue = False
        self.sprites_blue = {}
        self.sprites_blue['left'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'blue', 'blue1.png')).convert_alpha(), (120,120)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'blue', 'blue2.png')).convert_alpha(), (120,120)),
            ]
        self.sprites_blue['right'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites_blue['left']
        ]

        # BLUE BROKEN SHIELD

        self.sprites_blue_broken = {}
        self.sprites_blue_broken['left'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'blue', 'blue3.png')).convert_alpha(), (120,120)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'blue', 'blue4.png')).convert_alpha(), (120,120)),            
        ]

        self.sprites_blue_broken['right'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites_blue_broken['left']
        ]

        # Sniper
        self.is_Sniper = False
        self.sprites_sniper = {}
        self.sprites_sniper['left'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'sniper', 'sniper1.png')).convert_alpha(), (100,100)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'sniper', 'sniper2.png')).convert_alpha(), (100,100)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'sniper', 'sniper3.png')).convert_alpha(), (100,100)),
            ]
        
        self.sprites_sniper['right'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites_sniper['left']
        ]
        #Animação
        self.estado_animacao = 'right'
        self.frame_atual = 0
        self.velocidade_animacao = 400
        self.ultimo_update_animacao = pygame.time.get_ticks()

        # Faz um pequeno sorteio para escolher o tipo de jackal
        cores = [self.sprites_blue, self.sprites_red]
        self.escolhido = randint(1, 20)
        if self.escolhido < 20:
            self.sprites_escolhidas = random.choice(cores)
        else:
            self.sprites_escolhidas = self.sprites_sniper

        self.image = self.sprites_escolhidas[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center=posicao)

        # Habilidades
        self.plasma_cooldown = 5000
        self.ultimo_tiro = pygame.time.get_ticks()

        # Tipo de jackal
        if self.sprites_escolhidas == self.sprites_sniper:
            self.is_Sniper = True

        elif self.sprites_escolhidas == self.sprites_blue:
            self.is_Blue = True

        else:
            self.is_Red = True
            self.velocidade_animacao = 200

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
            if (direcao.length() > 400 and self.is_Sniper) or not self.is_Sniper:
                direcao.normalize_ip()
                self.posicao += direcao * self.velocidade * delta_time
                if paredes:
                    self.aplicar_colisao_mapa(paredes, self.raio_colisao_mapa)
                self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro >= self.plasma_cooldown:
            novo_cooldown = [6000, 8000, 10000, 11000]
            self.plasma_cooldown = random.choice(novo_cooldown)
            if self.is_Sniper:
                self.sniper()
            else:
                self.plasma()
            self.ultimo_tiro = agora
        if direcao.x < 0:
            self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'
        
        if self.vida < 0.3 * self.vida_base:
            if self.is_Blue:
                self.sprites_escolhidas = self.sprites_blue_broken
            elif self.is_Red:
                self.sprites_escolhidas = self.sprites_red_broken
                self.velocidade_animacao = 400
    
        self.animar()

    def plasma(self):
        # Cria uma instância do PlasmaGun
        PlasmaGun(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites, entity_manager.projeteis_inimigos_grupo),
            jogador=self.jogador,
            game=self.game,
            tamanho=(12,12),
            dano=8,
            velocidade=250
        )

    def sniper(self):
        # Cria uma instância do PlasmaGun
        M50(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites, entity_manager.projeteis_inimigos_grupo),
            jogador=self.jogador,
            game=self.game,
            tamanho=(45,45),
            dano=50,
            velocidade=750
        )