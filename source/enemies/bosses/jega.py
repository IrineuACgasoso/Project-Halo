import pygame
import random
import math
from enemies.enemies import InimigoBase
from feats.projetil import *
from feats.items import *
from player import *
from entitymanager import entity_manager


class Jega(InimigoBase):
    def __init__(self, posicao, game, grupos):
        valor_vida = 5000
        super().__init__(posicao, vida_base=valor_vida, dano_base=100, velocidade_base=50, game=game, sprite_key='jega', flip_sprite=True)

        self.titulo = "JEGA 'RDOMNAI, O Matador de Spartans"
        self.game = game
        self.vida = valor_vida     
        self.vida_base = valor_vida

        # Sprites e Animação
        self.sprites = self.get_sprites('default')
        self.frame_atual = 0  
        self.estado_animacao = 'left'
        self.indice_animacao = 0
        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center=self.posicao)
        self.velocidade_animacao = 180
        self.ultimo_update_animacao = pygame.time.get_ticks()

        # Hitbox
        nova_largura = self.rect.width / 1.3
        self.hitbox = pygame.Rect(0, 0, nova_largura, self.rect.height)
        self.hitbox.center = self.rect.center

        # Máquina de Estados e Fade
        self.estado = 'perseguindo'
        self.tempo_inicio_estado = pygame.time.get_ticks()
        
        self.alpha_atual = 255.0
        self.alpha_alvo = 255.0
        self.velocidade_fade = 600 # Pixels de alpha por segundo

        # Habilidade: Órbita e Bote
        self.ultima_habilidade = pygame.time.get_ticks()
        self.cooldown_habilidade = 5000   
        self.angulo_orbita = 0
        self.raio_orbita = 600
        self.velocidade_orbita = 1.3  
        self.sentido_orbita = 1     
        self.duracao_orbita = 3000  
        self.velocidade_bote = self.velocidade_base * 10
        self.duracao_bote = 1500 
        self.direcao_bote = pygame.math.Vector2(0, 0)   

        # Habilidade: Burst Carabina
        self.cooldown_carabin = 3000
        self.intervalo_carabina = 75
        self.cronometro_carabina = 0
        self.ultima_carabina = 0
        self.carabina_restante = 0
        self.contagem_carabina = 5

    @property
    def collision_rect(self):
        """Retorna a hitbox de Jega. Fica invulnerável durante a órbita ou se estiver invisível."""
        if self.estado == 'orbitando' or self.alpha_atual <= 0:
            return pygame.Rect(-1000, -1000, 0, 0)
        return self.hitbox

    @property
    def invulneravel(self):
        return self.estado == 'orbitando'
    
    def carabin(self):
        Carabin(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites, entity_manager.projeteis_inimigos_grupo),
            jogador=self.jogador,
            game=self.game,
            dano=40,
            velocidade=500,
            tamanho=(24, 24),
            is_Banished=True
        )
    
    def morrer(self, grupos=None):
        alvo_grupos = (entity_manager.all_sprites, entity_manager.item_group)
        chance = random.randint(1, 1000)

        qtd_shards = 2
        if chance > 800: qtd_shards = 4
        elif chance > 600: qtd_shards = 3

        for _ in range(qtd_shards):
            pos_offset = self.posicao + pygame.math.Vector2(random.randint(-30, 30), random.randint(-30, 30))
            Items(posicao=pos_offset, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=alvo_grupos)
        self.kill()

    # --- FUNÇÕES FATORADAS ---

    def _gerenciar_fade(self, delta_time):
        """Cuida da transição suave de invisibilidade do Jega."""
        if self.alpha_atual != self.alpha_alvo:
            if self.alpha_atual < self.alpha_alvo:
                self.alpha_atual += self.velocidade_fade * delta_time
                if self.alpha_atual > self.alpha_alvo:
                    self.alpha_atual = self.alpha_alvo
            else:
                self.alpha_atual -= self.velocidade_fade * delta_time
                if self.alpha_atual < self.alpha_alvo:
                    self.alpha_atual = self.alpha_alvo

    def _gerenciar_carabina(self, agora, delta_time):
        if agora - self.ultima_carabina >= self.cooldown_carabin and self.estado != 'orbitando':
            self.carabina_restante = self.contagem_carabina
            self.cooldown_carabin = random.choice([6000, 7000, 8000, 9000])
            self.ultima_carabina = agora
        
        if self.carabina_restante > 0:
            self.cronometro_carabina += delta_time * 1000
            if self.cronometro_carabina >= self.intervalo_carabina:
                self.cronometro_carabina = 0
                self.carabina_restante -= 1
                self.carabin()

    def _gerenciar_estados(self, agora, delta_time, direcao_ao_jogador, distancia):
        """Controla a movimentação baseada no estado atual do Jega."""
        if self.estado == 'perseguindo':
            self.alpha_alvo = 255 
            if distancia > 0:
                self.posicao += direcao_ao_jogador.normalize() * self.velocidade * delta_time
            
            # Condição de transição: Perseguindo -> Orbitando
            if agora - self.ultima_habilidade > self.cooldown_habilidade and distancia < 600:
                self.estado = 'orbitando'
                self.tempo_inicio_estado = agora
                self.sentido_orbita = random.choice([1, -1])
                self.angulo_orbita = math.atan2(self.posicao.y - self.jogador.posicao.y, 
                                                self.posicao.x - self.jogador.posicao.x)

        elif self.estado == 'orbitando':
            self.alpha_alvo = 0 # Fica invisível
            
            # Movimento Circular
            self.angulo_orbita += self.sentido_orbita * self.velocidade_orbita * delta_time
            nova_x = self.jogador.posicao.x + math.cos(self.angulo_orbita) * self.raio_orbita
            nova_y = self.jogador.posicao.y + math.sin(self.angulo_orbita) * self.raio_orbita
            self.posicao = pygame.math.Vector2(nova_x, nova_y)

            # Condição de transição: Orbitando -> Bote
            if agora - self.tempo_inicio_estado > self.duracao_orbita:
                self.estado = 'bote'
                self.tempo_inicio_estado = agora
                
                # TRAVANDO A MIRA: Calcula a direção do jogador neste exato milissegundo
                vetor_mira = self.jogador.posicao - self.posicao
                if vetor_mira.length() > 0:
                    self.direcao_bote = vetor_mira.normalize()
                else:
                    self.direcao_bote = pygame.math.Vector2(1, 0) # Fallback de segurança

        elif self.estado == 'bote':
            self.alpha_alvo = 255 # Reaparece rapidamente
            self.velocidade_animacao = 100 # Animação acelerada no bote
            
            # Corrida do bote em LINHA RETA (usando a mira travada, ignora o jogador)
            self.posicao += self.direcao_bote * self.velocidade_bote * delta_time
            
            # Condição de transição: Bote -> Perseguindo
            if agora - self.tempo_inicio_estado > self.duracao_bote:
                self.velocidade_animacao = 180
                self.estado = 'perseguindo'
                self.ultima_habilidade = agora 
                self.cooldown_habilidade = random.choice([8000, 9000, 10000])

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            # O rect precisa ser atualizado na troca de frame
            self.rect = self.image.get_rect(center=self.posicao)
            
        # Aplica transparência atualizada
        self.image.set_alpha(int(self.alpha_atual))

    # ----------------------------------------

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()
        
        # Cálculos de Vetor
        direcao_ao_jogador = (self.jogador.posicao - self.posicao)
        distancia = direcao_ao_jogador.length()

        # 1. Máquina de Estados e Movimentação Principal
        self._gerenciar_estados(agora, delta_time, direcao_ao_jogador, distancia)
        
        # 2. Habilidades Extras e Efeitos
        self._gerenciar_carabina(agora, delta_time)
        self._gerenciar_fade(delta_time)

        # 3. Colisão com o Mapa (Se não estiver orbitando pelas paredes)
        if paredes and self.estado != 'orbitando':
            self.aplicar_colisao_mapa(paredes, self.raio_colisao_mapa)
            
        # Atualiza Retângulos
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        self.hitbox.center = self.rect.center
        
        # 4. Animação
        if direcao_ao_jogador.x < 0:
            self.estado_animacao = 'left'
        elif direcao_ao_jogador.x > 0:
            self.estado_animacao = 'right'
            
        self.animar()