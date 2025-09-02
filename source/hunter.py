import pygame
from game import *
from enemies import *
from player import *
import random

class Hunter(InimigoBase):
    def __init__(self, posicao, grupos, jogador, game):
        super().__init__(posicao, grupos, jogador, game, vida_base=250, dano_base=40, velocidade_base=55)
        self.game = game

        #sprites
        self.sprites = {}
        #left
        self.sprites['left'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'hunter','hunter.png')).convert_alpha(), (250, 250)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'hunter','hunter2.png')).convert_alpha(), (270, 270))
            ]
        #right
        self.sprites['right'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites['left']
            ]

        #framagem da sprite
        self.frame_atual = 0  
        self.estado_animacao = 'right'
        self.indice_animacao = 0
        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center=self.posicao)
        self.velocidade_animacao = 250
        self.ultimo_update_animacao = pygame.time.get_ticks()

        #hitbox
        self.mask = pygame.mask.from_surface(self.image)

        #rage run ability
        self.velocidade = self.velocidade_base
        self.run_ativo = False
        self.cooldown_run = 6000
        self.tempo_ultima_run = pygame.time.get_ticks()
        self.duracao_run = 2500
        self.tempo_inicio_run = 0

        #cannon beam
        self.cooldown_cannon = 3000
        self.tempo_ultimo_cannon = pygame.time.get_ticks()

        #burst
        self.cooldown_burst = 4000
        self.contagem_burst = 10
        self.burst_restante = 0
        self.tempo_ultimo_burst = pygame.time.get_ticks()
        self.intervalo_burst = 150
        self.cronometro_burst = 0

    @property
    def collision_rect(self):
        "Retorna a hitbox de Hunter."
        return self.mask

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.posicao)
    
    def run(self):
        if not self.run_ativo:
            novo_cooldown = [5000, 5500, 6000, 6500]
            self.cooldown_run = random.choice(novo_cooldown)
            self.run_ativo = True
            self.velocidade_base = self.velocidade * 4
            self.tempo_inicio_run = pygame.time.get_ticks()
    
    def burst(self):
        PlasmaGun(
            posicao_inicial=self.posicao,
            grupos=(self.game.all_sprites, self.game.projeteis_inimigos_grupo),
            jogador=self.jogador,
            game=self.game,
            dano=15,
            velocidade=400,
            tamanho=(32, 32)
        )

    def cannon_beam(self):
        CannonBeam(
            posicao_inicial=self.posicao,
            grupos=(self.game.all_sprites, self.game.projeteis_inimigos_grupo),
            jogador=self.jogador,
            game=self.game,
            dano=250, 
            velocidade=350,
            duracao=3000
        )

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
        agora = pygame.time.get_ticks()
        # Lógica de controle do estado de corrida
        if self.run_ativo:
            if agora - self.tempo_inicio_run >= self.duracao_run:
                self.run_ativo = False
                self.velocidade_base = self.velocidade
        # Lógica para ativar a corrida
        if agora - self.tempo_ultima_run >= self.cooldown_run:
            self.tempo_ultima_run = agora
            self.run()
        #Ativa o burst
        if agora - self.tempo_ultimo_burst >= self.cooldown_burst:
            self.burst_restante = self.contagem_burst  
            novo_cooldown = [7000, 8000, 9000, 10000]
            self.cooldown_burst = random.choice(novo_cooldown)
            self.tempo_ultimo_burst = agora
        #Burst
        if self.burst_restante > 0:
            self.cronometro_burst += delta_time * 1000
            if self.cronometro_burst >= self.intervalo_burst:
                self.cronometro_burst = 0
                self.burst_restante -= 1
                self.burst()
        #Cannon
        if agora - self.tempo_ultimo_cannon >= self.cooldown_cannon:
            self.tempo_ultimo_cannon = agora
            novo_cooldown_cannon = [8000, 8500, 9000, 9500]
            self.cooldown_cannon = random.choice(novo_cooldown_cannon)
            self.cannon_beam()
        
        # O resto da sua lógica de movimento e habilidades
        direcao = (self.jogador.posicao - self.posicao).normalize()
        self.posicao += direcao * self.velocidade_base * delta_time
        self.rect.center = self.posicao

        if direcao.x < 0:
            self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'

        self.animar()

class CannonBeam(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, dano, velocidade, duracao):
        self.posicao = pygame.math.Vector2(posicao_inicial)
        super().__init__(posicao_inicial, grupos, jogador, game, dano=dano, velocidade=velocidade, duracao=duracao)
        #sprite
        self.image = pygame.transform.scale(pygame.image.load(join('assets', 'img', 'hunter', 'cannon.png')).convert_alpha(), (150, 150))
        #hitbox
        # Cria um novo retângulo menor para a colisão
        tamanho_hitbox = (75, 75)  # Ajuste este valor para o tamanho correto do feixe
        self.rect = pygame.Rect(0, 0, tamanho_hitbox[0], tamanho_hitbox[1])
        self.rect.center = self.image.get_rect(center=self.posicao).center
        #direcao
        direcao = self.jogador.posicao - self.posicao
        if direcao.length() > 0:
            self.direcao = direcao.normalize()
        else:
            self.direcao = pygame.math.Vector2(1, 0)
        #self kill
        self.tempo_criacao = pygame.time.get_ticks()

    def update(self, delta_time):
        # Atualiza a posição com base na direção e velocidade
        self.posicao += self.direcao * self.velocidade * delta_time
        self.rect.center = self.posicao
        
        # Verifica se o projétil passou da duração para removê-lo
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_criacao >= self.duracao:
            self.kill()

