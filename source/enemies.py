import pygame
import random
from os.path import join
from items import *
from player import *
from settings import *
from projetil import PlasmaGun, Dizimator, Carabin
from items import *


class InimigoBase(pygame.sprite.Sprite):
    def __init__(self, posicao, grupos, jogador, game, vida_base, dano_base, velocidade_base):
        super().__init__(grupos)
        self.game = game
        self.jogador = jogador
        self.vida_base = vida_base
        self.dano_base = dano_base
        self.velocidade_base = velocidade_base
        self.image = pygame.Surface((40, 40))
        self.image.fill('white')
        self.rect = self.image.get_rect(center=posicao)
        self.posicao = pygame.math.Vector2(self.rect.center)
        #settando os status
        self.vida = self.vida_base
        self.dano = self.dano_base
        self.velocidade = self.velocidade_base
        #dificulta baseado no nivel do player
        self.aplicar_dificuldade()
        #garantia de spawn
        self.invencivel = False
        self.tempo_criacao = pygame.time.get_ticks() # Adicionado para uso futuro, se necessário
        self.tempo_invencibilidade = 0

        
    def aplicar_dificuldade(self):
        self.vida *= 1 + self.jogador.contador_niveis / 10
        self.dano *= 1 + self.jogador.contador_niveis / 10
        self.velocidade *= 1 + self.jogador.contador_niveis / 100


    def morrer(self, grupos):
        dado = randint(0, 1000)
        if dado == 1000:
            Items(posicao=self.posicao, sheet_item=join('assets', 'img', 'cafe.png'), tipo='cafe', grupos=grupos)
        elif dado >= 990:
            Items(posicao=self.posicao, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=grupos)
        elif dado >= 970:
            Items(posicao=self.posicao, sheet_item=join('assets', 'img', 'lifeOrb.png'), tipo='life_orb', grupos=grupos)
        else:
            Items(posicao=self.posicao, sheet_item=join('assets', 'img', 'expShard.png'), tipo='exp_shard', grupos=grupos)
        self.kill()

    def update(self, delta_time):
        direcao = self.jogador.rect.center - self.posicao
        if direcao.length() > 0:
            direcao.normalize_ip()
        self.posicao += direcao * self.velocidade * delta_time
        self.rect.center = self.posicao

    @property
    def collision_rect(self):
        """Retorna o retângulo de colisão para este inimigo."""
        return self.rect

class Grunt(InimigoBase):
    def __init__(self, posicao, grupos, jogador, game):
        super().__init__(posicao, grupos, jogador, game, vida_base=4, dano_base=15, velocidade_base=90)
        self.image = pygame.image.load(join('assets', 'img', 'grunt', 'grunt.png')).convert_alpha()
        self.image = pygame.transform.scale(self.image, (100, 80))
        self.rect = self.image.get_rect(center=self.posicao)
        self.velocidade = 70
        self.vida = 2
        self.dano = 15
        #arma
        self.plasma_cooldown = 8000
        self.ultimo_tiro = pygame.time.get_ticks()
        #pre animacao
        self.sprites = {}
        sprites_right = [
            pygame.image.load(join('assets', 'img', 'grunt', 'grunt.png')).convert_alpha(),
            pygame.image.load(join('assets', 'img', 'grunt', 'grunt2.png')).convert_alpha(),
            #pygame.image.load(join('assets', 'img', 'grunt', 'grunt3.png')).convert_alpha()
        ]
        #add esquerda no dict
        self.sprites['right'] = [pygame.transform.scale(sprite, (128, 128)) for sprite in sprites_right]
        #Carrega direita
        sprites_left = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites['right']
        ]
        #add direita no dict
        self.sprites['left'] = sprites_left
        #framagem da sprite
        self.frame_atual = 0  
        self.estado_animacao = 'right'
        self.indice_animacao = 0
        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center=self.posicao)
        self.velocidade_animacao = 200
        self.ultimo_update_animacao = pygame.time.get_ticks()

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.posicao)

    def update(self, delta_time):
        direcao = (self.jogador.posicao - self.posicao)
        if direcao.length() > 0:
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * delta_time
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro >= self.plasma_cooldown:
            novo_cooldown = [8000, 9000, 10000, 11000]
            self.plasma_cooldown = random.choice(novo_cooldown)
            self.plasma()
            self.ultimo_tiro = agora
        if direcao.x < 0:
            self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'
        self.animar()

    def plasma(self):
        # Cria uma instância do PlasmaGun
        PlasmaGun(
            posicao_inicial=self.posicao,
            grupos=(self.game.all_sprites, self.game.projeteis_inimigos_grupo),
            jogador=self.jogador,
            game=self.game,
            tamanho=(12,12),
            dano=5,
            velocidade=250
        )    

