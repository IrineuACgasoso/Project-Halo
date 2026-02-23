import pygame
from game import *
from feats.items import *
from enemies.enemies import *
from enemies.standard.infection import Infection
from feats.projetil import AcidBreath
from feats.effects import DustParticle
from feats.assets import *
import random
import math


class Gravemind(InimigoBase):
    def __init__(self, posicao, game, grupos, jogador, is_final_form = False, is_minion=False):
        if is_final_form:
            self.tipo = 'final'
            valor_vida = 8000
            self.gas_invocado = False
            self.raio_safezone = 1000
            self.titulo = "GRAVEMIND, O Monumento de Todos os Pecados"
            self.numero_particulas = 5
            self.dispersao_particulas = (-300, 300)
            self.tamanho_sprite = (900, 600)
        else:
            self.tipo = 'proto'
            self.titulo = "PROTO GRAVEMIND"
            self.numero_particulas = 2
            self.dispersao_particulas = (-150, 150)
            self.tamanho_sprite = (750, 500)
            if is_minion:
                valor_vida = 500
            else:
                valor_vida = 2000
        super().__init__(posicao, vida_base=valor_vida, dano_base=50, velocidade_base=35, game=game, sprite_key=None)

        self.game = game
        self.vida = valor_vida
        self.vida_base = valor_vida
        self.is_final_form = is_final_form
        self.is_minion = is_minion

        # --- FSM (MÁQUINA DE ESTADOS) ---
        self.estado_atual = 'idle' # idle, acid_breath, spawning_infection, spawning_heads, respawning

        # --- NOVO TRECHO (Lendo 'default' e 'attack') ---
        self.sprites = {}

        # Como mudamos no assets.py, precisamos buscar direto no dicionário raiz do inimigo
        if is_final_form:
            dict_sprites = ASSETS['enemies']['gravemind']['final']
        else:
            dict_sprites = ASSETS['enemies']['gravemind']['proto']

        # Pega os frames normais (idle) e espelha para a direita
        img_idle1 = dict_sprites['default'][0]
        img_idle2 = dict_sprites['default'][1]
        
        self.sprites['left'] = [img_idle1, img_idle2]
        self.sprites['right'] = [
            pygame.transform.flip(img_idle1, True, False),
            pygame.transform.flip(img_idle2, True, False)
        ]

        # Pega a imagem de ataque e espelha para a direita
        img_attack = dict_sprites['attack'][0]
        
        self.sprites['attack_left'] = img_attack
        self.sprites['attack_right'] = pygame.transform.flip(img_attack, True, False)
        # ------------------------------------------------

        # ---- VARIÁVEIS DA ANIMAÇÃO DE RESPAWN ----
        self.altura_atual = 0 
        self.estado_respawn = 'reaparecendo' 
        self.velocidade_animacao_respawn = 300
        self.is_animating_respawn = True

        self.image = self.sprites['left'][0]
        # O ponto de spawn (posicao) deve ser o BOTTOM (chão) do boss
        self.rect = self.image.get_rect(centerx=posicao[0], bottom=posicao[1])
        # Salva a posição do CHÃO como referência constante
        self.posicao_chao = pygame.math.Vector2(posicao[0], posicao[1]) 
        # self.posicao ainda é usada para projéteis, então mantemos o centro lógico
        self.posicao = pygame.math.Vector2(self.rect.center)
        #hitbox
        self.hitbox = pygame.Rect(0, 0, self.rect.width, self.rect.height)
        self.hitbox.center = self.rect.center

        self.frame_atual = 0
        self.velocidade_animacao = 350
        self.ultimo_update_animacao = pygame.time.get_ticks()

        # Prepara a superfície para o efeito de subir do chão
        self.image = pygame.Surface(self.tamanho_sprite, pygame.SRCALPHA)
        self.rect = self.image.get_rect(centerx=posicao[0], bottom=posicao[1])
        
        # Chama uma vez com delta_time 0 apenas para preparar a primeira fatia
        self.atualizar_sprite_respawn(0)

        # Respawns
        self.vida_limite = self.vida_base / 6
        self.timer_particula = 0
        self.intervalo_particula = 0.05  # Spawna uma partícula a cada 0.05 segundos

        # Variável para controlar o estado da animação
        self.estado_animacao = 'normal'

        # --- CONFIGURAÇÃO DOS ATAQUES (COOLDOWNS) ---
        
        # Infection Spawn (Baixa Prioridade)
        self.timer_infeccao = 0
        self.cooldown_infeccao = 4.5
        self.qtd_spawn_infeccao = 5
        self.intervalo_entre_spawns = 0.25
        self.spawns_restantes = 0
        self.timer_entre_spawns = 0
        
        if self.is_final_form:
            self.qtd_spawn_infeccao = 8
            self.intervalo_entre_spawns = 0.15
            self.cooldown_infeccao = 3
            
        # Acid Breath (Média Prioridade)
        self.timer_acido = 0
        self.cooldown_acido = 2.5
        self.qtd_tiros_acido = 8
        self.intervalo_burst = 0.25
        self.tiros_restantes = 0
        self.timer_burst = 0
        
        if self.is_final_form:
            self.qtd_tiros_acido = 20
            self.intervalo_burst = 0.15
            self.cooldown_acido = 1.5

        # Head Spawn (Final Form)
        self.timer_cabecas = 0
        self.cooldown_cabecas = 15.0
        self.qtd_cabecas = 2
        self.cabecas_restantes = 0
        self.timer_entre_cabecas = 0
        self.intervalo_spawn_cabeca = 1.0


    @property
    def collision_rect(self):
        """Retorna a hitbox específica do Gravemind."""
        return self.hitbox
    
    @property
    def invulneravel(self):
        return self.estado_respawn == 'reaparecendo' or self.estado_respawn == 'desaparecendo'
        
    
    def get_direction_key(self):
        """Retorna a string 'left' ou 'right' baseada na posição do player"""
        if self.jogador.posicao.x < self.posicao.x:
            return 'left'
        else:
            return 'right'
    
    def atualizar_sprite_respawn(self, delta_time):
        direcao = self.get_direction_key()
        sprite_base = self.sprites[direcao][0]

        if self.estado_respawn == 'reaparecendo':
            self.altura_atual += self.velocidade_animacao_respawn * delta_time

            # --- EFEITO DE PARTÍCULAS ---
            # Spawna partículas enquanto estiver subindo
            if delta_time > 0 and self.altura_atual < self.tamanho_sprite[1]:

                for _ in range(self.numero_particulas): # Quantidade por frame
                    pos_x = self.posicao_chao.x + random.randint(self.dispersao_particulas[0], self.dispersao_particulas[1])
                    DustParticle(
                        posicao=(pos_x, self.posicao_chao.y),
                        grupos= entity_manager.all_sprites
                    )

            if self.altura_atual >= self.tamanho_sprite[1]:
                self.altura_atual = self.tamanho_sprite[1]
                self.is_animating_respawn = False
                self.estado_respawn = 'idle'
                self.image = sprite_base # Volta para a imagem cheia
                return
                
        elif self.estado_respawn == 'desaparecendo':
            self.altura_atual -= self.velocidade_animacao_respawn * delta_time

            for _ in range(self.numero_particulas): # Quantidade por frame
                    pos_x = self.posicao_chao.x + random.randint(self.dispersao_particulas[0], self.dispersao_particulas[1])
                    DustParticle(
                        posicao=(pos_x, self.posicao_chao.y),
                        grupos= entity_manager.all_sprites
                    )

            if self.altura_atual <= 0:
                self.altura_atual = 0
                self.is_animating_respawn = False
                self.respawn()
                return

        largura_total, altura_total = self.tamanho_sprite
        # Garante que a altura seja pelo menos 1 para o subsurface não crashar
        altura_int = int(max(1, min(self.altura_atual, altura_total)))

        temp_surface = pygame.Surface((largura_total, altura_total), pygame.SRCALPHA)
        
        try:
            fatia_rect = (0, 0, largura_total, altura_int)
            fatia_sprite = sprite_base.subsurface(fatia_rect)
            
            # Blita no fundo para dar o efeito de subir do chão
            temp_surface.blit(fatia_sprite, (0, altura_total - altura_int))
            
            self.image = temp_surface
            self.rect = self.image.get_rect(centerx=self.posicao_chao.x, bottom=self.posicao_chao.y)
            self.posicao.xy = self.rect.center
        except Exception as e:
            # Se a altura for muito pequena (ex: 0.5), o subsurface pode falhar. 
            # Nesse caso, mantemos a imagem transparente.
            pass

    def respawn(self):
        if self.game.gravemind_reborns > 1 and not self.is_minion:
            self.game.gravemind_reborns -= 1
            # Spawna o aviso na posição do jogador e se destrói
            FloodWarning(posicao=self.jogador.posicao, grupos = entity_manager.all_sprites, game=self.game, spawn_minion=False)
        elif self.game.gravemind_reborns == 1:
            self.game.gravemind_reborns = 0
            ProtoGravePit(posicao=self.jogador.posicao, grupos=entity_manager.all_sprites, game=self.game)
        self.kill()

    # --- LÓGICA DE AÇÃO (EXECUÇÃO) ---
    def executar_spawn_infeccao(self, delta_time):
        """Estado: spawning_infection"""
        self.timer_entre_spawns += delta_time 
        if self.timer_entre_spawns >= self.intervalo_entre_spawns:
            self.timer_entre_spawns = 0
            self.spawns_restantes -= 1
            
            # Lógica de Spawn
            deslocamento_x = randint(-300, 300)
            deslocamento_y = randint(-300, 300)
            posicao_spawn = self.posicao + pygame.math.Vector2(deslocamento_x, deslocamento_y)
            Infection(posicao=posicao_spawn, game=self.game)

            if self.spawns_restantes <= 0:
                # Terminou a ação, reseta cooldown e volta pra Idle
                novo_cooldown = [5.0, 5.5, 6.5, 7.5]
                self.cooldown_infeccao = random.choice(novo_cooldown)
                self.timer_infeccao = 0
                self.estado_atual = 'idle'

    def executar_acid_breath(self, delta_time):
        """Estado: acid_breath"""
        if self.is_final_form:
            velocidade_breath = 375
        else:
            velocidade_breath = 200

        self.timer_burst += delta_time
        if self.timer_burst >= self.intervalo_burst:
            self.timer_burst = 0
            self.tiros_restantes -= 1
            
            # Lógica do tiro
            AcidBreath(
                posicao_inicial=self.posicao,
                grupos=(entity_manager.all_sprites, entity_manager.projeteis_inimigos_grupo), 
                jogador=self.jogador,
                game=self.game,
                velocidade=velocidade_breath
            )
            
            if self.tiros_restantes <= 0:
                # Terminou o burst, volta pra Idle
                novo_cooldown = [4.5, 5.5, 6.0, 6.5]
                self.cooldown_acido = random.choice(novo_cooldown)
                self.timer_acido = 0
                self.estado_atual = 'idle'

    def executar_spawn_cabecas(self, delta_time):
        """Estado: spawning_heads"""
        self.timer_entre_cabecas += delta_time
        if self.timer_entre_cabecas >= self.intervalo_spawn_cabeca:
            self.timer_entre_cabecas = 0
            self.cabecas_restantes -= 1

            # Lógica de spawn Ultimate
            angulo = random.uniform(0, 2 * math.pi)
            margem_seguranca = 150 
            raio_maximo = self.raio_safezone - margem_seguranca
            distancia = random.uniform(0, raio_maximo)
            offset_x = math.cos(angulo) * distancia
            offset_y = math.sin(angulo) * distancia
            posicao_spawn = self.posicao + pygame.math.Vector2(offset_x, offset_y)
            
            FloodWarning(posicao=posicao_spawn, grupos=entity_manager.all_sprites, game=self.game, spawn_minion=True)

            if self.cabecas_restantes <= 0:
                novo_cooldown_ultimate = [20.0, 25.0, 30.0]
                self.cooldown_cabecas = random.choice(novo_cooldown_ultimate)
                self.timer_cabecas = 0
                self.timer_acido = -5.0
                self.timer_infeccao = -5.0
                self.estado_atual = 'idle'

    def morrer(self, grupos):
            
        alvo_grupos = (entity_manager.all_sprites, entity_manager.item_group)
        chance= randint(1,1000)

        # Drop garantido de Shards grandes por ser Boss
        if self.is_minion and not self.is_final_form:
            qtd_shards = 1
        elif self.is_final_form:
            qtd_shards = 6
            if chance > 800: qtd_shards += 4
            elif chance > 600: qtd_shards += 2
        
        else:
            qtd_shards = 1

        for _ in range(qtd_shards):
            pos_offset = self.posicao + pygame.math.Vector2(random.randint(-30, 30), random.randint(-30, 30))
            Items(posicao=pos_offset, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=alvo_grupos)
        self.kill()

    def animar(self):
        agora = pygame.time.get_ticks()
        # Pega a direção atual ('left' ou 'right')
        direcao = self.get_direction_key()
        # Verifica se já passou tempo suficiente para mudar de frame
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            # Lógica usando o dicionário self.sprites
            if self.estado_animacao == 'atacando':
                # Usa a chave attack_left ou attack_right
                self.image = self.sprites[f'attack_{direcao}']
            else:
                # Usa a lista da chave left ou right
                lista_sprites = self.sprites[direcao]
                self.frame_atual = (self.frame_atual + 1) % len(lista_sprites)
                self.image = lista_sprites[self.frame_atual]
            
            # Atualiza o rect para garantir centralização
            self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, delta_time, paredes = None):
        if self.is_final_form and not self.is_animating_respawn and not self.gas_invocado:
            MiasmaGas(
                posicao_boss=self.posicao,
                raio_seguro=self.raio_safezone,
                game=self.game,
                grupos=(entity_manager.all_sprites),
                boss=self
            )
            self.gas_invocado = True

        if self.is_animating_respawn:
            self.atualizar_sprite_respawn(delta_time)
            # Retorna para não executar o resto do código enquanto anima
            return
        #Lógica de morte para iniciar a animação de desaparecimento
        if not self.is_minion:
            if not self.is_final_form and self.vida <= self.vida_limite: 
                self.estado_respawn = 'desaparecendo'
                self.is_animating_respawn = True
        
        # Atualiza Cooldowns
        self.timer_infeccao += delta_time 
        self.timer_acido += delta_time
        if self.is_final_form:
            self.timer_cabecas += delta_time 

        # Attack FSM
        if self.estado_atual == 'idle':
            # Prioridade 1: Ultimate (Cabeças)
            if (self.is_final_form and not self.is_minion) and (self.timer_cabecas >= self.cooldown_cabecas):
                    self.estado_atual = 'spawning_heads'
                    self.cabecas_restantes = self.qtd_cabecas
                    self.timer_entre_cabecas = 0 # Pronto para spawnar a primeira
            
            # Prioridade 2: Ataque Principal (Ácido)
            elif self.timer_acido >= self.cooldown_acido:
                self.estado_atual = 'acid_breath'
                self.tiros_restantes = self.qtd_tiros_acido
                self.timer_burst = 0 # Pronto para o primeiro tiro

            # Prioridade 3: Spawn de Minions (Infecção)
            elif self.timer_infeccao >= self.cooldown_infeccao:
                self.estado_atual = 'spawning_infection'
                self.spawns_restantes = self.qtd_spawn_infeccao
                self.timer_entre_spawns = 0

        # Execução do Estado Atual
        if self.estado_atual == 'acid_breath':
            self.executar_acid_breath(delta_time)
        elif self.estado_atual == 'spawning_infection':
            self.executar_spawn_infeccao(delta_time)
        elif self.estado_atual == 'spawning_heads':
            self.executar_spawn_cabecas(delta_time)
        
        if not self.is_animating_respawn:
            self.animar()

