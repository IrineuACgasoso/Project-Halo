import pygame
import random
import math
from source.enemies.enemies import *
from source.feats.projetil import *
from source.feats.items import *
from source.player.player import *
from source.feats.assets import *
from source.feats.projetil import LaserBeam
from source.enemies.standard.sentinel import Sentinel
from source.systems.entitymanager import entity_manager


class GuiltySpark(InimigoBase):
    def __init__(self, posicao, game, grupos):
        valor_vida = 5000
        super().__init__(posicao, vida_base=valor_vida, dano_base=80, velocidade_base= 100, game=game, sprite_key='guilty', flip_sprite=True)
        self.titulo = "GUILTY SPARK, O Monitor da Instalação 04"
        self.game= game
        self.vida = valor_vida
        self.vida_base = valor_vida

        # Sprites
        self.sprites = self.get_sprites('normal')
        self.estado_animacao = 'left'
        self.frame_atual = 0  
        self.indice_animacao = 0
        self.velocidade_animacao = 300
        self.ultimo_update_animacao = pygame.time.get_ticks()
        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center=self.posicao)

        # Hitbox
        self.mask = pygame.mask.from_surface(self.image)

        self.novo_cooldown = (3000, 4000, 5000, 6000, 8000, 10000)
        # Invocação de Sentinels
        self.wait = 1000
        self.start_sentinel = pygame.time.get_ticks()
        self.cooldown_invocacao = random.choice(self.novo_cooldown)
        self.ultima_invocacao = pygame.time.get_ticks()
        
        # Distância dos eixos onde as sentinelas aparecerão
        self.offset_invocacao = 150

        # Laserbeam
        self.num_laser = 1
        self.laser_restantes = 0
        self.intervalo_burst = 150
        self.cooldown_laser = random.choice(self.novo_cooldown)
        self.ultimo_laser = pygame.time.get_ticks()
        self.estado_habilidade = 'idle'

        self.velocidade_anterior = self.velocidade_base

        # TP
        self.cooldown_tp = 3000
        self.ultimo_tp = pygame.time.get_ticks()

        # Enrage
        self.enrage = False
    
    def invocar_sentinelas(self):
        """Invoca 4 sentinelas nos eixos cardinais usando o efeito de teleporte."""
        agora = pygame.time.get_ticks()

        if agora - self.start_sentinel >= self.wait:
        
            # Definição dos 4 eixos (X, Y)
            eixos = [
                (0, -self.offset_invocacao), # Norte
                (0, self.offset_invocacao),  # Sul
                (-self.offset_invocacao, 0), # Oeste
                (self.offset_invocacao, 0)   # Leste
            ]

            for off_x, off_y in eixos:
                pos_spawn = pygame.math.Vector2(self.posicao.x + off_x, self.posicao.y + off_y)
                
                # SÓ invoca a sentinela e o efeito se o chão for válido!
                if self.game.mapa.posicao_e_valida(pos_spawn):
                    GuiltyTeleport((round(pos_spawn.x), round(pos_spawn.y)))
                    
                    nova_sentinela = Sentinel(pos_spawn, self.game)
                    entity_manager.all_sprites.add(nova_sentinela)
                    entity_manager.inimigos_grupo.add(nova_sentinela)

            # Reinicia os contadores e cooldowns
            self.ultima_invocacao = agora
            self.cooldown_invocacao = random.choice(self.novo_cooldown)

            # Reinicia os estados
            self.image = self.sprites[self.estado_animacao][0]
            self.estado_habilidade = 'idle' # Volta para o estado de movimento

    def laser_attack(self):
        agora = pygame.time.get_ticks()

        if agora - self.start_laser >= self.wait:
            if self.laser_restantes > 0:
                if agora - self.ultimo_laser >= self.intervalo_burst:
                    self.laser_restantes -= 1
                    self.ultimo_laser = agora
                    LaserBeam(
                        posicao_inicial=self.posicao,
                        grupos=(entity_manager.all_sprites, entity_manager.projeteis_inimigos_grupo),
                        jogador=self.jogador,
                        game=self.game,
                        dano=self.dano_base * 2,
                        velocidade= 1500,  # Ajuste o dano do laser
                        duracao=1500,  # Ajusta a duração em milissegundos
                        color='blue'
                    )
            else:
                # Reseta os contadores
                self.ultimo_laser = agora

                # Novo Cooldown
                self.cooldown_laser = random.choice(self.novo_cooldown)

                # Retorna ao estado e sprite normal
                self.image = self.sprites[self.estado_animacao][0]
                self.estado_habilidade = 'idle' # Volta para o estado de movimento
            

    def teleporte(self):
        """
        Teleporta o boss garantindo que o destino seja válido 
        de acordo com o sistema de Navigation do Mapa.
        """
        posicao_valida = False
        tentativas = 0
        max_tentativas = 30
        nova_pos = pygame.math.Vector2(0, 0)

        while not posicao_valida and tentativas < max_tentativas:
            tentativas += 1
            
            # Gera um raio aleatório ao redor do jogador
            angulo = random.uniform(0, 2 * math.pi)
            distancia = random.uniform(200, 450) # Distância do TP
            
            target_x = self.jogador.posicao.x + distancia * math.cos(angulo)
            target_y = self.jogador.posicao.y + distancia * math.sin(angulo)
            nova_pos.update(target_x, target_y)
            
            # USA O SEU MÉTODO DO MAPA:
            if self.game.mapa.posicao_e_valida(nova_pos):
                posicao_valida = True

        if posicao_valida:
            # Efeito de saída na posição antiga
            GuiltyTeleport(self.rect.center)
            
            # Atualiza posição
            self.posicao = pygame.math.Vector2(nova_pos)
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))
            
            # Efeito de entrada na posição nova
            GuiltyTeleport(self.rect.center)
            
            # Feedback sonoro ou buffs se houver
            self.ultimo_tp = pygame.time.get_ticks()
            
        self.estado_habilidade = 'idle'

    def rage(self):
        if not self.enrage:
            self.enrage = True
            # Damaged
            self.sprites = self.get_sprites('damaged')
            self.indice_animacao = 0
            # Cooldowns e melhoria das habilidades
            self.novo_cooldown = (500, 1500, 2500, 4000, 5000)
            self.cooldown_invocacao = random.choice(self.novo_cooldown)
            self.cooldown_laser = random.choice(self.novo_cooldown)
            self.num_laser += 2
            self.velocidade_anterior *= 2.5

    def morrer(self, grupos = None):
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 4, 100)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 50)
        Items.spawn_drop(self.posicao, grupos, 'cafe', 1, 1)
        self.kill()

    def animar(self):
        """Atualiza a sprite do GuiltySpark com base na sua direção."""
        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center=self.posicao)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()
        direcao = (self.jogador.posicao - self.posicao)
        if direcao.length() > 0:
            direcao.normalize_ip()

        self.posicao += direcao * self.velocidade * delta_time
        if paredes:
            self.aplicar_colisao_mapa(paredes, self.raio_colisao_mapa)
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        if self.vida <= self.vida_base / 2 and not self.enrage:
            self.rage()

        # Hability FSM
        if self.estado_habilidade == 'idle':
            self.velocidade = self.velocidade_anterior # Restaura o valor bufado, não o base
            # Ativa Laser
            if agora - self.ultimo_laser >= self.cooldown_laser:
                self.estado_habilidade = 'laser'
                self.laser_restantes = self.num_laser
                self.image = self.sprites[self.estado_animacao][1]
                self.start_laser = pygame.time.get_ticks()
                self.velocidade = 0 # Para o movimento
            #  Invoca Sentinels
            elif agora - self.ultima_invocacao >= self.cooldown_invocacao:
                self.estado_habilidade = 'sentinel'
                self.image = self.sprites[self.estado_animacao][2]
                self.start_sentinel = pygame.time.get_ticks()
                self.velocidade = 0
            # Ativa TP
            elif (self.jogador.posicao - self.posicao).length() > 900\
                and (agora - self.ultimo_tp >= self.cooldown_tp):
                self.estado_habilidade = 'teleporte'
        
        # Execução dos Estados
        if self.estado_habilidade == 'laser':
            self.laser_attack()
        elif self.estado_habilidade == 'sentinel':
            self.invocar_sentinelas()
        elif self.estado_habilidade == 'teleporte':
            self.teleporte()
        
        # Lógica de animação
        else:
            if direcao.x < 0:
                self.estado_animacao = 'left'
            elif direcao.x > 0:
                self.estado_animacao = 'right'
            self.animar()


class GuiltyTeleport(pygame.sprite.Sprite):
    def __init__(self, posicao):
        super().__init__(entity_manager.all_sprites)
        self.posicao = pygame.math.Vector2(posicao) 
        self.sprites = ASSETS['enemies']['guilty']['teleport']

        # Animação
        self.frame_atual = 0
        self.image = self.sprites[self.frame_atual]
        self.rect = self.image.get_rect(center=self.posicao)
        
        self.tempo_criacao = pygame.time.get_ticks()
        self.ultimo_update_animacao = pygame.time.get_ticks()
        self.velocidade_animacao = 30
        self.duracao_aviso = 330
    
    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        if agora - self.tempo_criacao >= self.duracao_aviso:
            self.kill()
        self.animar()

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites)
            self.image = self.sprites[self.frame_atual]
            self.rect = self.image.get_rect(center=self.posicao)  