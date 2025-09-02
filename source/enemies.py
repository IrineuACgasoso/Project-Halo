import pygame
from os.path import join
from random import randint
from items import *
from player import *
from settings import *


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
        if 13 >= self.jogador.contador_niveis > 8:
            self.vida *= self.jogador.contador_niveis / 5
            self.dano *= self.jogador.contador_niveis / 5
        elif 18 >= self.jogador.contador_niveis > 13:
            self.vida *= self.jogador.contador_niveis / 2
            self.dano *= self.jogador.contador_niveis / 2
            self.velocidade *= self.jogador.contador_niveis / 10
        elif 30 >= self.jogador.contador_niveis > 18:
            self.vida *= self.jogador.contador_niveis
            self.dano *= self.jogador.contador_niveis
            self.velocidade *= self.jogador.contador_niveis / 15
        elif self.jogador.contador_niveis > 30:
            self.constante_lategame = self.jogador.contador_niveis - 15
            self.vida *= self.constante_lategame * (self.jogador.contador_niveis)
            self.dano *= self.constante_lategame * (self.jogador.contador_niveis)
            self.velocidade *= self.jogador.contador_niveis / 10

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
    
class ProjetilInimigoBase(pygame.sprite.Sprite):
    def __init__(self, posicao_inicial, grupos, jogador, game, dano, velocidade, duracao):
        super().__init__(grupos)
        self.jogador = jogador
        self.game = game
        self.posicao = pygame.math.Vector2(posicao_inicial)
        
        #status
        self.dano = dano
        self.velocidade = velocidade
        self.duracao = duracao

        # Aparência
        self.image = pygame.Surface((20,20))
        self.rect = self.image.get_rect(center=self.posicao)

        # Calcula a direção para o jogador
        direcao_para_jogador = self.jogador.posicao - self.posicao
        if direcao_para_jogador.length() > 0:
            self.direcao = direcao_para_jogador.normalize()
        else:
            self.direcao = pygame.math.Vector2(0, 0)
        
        self.tempo_criacao = pygame.time.get_ticks()

    def update(self, delta_time):
        self.posicao += self.direcao * self.velocidade * delta_time
        self.rect.center = self.posicao
        
        # Mata o projétil se o tempo de vida se esgotar
        if pygame.time.get_ticks() - self.tempo_criacao >= self.duracao:
            self.kill()



class InimigoBug(InimigoBase):
    def __init__(self, posicao, grupos, jogador, game):
        super().__init__(posicao, grupos, jogador, game, vida_base=1, dano_base=10, velocidade_base=110)
        spritesheet = pygame.image.load(join('assets', 'img', 'bug.png'))
        self.animacoes = self.fatiar_spritesheet(spritesheet)
        self.estado_animacao = 'down'
        self.frame_atual = 0
        self.velocidade_animacao = 150
        self.ultimo_update_animacao = pygame.time.get_ticks()
        self.image = self.animacoes[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center=posicao)
        
    def fatiar_spritesheet(self, sheet):
        largura_frame = 32
        altura_frame = 32
        animacoes = {'up': [], 'left': [], 'right': [], 'down': []}
        for linha, nome_animacao in enumerate(['down', 'left', 'right', 'up']):
            for coluna in range(4):
                x = coluna * largura_frame
                y = linha * altura_frame
                frame = sheet.subsurface(pygame.Rect(x, y, largura_frame, altura_frame))
                frame_escalado = pygame.transform.scale(frame, (100, 100))
                animacoes[nome_animacao].append(frame_escalado)
        return animacoes

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.animacoes[self.estado_animacao])
            self.image = self.animacoes[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, delta_time):
        direcao = (self.jogador.posicao - self.posicao).normalize() if (self.jogador.posicao - self.posicao).length() > 0 else pygame.math.Vector2()
        self.posicao += direcao * self.velocidade * delta_time
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        if abs(direcao.y) > abs(direcao.x):
            self.estado_animacao = 'up' if direcao.y < 0 else 'down'
        elif abs(direcao.x) > 0:
            self.estado_animacao = 'left' if direcao.x < 0 else 'right'
        self.animar()


class Grunt(InimigoBase):
    def __init__(self, posicao, grupos, jogador, game):
        super().__init__(posicao, grupos, jogador, game, vida_base=2, dano_base=15, velocidade_base=90)
        self.image = pygame.image.load(join('assets', 'img', 'grunt', 'grunt.png')).convert_alpha()
        self.image = pygame.transform.scale(self.image, (100, 80))
        self.rect = self.image.get_rect(center=self.posicao)
        self.velocidade = 70
        self.vida = 2
        self.dano = 15
        #arma
        self.plasma_cooldown = 4000
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
            self.atacar_com_projetil()
            self.ultimo_tiro = agora
        if direcao.x < 0:
            self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'
        self.animar()

    def atacar_com_projetil(self):
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

