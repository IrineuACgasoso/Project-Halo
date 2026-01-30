import pygame
import random
import math
from enemies.enemies import *
from feats.projetil import *
from feats.items import *
from player import *
from feats.projetil import LaserBeam
from enemies.standard.sentinel import Sentinel
from entitymanager import entity_manager


class GuiltySpark(InimigoBase):
    def __init__(self, posicao, game, grupos):
        valor_vida = 5000
        super().__init__(posicao, vida_base=valor_vida, dano_base=80, velocidade_base= 100, game=game)
        self.titulo = "GUILTY SPARK, O Monitor da Instalação 04"
        self.game= game
        self.vida = valor_vida
        self.vida_base = valor_vida
        # Sprites
        self.sprites = {}
        # Left
        self.sprites['left'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'guilty.png')).convert_alpha(), (100, 100)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'guilty2.png')).convert_alpha(), (100, 100)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'guilty3.png')).convert_alpha(), (100, 100))
        ]

        # Right
        self.sprites['right'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites['left']
        ]

        # Damaged
        self.sprites['dleft'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'guilty4.png')).convert_alpha(), (100, 100)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'guilty5.png')).convert_alpha(), (100, 100)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'guilty6.png')).convert_alpha(), (100, 100)),

        ]

        # Right
        self.sprites['dright'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites['dleft']
        ]
        # Image
        self.estado_animacao = 'left'
        self.frame_atual = 0  
        self.indice_animacao = 0
        self.velocidade_animacao = 300
        self.ultimo_update_animacao = pygame.time.get_ticks()
        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center=self.posicao)

        # Hitbox
        self.mask = pygame.mask.from_surface(self.image)

        # Invocação de Sentinels
        self.wait = 1000
        self.start_sentinel = pygame.time.get_ticks()
        self.cooldown_invocacao = 10000 # 10 segundos entre invocações
        self.ultima_invocacao = pygame.time.get_ticks()
        
        # Distância dos eixos onde as sentinelas aparecerão
        self.offset_invocacao = 150

        # Laserbeam
        self.num_laser = 1
        self.laser_restantes = 0
        self.intervalo_burst = 150
        self.cooldown_laser = 3000
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
                
                # Cria o efeito visual de teleporte na posição
                Teleport((round(pos_spawn.x), round(pos_spawn.y)))
                
                # Note: Passamos a posição e a referência do game
                nova_sentinela = Sentinel(pos_spawn, self.game)
                
                # Adiciona aos grupos necessários através do entity_manager
                entity_manager.all_sprites.add(nova_sentinela)
                entity_manager.inimigos_grupo.add(nova_sentinela)

            # Reinicia os contadores e cooldowns
            self.ultima_invocacao = agora
            if self.enrage:
                novo_cooldown = [6000, 7000, 8000, 9000]
            else:
                novo_cooldown = [8000, 10000, 11000, 12000]
            self.cooldown_laser = random.choice(novo_cooldown)

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
                        posicao_inimigo=self.posicao,
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
                if self.enrage:
                    novo_cooldown = [1500, 2000, 2500, 3000]
                else:
                    novo_cooldown = [4000, 6000, 7000, 8000]
                self.cooldown_laser = random.choice(novo_cooldown)

                # Retorna ao estado e sprite normal
                self.image = self.sprites[self.estado_animacao][0]
                self.estado_habilidade = 'idle' # Volta para o estado de movimento
            

    def teleporte(self):
        # Gera um ângulo aleatório (em radianos)
        angulo = random.uniform(0, 2 * math.pi)
        # Define a distância de teleporte entre 150 e 250 pixels do jogador
        distancia_teleporte = random.uniform(150, 250)
        # Calcula a nova posição
        nova_posicao_x = self.jogador.posicao.x + distancia_teleporte * math.cos(angulo)
        nova_posicao_y = self.jogador.posicao.y + distancia_teleporte * math.sin(angulo)
        Teleport((round(nova_posicao_x), round(nova_posicao_y)))
        self.posicao.x = nova_posicao_x
        self.posicao.y = nova_posicao_y
        # Atualiza a posição do retângulo
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        # Recebe um buff de velocidade a cada teleporte
        self.velocidade *= 1.1
        self.velocidade_anterior = self.velocidade
        # Salva o ultimo tp
        self.ultimo_tp = pygame.time.get_ticks()
        # Volta pro estado padrão
        self.estado_habilidade = 'idle'

    def rage(self):
        if not self.enrage:
            self.enrage = True
            self.num_laser += 2
            self.velocidade_anterior *= 2.5
            self.cooldown_laser = 1000
            self.cooldown_invocacao = 2000

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
        """Atualiza a sprite do GuiltySpark com base na sua direção."""
        if self.enrage:
                # Cria uma temp para criar a string do estado damaged
                temp = f'd{self.estado_animacao}'
                self.estado_animacao = temp

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


class Teleport(pygame.sprite.Sprite):
    def __init__(self, posicao):
        super().__init__(entity_manager.all_sprites)
        self.posicao = pygame.math.Vector2(posicao) 
        self.sprites = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp1.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp2.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp3.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp4.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp5.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp6.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp7.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp8.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp9.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp10.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp11.png')).convert_alpha(), (128, 160)),
        ]

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