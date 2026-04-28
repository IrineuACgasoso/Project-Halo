import pygame
import random
from source.feats.items import *
from source.player.player import *
from source.windows.settings import *
from source.feats.projetil import LaserBeam, PlasmaGun
from source.enemies.enemies import *
from source.systems.entitymanager import entity_manager



class Hunter(InimigoBase):
    def __init__(self, posicao, grupos, game):
        # 1. Base gerencia o Cache Global
        super().__init__(posicao, vida_base=750, dano_base=40, velocidade_base=40, game=game, sprite_key='hunter', flip_sprite=True)
        self.titulo = "HUNTER, O Guerreiro Mgalekgolo"
        
        # 2. Sprites do Cache
        self.sprites = self.get_sprites('default')
        self.frame_atual = 0  
        self.estado_animacao = 'left'
        self.image = self.sprites[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))
        
        self.velocidade_animacao = 900
        self.ultimo_update_animacao = pygame.time.get_ticks()
        
        # Hitbox (Inicia a mask)
        self.mask = pygame.mask.from_surface(self.image)

        # Timers e Habilidades 
        # RUN
        self.run_ativo = False
        self.cooldown_run = 6000
        self.tempo_ultima_run = pygame.time.get_ticks()
        self.duracao_run = 2500
        self.tempo_inicio_run = 0
        self.velocidade_corrida = 350
        # CANNON
        self.cooldown_cannon = 3000
        self.tempo_ultimo_cannon = pygame.time.get_ticks()
        # BURST
        self.cooldown_burst = 4000
        self.contagem_burst = 10
        self.burst_restante = 0
        self.tempo_ultimo_burst = pygame.time.get_ticks()
        self.intervalo_burst = 150
        self.cronometro_burst = 0

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            
            # ATUALIZAÇÃO IMPORTANTE: Mask e Rect
            self.mask = pygame.mask.from_surface(self.image)
            self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))

    def run(self):
        """Ativa o estado de investida do Hunter."""
        self.run_ativo = True
        self.tempo_inicio_run = pygame.time.get_ticks()
        self.velocidade = self.velocidade_corrida
        self.velocidade_animacao = 200 # Animação rápida durante a corrida

    def burst(self):
        """Dispara a metralhadora de plasma."""
        # Calcula a direção para o jogador 
        direcao_com_spread = self.calcular_direcao_tiro(0.15)

        PlasmaGun(
            posicao_inicial=self.posicao,
            grupos          = (entity_manager.all_sprites,),
            jogador         = self.jogador,
            game            = self.game,
            dono            = 'INIMIGO',
            dano            = 15,
            velocidade      = 500,
            tamanho         = (36, 36),
            direcao_spread  = direcao_com_spread,
            vai_rotacionar  = False
        )

    def cannon_beam(self):
        """Dispara o canhão principal."""
        # Calcula a direção do Cannon
        direcao_tiro = self.calcular_direcao_tiro()

        LaserBeam(
            posicao_inicial= self.posicao,
            grupos         = (entity_manager.all_sprites,),
            jogador        = self.jogador,
            game           = self.game,
            dono           = 'INIMIGO',
            tamanho        = (96, 96),
            dano           = 250, 
            velocidade     = 750,
            direcao_spread = direcao_tiro,
            vai_rotacionar = False,
            color          = 'green',
        )

    def morrer(self, grupos = None):
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 2, 100)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 50)
        Items.spawn_drop(self.posicao, grupos, 'cafe', 1, 1)
        self.kill()

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()

        # --- LÓGICA DE HABILIDADES ---
        # Rage Run
        if self.run_ativo:
            if agora - self.tempo_inicio_run >= self.duracao_run:
                self.run_ativo = False
                self.velocidade_animacao = 900
                self.velocidade = self.velocidade_base
        elif agora - self.tempo_ultima_run >= self.cooldown_run:
            self.tempo_ultima_run = agora
            self.run()

        # Burst logic
        if agora - self.tempo_ultimo_burst >= self.cooldown_burst:
            self.burst_restante = self.contagem_burst  
            self.cooldown_burst = random.choice([5000, 5500, 6000, 6500])
            self.tempo_ultimo_burst = agora

        if self.burst_restante > 0:
            self.cronometro_burst += delta_time * 1000
            if self.cronometro_burst >= self.intervalo_burst:
                self.cronometro_burst = 0
                self.burst_restante -= 1
                self.burst()

        # Cannon
        if agora - self.tempo_ultimo_cannon >= self.cooldown_cannon:
            self.tempo_ultimo_cannon = agora
            self.cooldown_cannon = random.choice([7500, 8000, 8500, 9000])
            self.cannon_beam()

        # --- MOVIMENTAÇÃO E ANIMAÇÃO ---
        # Deixa a Base fazer o movimento matemático e colisões
        super().update(delta_time, paredes)

        # Atualiza o lado para onde ele olha baseado no jogador
        if self.jogador.posicao.x < self.posicao.x:
            self.estado_animacao = 'left'
        else:
            self.estado_animacao = 'right'

        self.animar()