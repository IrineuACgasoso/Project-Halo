import pygame
import random
import math
from feats.items import *
from player import *
from settings import *
from feats.projetil import LaserBeam
from enemies.enemies import *
from feats.effects import PrometheanTeleport
from entitymanager import entity_manager



class Knight(InimigoBase):
    def __init__(self, posicao, grupos, game):
        super().__init__(posicao, vida_base=500, dano_base=60, velocidade_base=50, game=game)
        self.game = game
        self.titulo = 'PROMETHEAN KNIGHT'

        #sprites
        self.sprites = {}
        #right
        self.sprites['right'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'prometheans', 'knight', 'command1.png')).convert_alpha(), (250, 250)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'prometheans', 'knight', 'command2.png')).convert_alpha(), (250, 250)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'prometheans', 'knight', 'command3.png')).convert_alpha(), (250, 250)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'prometheans', 'knight', 'command4.png')).convert_alpha(), (250, 250)),
        ]
        #left
        self.sprites['left'] = [pygame.transform.flip(sprite, True, False) for sprite in self.sprites['right']]
        # Inicia a animação
        self.frame_atual = 0
        self.estado_animacao = 'right' 
        self.velocidade_animacao = 300 # Milissegundos por frame
        self.ultimo_update_animacao = pygame.time.get_ticks()
        #rect
        self.image = self.sprites[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center=self.posicao)
        # Cria a hitbox do knight
        self.hitbox = pygame.Rect(0, 0, self.rect.width * 0.6, self.rect.height * 0.9)
        self.hitbox.center = self.rect.center

        # FSM
        self.estado_habilidade = 'idle' # Laser, Run, TP, Stun

        # TP
        self.cooldown_tp = 5000
        self.ultimo_tp = 0
        self.tp_orb = None # Variável para segurar a partícula de teleporte
        self.tp_destino = pygame.math.Vector2(0,0)

        # Stun
        self.cooldown_stun = 13000
        self.ultima_stun = 0
        
        # Laser
        self.start_laser = pygame.time.get_ticks()
        self.wait_laser = 750
        self.cooldown_laser = 7000
        self.ultimo_laser = pygame.time.get_ticks()

        # Run
        self.running = False
        self.cooldown_run = 10000
        self.duracao_run = 2500
        self.ultima_run = pygame.time.get_ticks()
        self.inicio_run = 0
        self.velocidade = self.velocidade_base

    @property
    def collision_rect(self):
        return self.hitbox
    
    @property
    def invulneravel(self):
        return self.estado_habilidade == 'tp_traveling'
    
    # ===========
    # HABILIDADES
    # ===========
    
    def executar_laser(self):
        agora = pygame.time.get_ticks()

        self.velocidade = 0

        if agora - self.start_laser >= self.wait_laser:

            LaserBeam(
                posicao_inimigo=self.posicao,
                grupos=(entity_manager.all_sprites, entity_manager.projeteis_inimigos_grupo),
                jogador=self.jogador,
                game=self.game,
                dano=self.dano_base * 2.5,
                velocidade= 1500,  # Ajuste o dano do laser
                duracao=2000,  # Ajusta a duração em milissegundos
                color='red'
            )

            novo_cooldown = [5000, 7000, 8000, 10000]
            self.cooldown_laser = random.choice(novo_cooldown)
            self.ultimo_laser = pygame.time.get_ticks()
        
            self.estado_habilidade = 'idle'

    def executar_run(self):
        agora = pygame.time.get_ticks()
                
        if not self.running:
            self.velocidade_animacao = 120
            self.running = True
            self.velocidade = self.velocidade_base * 6.0
            self.inicio_run = pygame.time.get_ticks()
        
        # Desativa Run
        else:
            if agora - self.inicio_run >= self.duracao_run:
                # Novo Cooldown
                novo_cooldown = [10000, 12000, 15000, 18000]
                self.cooldown_run = random.choice(novo_cooldown)

                # Reseta stats
                self.velocidade = self.velocidade_base
                self.velocidade_animacao = 300
                self.running = False

                self.ultima_run = pygame.time.get_ticks()
                self.estado_habilidade = 'idle'
    
    # --
    # TP
    # --

    def executar_tp(self):
        # Calcula Destino
        angulo = random.uniform(0, 2 * math.pi)
        distancia = random.uniform(250, 300)
        dest_x = self.jogador.posicao.x + distancia * math.cos(angulo)
        dest_y = self.jogador.posicao.y + distancia * math.sin(angulo)
        self.tp_destino = pygame.math.Vector2(dest_x, dest_y)

        # Cria a partícula visual (Orb) que viaja até lá
        self.tp_orb = PrometheanTeleport(
                                    self.posicao, 
                                    self.tp_destino, 
                                    (4, 12),
                                    120,
                                    (20, 30),
                                    [entity_manager.all_sprites], 
                                    self.game
                                )

        # "Some" com o Knight
        self.image.set_alpha(0)
        
        # Muda estado para esperar a partícula
        self.estado_habilidade = 'tp_traveling'

    def finalizar_tp(self):
        # A partícula chegou
        
        # Move o Knight
        self.posicao = pygame.math.Vector2(self.tp_orb.posicao) # Garante que pega a pos exata
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        
        # Reaparece
        self.image.set_alpha(255)
        
        # Reseta cooldowns e estado
        novo_cooldown = [4000, 5000, 6000, 7000]
        self.cooldown_tp = random.choice(novo_cooldown)
        self.ultimo_tp = pygame.time.get_ticks()
        
        self.tp_orb = None
        self.estado_habilidade = 'idle'
    
    def update_tp(self):
        # Verifica se o Orb ainda existe
        if self.tp_orb and not self.tp_orb.alive():
            # Se o orb morreu (alive() é False), significa que chegou no destino
            self.finalizar_tp()


    def morrer(self, grupos):
        qtd_shards = 2

        chance= randint(1,1000)
        if chance >= 900: qtd_shards += 1

        alvo_grupos = (entity_manager.all_sprites, entity_manager.item_group)

        for _ in range(qtd_shards):
            pos_offset = self.posicao + pygame.math.Vector2(random.randint(-30, 30), random.randint(-30, 30))
            Items(posicao=pos_offset, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=alvo_grupos)
        self.kill()
    
    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            # Só atualiza a imagem se não estiver invisível, senão reseta o alpha
            if self.estado_habilidade != 'tp_traveling':
                if self.estado_habilidade != 'laser':
                    self.image = self.sprites[self.estado_animacao][self.frame_atual]
                    self.image.set_alpha(255)
            else:
                # Mantém atualizado o rect sprite mas invisivel
                temp_img = self.sprites[self.estado_animacao][self.frame_atual]
                temp_img.set_alpha(0)
                self.image = temp_img

        self.rect = self.image.get_rect(center=self.posicao)
        self.hitbox.center = self.rect.center

    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        if (self.estado_habilidade != 'tp_traveling') and (self.estado_habilidade != 'laser'):
            direcao = (self.jogador.posicao - self.posicao)
            if direcao.length() > 0:
                direcao.normalize_ip()
                self.posicao += direcao * self.velocidade * delta_time
                self.rect.center = (round(self.posicao.x), round(self.posicao.y))
            self.hitbox.center = self.rect.center

            if direcao.x < 0:
                self.estado_animacao = 'left'
            elif direcao.x > 0:
                self.estado_animacao = 'right'

        # Hability FSM
        if self.estado_habilidade == 'idle':
            self.velocidade = self.velocidade_base
            # Ativa Laser
            if agora - self.ultimo_laser >= self.cooldown_laser:
                self.estado_habilidade = 'laser'
                self.start_laser = pygame.time.get_ticks()
            # Ativa Run
            elif agora - self.ultima_run >= self.cooldown_run:
                self.estado_habilidade = 'run'
            # Ativa TP
            elif agora - self.ultimo_tp >= self.cooldown_tp:
                self.executar_tp()
        
        # Execução dos Estados
        if self.estado_habilidade == 'run':
            self.executar_run()
        elif self.estado_habilidade == 'laser':
            self.executar_laser()
        elif self.estado_habilidade == 'tp_traveling':
            self.update_tp() # Monitora a partícula
        
        self.animar()