class Jackal(InimigoBase):
    def __init__(self, posicao, grupos, jogador, game):
        super().__init__(posicao, grupos, jogador, game, vida_base=2000, dano_base=10, velocidade_base=50)
        #sprites
        #red
        self.sprites_red = {}
        self.sprites_red['right'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'jackal', 'jackred.png')).convert_alpha(), (130,130)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'jackal', 'jackred2.png')).convert_alpha(), (130,130)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'jackal', 'jackred3.png')).convert_alpha(), (130,130))
            ]
        self.sprites_red['left'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites_red['right']
        ]
        #blue
        self.sprites_blue = {}
        self.sprites_blue['left'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'jackal', 'jackblue.png')).convert_alpha(), (150,150)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'jackal', 'jackblue2.png')).convert_alpha(), (150,150)),
            ]
        self.sprites_blue['right'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites_blue['left']
        ]
        #Animação
        self.estado_animacao = 'right'
        self.frame_atual = 0
        self.velocidade_animacao = 400
        self.ultimo_update_animacao = pygame.time.get_ticks()
        cores = [self.sprites_red, self.sprites_blue]
        self.sprites_escolhidas = random.choice(cores)
        self.image = self.sprites_escolhidas[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center=posicao)

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites_escolhidas[self.estado_animacao])
            self.image = self.sprites_escolhidas[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, delta_time):
        direcao = (self.jogador.posicao - self.posicao)
        agora = pygame.time.get_ticks()
        if direcao.length() > 0:
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * delta_time
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        if direcao.x < 0:
            self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'
    
        self.animar()

class Infection(InimigoBase):
    def __init__(self, posicao, grupos, jogador, game):
        super().__init__(posicao, grupos, jogador, game, vida_base=1, dano_base=5, velocidade_base=80)
        #sprites
        self.sprites = {}

        # Carrega e redimensione as sprites da esquerda
        sprites_left = [
            pygame.image.load(join('assets', 'img', 'infection', 'infection1.png')).convert_alpha(),
            pygame.image.load(join('assets', 'img', 'infection', 'infection2.png')).convert_alpha()
        ]
        #add esquerda no dict
        self.sprites['left'] = [pygame.transform.scale(sprite, (100, 100)) for sprite in sprites_left]
        #Carrega direita
        sprites_right = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites['left']
        ]
        #add direita no dict
        self.sprites['right'] = sprites_right
        #framagem da sprite
        self.frame_atual = 0  
        self.estado_animacao = 'left'
        self.indice_animacao = 0
        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center=self.posicao)
        self.velocidade_animacao = 150
        self.ultimo_update_animacao = pygame.time.get_ticks()
    
    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.posicao) # Mantém o centro na mesma posição

    def update(self, delta_time):
        direcao = (self.jogador.posicao - self.posicao)
        if direcao.length() > 0:
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * delta_time
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        if direcao.x < 0:
            self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'
        self.animar()
            
