import pygame
import random
from os.path import join
from source.enemies.enemies import InimigoBase
from source.player.player import *
from source.windows.settings import *
from source.feats.items import *
from source.feats.projetil import BurstRifle
from source.feats.effects import DustParticle
from source.systems.entitymanager import entity_manager



class Infection(InimigoBase):
    def __init__(self, posicao, game):
        # 1. A Base gerencia o cache e define self.posicao inicial
        super().__init__(posicao, vida_base=1, dano_base=5, velocidade_base=120, game=game, sprite_key='infection')
        
        # 2. Busca os sprites já processados (Cache Global)
        self.sprites = self.get_sprites('default')

        # 3. Configuração de animação
        self.frame_atual = 0  
        self.estado_animacao = 'left'
        self.image = self.sprites[self.estado_animacao][self.frame_atual]
        
        # Sincroniza o rect inicial com a posição arredondada
        self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))
        
        self.velocidade_animacao = 150
        self.ultimo_update_animacao = pygame.time.get_ticks()

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))

    def update(self, delta_time, paredes=None):
        super().update(delta_time, paredes)

        direcao_x = self.jogador.posicao.x - self.posicao.x
        
        if direcao_x < 0:
            self.estado_animacao = 'left'
        elif direcao_x > 0:
            self.estado_animacao = 'right'

        self.animar()


class FloodForms(InimigoBase):
    def __init__(self, posicao, game):
        escolhido = random.randint(1, 20)
        if escolhido > 5:
            self.forma = random.choice(['marine', 'carry'])
        else:
            self.forma = 'elite'

        # Mantive a sprite_key='infection' assumindo que você usa o Cenário 1 (Tudo no mesmo dicionário)
        super().__init__(posicao, vida_base=20, dano_base=10, velocidade_base=100, game=game, sprite_key='infection')

        # Sprites e animação            
        self.sprites = self.get_sprites(self.forma)
        self.estado_animacao = 'right'
        self.frame_atual = 0
        self.velocidade_animacao = 200
        self.ultimo_update_animacao = pygame.time.get_ticks()

        self.image = self.sprites[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center=posicao)

        # Atributos de cada Forma
        self.is_Carry = False
        self.is_Marine = False

        if self.forma == 'elite':
            self.dano = 2 * self.dano_base
            self.velocidade = 2 * self.velocidade_base
            self.velocidade_animacao = 120
            
        elif self.forma == 'carry':
            self.vida = 5 * self.vida_base
            if hasattr(self, 'vida_maxima'):
                self.vida_maxima = self.vida # Previne bugs visuais na barra de vida
            self.dano = self.dano_base / 2
            self.velocidade = self.velocidade_base / 2
            self.is_Carry = True
            
        elif self.forma == 'marine':
            self.is_Marine = True
            # --- Variáveis da Habilidade de Tiro (Rajada) ---
            self.cooldown_ataque = 2500       # 2.5s entre as rajadas
            self.ultimo_ataque = pygame.time.get_ticks()
            self.tiros_por_rajada = 3         # Dá 3 tiros seguidos
            self.tiros_dados = 0              
            self.delay_entre_tiros = 150      # Tempo super rápido entre cada tiro da rajada
            self.ultimo_tiro_rajada = 0
            self.em_rajada = False
            self.distancia_tiro = 400         # Alcance da visão/tiro

    def marine_burst(self):
        agora = pygame.time.get_ticks()
        distancia = (self.jogador.posicao - self.posicao).length()

        # Inicia a rajada se o jogador estiver no alcance e o cooldown permitiu
        if not self.em_rajada and distancia < self.distancia_tiro and agora - self.ultimo_ataque > self.cooldown_ataque:
            self.em_rajada = True
            self.tiros_dados = 0
            self.ultimo_tiro_rajada = agora

        # Continua atirando até bater o limite de 3 tiros
        if self.em_rajada:
            if agora - self.ultimo_tiro_rajada > self.delay_entre_tiros:
                self.disparar()
                self.tiros_dados += 1
                self.ultimo_tiro_rajada = agora
                
                # Encerra a rajada
                if self.tiros_dados >= self.tiros_por_rajada:
                    self.em_rajada = False
                    self.ultimo_ataque = agora
                    novo_cooldown = [4000, 4500, 5000, 6000]
                    self.cooldown_ataque = random.choice(novo_cooldown)

    def disparar(self):
        # Calcula a direção para o jogador
        direcao_com_spread = self.calcular_direcao_tiro(0.2)

        BurstRifle(
            posicao_inicial = self.posicao.copy(),
            grupos          = (entity_manager.all_sprites,),
            jogador         = self.jogador,
            game            = self.game,
            dono            = 'INIMIGO',
            tamanho         = (32, 32), # Ajuste o tamanho da bala (Largura x Altura) aqui
            dano            = 8,
            velocidade      = 700,
            direcao_spread  = direcao_com_spread, # Passa a direção bagunçada para a bala
        )

    def morrer(self, grupos=None):
        alvo_grupos = (entity_manager.all_sprites, entity_manager.items_grupo)
        chance = random.randint(1, 1000)

        if self.is_Carry: 
            qtd_shards = 2
        else:
            qtd_shards = 1

        Items.spawn_drop(self.posicao, grupos, 'exp_shard', qtd_shards, 100)
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 1, 2)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 1)
        
        if self.is_Carry:
            for _ in range(2 * qtd_shards):
                pos_offset = self.posicao + pygame.math.Vector2(random.randint(-50, 50), random.randint(-50, 50))
                DustParticle(posicao=pos_offset, grupos=entity_manager.all_sprites)
                Infection(posicao=pos_offset, game=self.game)

        self.kill()

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, delta_time, paredes=None):
        super().update(delta_time, paredes)

        # Executa a lógica de tiro apenas se for Marine
        if self.is_Marine:
            self.marine_burst()

        direcao_x = self.jogador.posicao.x - self.posicao.x
        
        if direcao_x < 0:
            self.estado_animacao = 'left'
        elif direcao_x > 0:
            self.estado_animacao = 'right'

        self.animar()