class FloodWarning(pygame.sprite.Sprite):
    def __init__(self, posicao, game, grupos, spawn_minion=False):
        super().__init__(grupos)
        self.spawn_minion = spawn_minion
        self.game = game
        self.posicao = pygame.math.Vector2(posicao)
        self.timer_vida = 2.5  # Duração do aviso em milissegundos (3 segundos)
        self.raio = 300     # Raio do círculo de aviso
        self.dano = 300      # Dano que o jogador receberá se estiver dentro do círculo
        # Cria a sprite visual do círculo
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        self.image.set_colorkey((0,0,0)) # Torna a superfície preta transparente
        pygame.draw.circle(self.image, (255, 100, 0, 100), (self.raio, self.raio), self.raio)
        
        self.rect = self.image.get_rect(center=self.posicao)
        self.tempo_criacao = pygame.time.get_ticks()

    def update(self, delta_time):
        self.timer_vida -= delta_time
        # Verifica se o tempo do aviso acabou
        if self.timer_vida <= 0:
            # Verifica a colisão com o jogador
            distancia_do_player = self.game.player.posicao.distance_to(self.posicao)
            if distancia_do_player <= self.raio:
                self.game.player.vida_atual -= self.dano
            novo_boss = Gravemind(
                posicao=self.posicao, 
                grupos=(entity_manager.all_sprites, entity_manager.inimigos_grupo),
                jogador=self.game.player,
                game=self.game,
                is_minion=self.spawn_minion
            )     
            self.game.boss_atual = novo_boss   
            # Remove o círculo de aviso
            self.kill()

