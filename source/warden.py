import pygame
from game import *
from items import *
from enemies import *
from player import *
import random
import math

class WardenEternal(InimigoBase):
    def __init__(self, posicao, grupos, jogador, game, clone = False):
        super().__init__(posicao, grupos, jogador, game, vida_base=1000, dano_base=90, velocidade_base=80)
        self.game = game
        self.grupos = grupos
        #sprites
        #original
        if clone == False:
            self.sprites = {}
            self.sprites['left'] = [
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'warden', 'warden.png')).convert_alpha(), (550,550)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'warden', 'warden2.png')).convert_alpha(), (550,550)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'warden', 'warden3.png')).convert_alpha(), (550,550))
                
                ]
            self.sprites['right'] = [
                pygame.transform.flip(sprite, True, False) for sprite in self.sprites['left']
            ]
        #clone
        else:
            self.sprites = {}
            self.sprites['left'] = [
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'warden', 'clone2.png')).convert_alpha(), (500,500)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'warden', 'clone.png')).convert_alpha(), (500,500)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'warden', 'clone3.png')).convert_alpha(), (500,500))
                
                ]
            self.sprites['right'] = [
                pygame.transform.flip(sprite, True, False) for sprite in self.sprites['left']
            ]

        # Inicia a animação
        self.frame_atual = 0
        self.estado_animacao = 'right' 
        self.velocidade_animacao = 300 # Milissegundos por frame
        self.ultimo_update_animacao = pygame.time.get_ticks()
        
        # Define a imagem e o retângulo inicial
        self.image = self.sprites[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center=self.posicao)

        # Cria a hitbox do warden
        self.mask = pygame.mask.from_surface(self.image)


        #Clone
        if not clone:
            self.clones_restantes = 2
        else:
            self.clones_restantes = 0
        self.vida_limite = 0.66 * self.vida_base

    @property
    def collision_rect(self):
        return self.mask
    
    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.posicao)
            # Recrie a hitbox aqui para que ela se adapte ao novo tamanho
            self.hitbox = pygame.Rect(0, 0, self.rect.width * 0.6, self.rect.height * 0.9)
            self.hitbox.center = self.rect.center

    def clonar(self):
        # Cria dois novos clones
        for _ in range(2):
            # Posiciona os clones um pouco distantes do original
            posicao_clone = self.posicao + pygame.math.Vector2(random.randint(-700, 700), random.randint(-700, 700))
            
            # Instancia o clone com 'clone=True'
            clone = WardenEternal(
                posicao=posicao_clone,
                grupos=self.grupos,
                jogador=self.jogador,
                game=self.game,
                clone=True
            )
            # Adiciona o clone ao grupo de inimigos
            self.game.inimigos_grupo.add(clone)
        # Zera os clones restantes para que o boss não clone novamente
        self.clones_restantes = 0

    def morrer(self, grupos):
        chance= randint(1,1000)
        if chance >= 950:
            Items(posicao=self.posicao, sheet_item=join('assets', 'img', 'cafe.png'), tipo='cafe', grupos=grupos)
            for _ in range(5):
                posicao_drop = self.posicao + pygame.math.Vector2(randint(-30, 30), randint(-30, 30))
                Items(posicao=posicao_drop, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=grupos)
        elif 800 <= chance < 950:
            chance2 = randint(1,4)
            if chance2 == 4:
                Items(posicao=self.posicao, sheet_item=join('assets', 'img', 'cafe.png'), tipo='cafe', grupos=grupos)
            for _ in range(4):
                posicao_drop = self.posicao + pygame.math.Vector2(randint(-30, 30), randint(-30, 30))
                Items(posicao=posicao_drop, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=grupos)
        elif 500 <= chance < 800:
            for _ in range(3):
                posicao_drop = self.posicao + pygame.math.Vector2(randint(-30, 30), randint(-30, 30))
                Items(posicao=posicao_drop, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=grupos)
        else:
            for _ in range(2):
                posicao_drop = self.posicao + pygame.math.Vector2(randint(-30, 30), randint(-30, 30))
                Items(posicao=posicao_drop, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=grupos)
        self.kill()

    def update(self, delta_time):
        direcao = (self.jogador.posicao - self.posicao)
        if direcao.length() > 0:
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * delta_time
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        # Lógica de criação de clones
        if self.clones_restantes > 0 and self.vida <= self.vida_limite:
            self.clonar()
        if direcao.x < 0:
                self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'
        self.animar()

    