class PlasmaGun(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, tamanho, dano, velocidade):
        super().__init__(posicao_inicial, grupos, jogador, game, dano=dano, velocidade=velocidade, duracao=5000)
        self.image = pygame.image.load(join('assets', 'img', 'plasmagun.png'))
        self.image = pygame.transform.scale(self.image, tamanho)
        self.rect = self.image.get_rect(center=self.posicao)
        self.mask = pygame.mask.from_surface(self.image)

class Carabin(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, tamanho, dano, velocidade, duracao =4000):
        super().__init__(posicao_inicial, grupos, jogador, game, dano=dano, velocidade=velocidade, duracao=duracao)
        self.image = pygame.image.load(join('assets', 'img', 'carabin.png'))
        self.image = pygame.transform.scale(self.image, tamanho)
        self.rect = self.image.get_rect(center=self.posicao)
        self.mask = pygame.mask.from_surface(self.image)


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
            
class InimigoPython(InimigoBase):
    def __init__(self, posicao, grupos, jogador, game):
        super().__init__(posicao, grupos, jogador, game, vida_base=1,dano_base=10, velocidade_base=75)
        spritesheet = pygame.image.load(join('assets', 'img', 'python.png'))
        self.image = pygame.transform.scale(spritesheet, (600, 600))
        self.animacoes = self.fatiar_spritesheet(self.image)
        self.estado_animacao = 'down'
        self.frame_atual = 0
        self.velocidade_animacao = 150
        self.ultimo_update_animacao = pygame.time.get_ticks()
        self.image = self.animacoes[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center=posicao)

    def fatiar_spritesheet(self, sheet):
        largura_frame = 150
        altura_frame = 150
        animacoes = {'up': [], 'left': [], 'right': [], 'down': []}
        for linha, nome_animacao in enumerate(['down', 'left', 'right', 'up']):
            for coluna in range(4):
                x = coluna * largura_frame
                y = linha * altura_frame
                frame = sheet.subsurface(pygame.Rect(x, y, largura_frame, altura_frame))
                frame_escalado = pygame.transform.scale(frame, (100, 100))
                animacoes[nome_animacao].append(frame_escalado)
        return animacoes

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.animacoes[self.estado_animacao])
            self.image = self.animacoes[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, delta_time):
        direcao = (self.jogador.posicao - self.posicao).normalize() if (self.jogador.posicao - self.posicao).length() > 0 else pygame.math.Vector2()
        self.posicao += direcao * self.velocidade * delta_time
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        if abs(direcao.y) > abs(direcao.x):
            self.estado_animacao = 'up' if direcao.y < 0 else 'down'
        elif abs(direcao.x) > 0:
            self.estado_animacao = 'left' if direcao.x < 0 else 'right'
        self.animar()

class InimigoLadrao(InimigoBase):
    def __init__(self, posicao, grupos, jogador, game):
        super().__init__(posicao, grupos, jogador, game, vida_base= 25, dano_base=1, velocidade_base=300)
        spritesheet = pygame.image.load(join('assets', 'img', 'ladrao.png'))
        self.image = pygame.transform.scale(spritesheet, (600, 600))
        self.animacoes = self.fatiar_spritesheet(self.image)
        self.estado_animacao = 'down'
        self.frame_atual = 0
        self.velocidade_animacao = 150
        self.ultimo_update_animacao = pygame.time.get_ticks()
        self.image = self.animacoes[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center=posicao)

    def fatiar_spritesheet(self, sheet):
        largura_frame = 150
        altura_frame = 150
        animacoes = {'up': [], 'left': [], 'right': [], 'down': []}
        for linha, nome_animacao in enumerate(['down', 'left', 'right', 'up']):
            for coluna in range(4):
                x = coluna * largura_frame
                y = linha * altura_frame
                frame = sheet.subsurface(pygame.Rect(x, y, largura_frame, altura_frame))
                frame_escalado = pygame.transform.scale(frame, (100, 100))
                animacoes[nome_animacao].append(frame_escalado)
        return animacoes

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.animacoes[self.estado_animacao])
            self.image = self.animacoes[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, delta_time):
        direcao = (self.jogador.posicao - self.posicao).normalize() if (self.jogador.posicao - self.posicao).length() > 0 else pygame.math.Vector2()
        self.posicao += direcao * self.velocidade * delta_time
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        if abs(direcao.y) > abs(direcao.x):
            self.estado_animacao = 'up' if direcao.y < 0 else 'down'
        elif abs(direcao.x) > 0:
            self.estado_animacao = 'left' if direcao.x < 0 else 'right'
        self.animar()