class ProtoGravePit(pygame.sprite.Sprite):
    def __init__(self, posicao, game, grupos):
        super().__init__(grupos)
        
        self.game = game 
        self.posicao = pygame.math.Vector2(posicao)
        self.timer_pit = 2.5   
        self.raio = 400      
        self.dano = 10000 

        # Cria a sprite visual do círculo
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        self.image.set_colorkey((0, 0, 0))
        pygame.draw.circle(self.image, (255, 0, 0, 150), (self.raio, self.raio), self.raio)
        
        self.rect = self.image.get_rect(center=self.posicao)
        self.tempo_criacao = pygame.time.get_ticks()

    def update(self, delta_time):
        self.timer_pit -= delta_time
        if self.timer_pit <= 0:
            # Verifica a colisão com o jogador e causa dano
            distancia_do_player = self.game.player.posicao.distance_to(self.posicao)
            if distancia_do_player <= self.raio:
                self.game.player.vida_atual -= self.dano
            #Proto Gravemind
            novo_boss = Gravemind(
                posicao=self.posicao,
                grupos=(entity_manager.all_sprites, entity_manager.inimigos_grupo),
                jogador=self.game.player,
                game=self.game,
                is_final_form=True  
            )
            self.game.boss_atual = novo_boss 
            self.kill()