class Brute(InimigoBase):
    def __init__(self, posicao, grupos, jogador, game):
        super().__init__(posicao, grupos, jogador, game, vida_base=30,dano_base=20, velocidade_base=75)
        self.game

        #sprites
        self.sprites = {}
        # Carrega e redimensione as sprites da esquerda
        self.sprites['left'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'brute', 'brute.png')).convert_alpha(),(200,200)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'brute', 'brute2.png')).convert_alpha(),(200,200))
            #pygame.transform.scale(pygame.image.load(join('assets', 'img', 'brute', 'brute3.png')).convert_alpha(),(150,150))

        ]
        #Carrega direita
        self.sprites['right'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites['left']
        ]
        #Animação
        self.estado_animacao = 'right'
        self.frame_atual = 0
        self.velocidade_animacao = 250
        self.ultimo_update_animacao = pygame.time.get_ticks()
        self.image = self.sprites[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center=posicao)

        #Rage
        self.rage = False

        #Dizimadora
        self.cooldown_shot = 3000
        self.ultimo_shot= 0 

    def dizim(self):
        Dizimator(
            posicao_inicial=self.posicao,
            grupos=(self.game.all_sprites, self.game.projeteis_inimigos_grupo),
            jogador=self.jogador,
            game=self.game,
            tamanho=(48,48),
            dano=15,
            velocidade=800)
    
    def morrer(self, grupos):
        for _ in range(3):
            posicao_drop = self.posicao + pygame.math.Vector2(randint(-30, 30), randint(-30, 30))
            Items(posicao=posicao_drop, sheet_item=join('assets', 'img', 'expShard.png'), tipo='exp_shard', grupos=grupos)
        self.kill()

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.posicao)

    def update(self, delta_time):
        direcao = (self.jogador.posicao - self.posicao)
        agora = pygame.time.get_ticks()
        if direcao.length() > 0:
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * delta_time
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        if agora - self.ultimo_shot >= self.cooldown_shot:
            self.ultimo_shot = agora
            novo_cooldown = [5000, 6000, 7000, 8000]
            self.cooldown_shot = random.choice(novo_cooldown)
            self.dizim()
        if self.vida <= self.vida_base / 2 and self.rage == False:
            self.velocidade *= 3
            self.rage = True
        if direcao.x < 0:
            self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'
        self.animar()


class Elite(InimigoBase):
    def __init__(self, posicao, grupos, jogador, game):
        super().__init__(posicao, grupos, jogador, game, vida_base=20,dano_base=20, velocidade_base=90)
        self.game

        #sprites
        self.sprites = {}
        # Carrega e redimensione as sprites da esquerda
        self.sprites['left'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'elite', 'elite.png')).convert_alpha(),(180,180)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'elite', 'elite.png')).convert_alpha(),(180,180))
            #pygame.transform.scale(pygame.image.load(join('assets', 'img', 'brute', 'brute3.png')).convert_alpha(),(150,150))

        ]
        #Carrega direita
        self.sprites['right'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites['left']
        ]
        #Animação
        self.estado_animacao = 'right'
        self.frame_atual = 0
        self.velocidade_animacao = 250
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
            grupos=(self.game.all_sprites, self.game.projeteis_inimigos_grupo),
            jogador=self.jogador,
            game=self.game,
            dano=10,
            velocidade=500,
            tamanho=(12, 12)
        )

    def morrer(self, grupos):
        for _ in range(3):
            posicao_drop = self.posicao + pygame.math.Vector2(randint(-30, 30), randint(-30, 30))
            Items(posicao=posicao_drop, sheet_item=join('assets', 'img', 'expShard.png'), tipo='exp_shard', grupos=grupos)
        self.kill()

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.posicao)

    def update(self, delta_time):
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
        if direcao.length() < 500:
            self.velocidade = 0
        else:
            self.velocidade = self.velocidade_base
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * delta_time
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        if direcao.x < 0:
            self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'
        self.animar()