class MiasmaGas(pygame.sprite.Sprite):
    def __init__(self, posicao_boss, raio_seguro, game, grupos, boss):
        super().__init__(grupos)
        self.game = game
        self.boss = boss # Referência ao boss para saber quando ele morre
        self.posicao_boss = pygame.math.Vector2(posicao_boss)
        self.raio_seguro = raio_seguro
        self.dano_por_segundo = 150 
        
        # OTIMIZAÇÃO: Desenha apenas UMA VEZ no início
        tamanho = 6000
        self.image = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
        self.image.fill((50, 120, 50, 200)) 
        pygame.draw.circle(self.image, (0, 0, 0, 0), (tamanho//2, tamanho//2), self.raio_seguro)
        
        self.rect = self.image.get_rect(center=self.posicao_boss)
        self.tempo_ultimo_dano = 0

    def update(self, delta_time):
        if not self.boss.alive():
            self.kill()
            return

        distancia = self.game.player.posicao.distance_to(self.posicao_boss)
        if distancia > self.raio_seguro:
            self.tempo_ultimo_dano += delta_time # Acumula o tempo real
            if self.tempo_ultimo_dano >= 1.0: # Se passou 1 segundo
                self.game.player.vida_atual -= self.dano_por_segundo
                self.tempo_ultimo_dano = 0

