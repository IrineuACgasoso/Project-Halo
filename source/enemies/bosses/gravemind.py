import pygame
import random
import math
from source.feats.items import *
from source.enemies.enemies import *
from source.enemies.standard.infection import Infection
from source.feats.projetil import AcidBreath
from source.feats.effects import DustParticle
from source.feats.assets import *
from source.systems.entitymanager import entity_manager

class Gravemind(InimigoBase):
    def __init__(self, posicao, game, jogador=None, is_final_form=False, is_minion=False, grupos=None):
        # 1. Configuração de Atributos Base
        if is_final_form:
            self.tipo = 'final'
            valor_vida = 8000
            self.titulo = "GRAVEMIND, O Monumento de Todos os Pecados"
            self.raio_safezone = 1000
        else:
            self.tipo = 'proto'
            self.titulo = "PROTO GRAVEMIND"
            valor_vida = 500 if is_minion else 2000

        if grupos is None:
            grupos = (entity_manager.all_sprites, entity_manager.inimigos_grupo)

        super().__init__(posicao, vida_base=valor_vida, dano_base=50, velocidade_base=35, game=game, sprite_key=None)
        
        for grupo in grupos:
            grupo.add(self)

        self.game = game
        self.jogador = jogador if jogador else entity_manager.player
        self.is_final_form = is_final_form
        self.is_minion = is_minion
        self.gas_invocado = False
        
        # --- VARIÁVEIS DE ANIMAÇÃO E RESPRAWN ---
        self.setup_assets(is_final_form)
        self.estado_animacao = 'reaparecendo'
        self.frame_atual = 0
        self.velocidade_animacao = 600
        self.ultimo_update_animacao = pygame.time.get_ticks()
        
        self.altura_atual = 0 
        self.estado_respawn = 'reaparecendo' 
        self.is_animating_respawn = True
        self.posicao_chao = pygame.math.Vector2(posicao)
        self.timer_particula = pygame.time.get_ticks()
        self.intensidade_shake = 25 if is_final_form else 10

        # --- LÓGICA DE ESTADO ---
        self.estado_habilidade = 'idle'
        self.vida_limite = self.vida_base / 6 

        # --- VARIÁVEIS DE ATAQUE: ÁCIDO ---
        self.cooldown_acido = 2500 if is_final_form else 4000
        self.ultima_baforada = pygame.time.get_ticks()
        self.tiros_restantes = 0
        self.ultimo_tiro_burst = 0
        self.velocidade_baforada = 400 if self.is_final_form else 525

        # --- VARIÁVEIS DE ATAQUE: INFEÇÃO ---
        self.cooldown_infeccao = 3000 if is_final_form else 5000
        self.ultima_infeccao = pygame.time.get_ticks()
        self.spawns_restantes = 0
        self.ultimo_spawn_tick = 0

        # --- VARIÁVEIS DE ATAQUE: CABEÇAS ---
        self.cooldown_cabecas = 15000
        self.ultima_cabeca = pygame.time.get_ticks()
        self.cabecas_restantes = 0
        self.intervalo_cabeca_tick = 0

        # Surface e Rect inicial
        self.surf_render = pygame.Surface(self.tamanho_sprite, pygame.SRCALPHA).convert_alpha()
        self.image = self.surf_render
        self.rect = self.image.get_rect(centerx=posicao[0], bottom=posicao[1])

    @property
    def invulneravel(self):
        return self.is_animating_respawn

    def setup_assets(self, is_final_form):
        key = 'final' if is_final_form else 'proto'
        self.tamanho_sprite = (900, 600) if is_final_form else (750, 500)
        dict_sprites = ASSETS['enemies']['gravemind'][key]
        img_idle1 = dict_sprites['default'][0].convert_alpha()
        img_idle2 = dict_sprites['default'][1].convert_alpha()
        img_atk = dict_sprites['attack'][0].convert_alpha()
        self.sprites = {
            'left': [img_idle1, img_idle2],
            'right': [pygame.transform.flip(img_idle1, True, False), pygame.transform.flip(img_idle2, True, False)],
            'attack_left': img_atk,
            'attack_right': pygame.transform.flip(img_atk, True, False)
        }

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()

        if self.is_animating_respawn:
            self.atualizar_animacao_respawn(delta_time)
            return

        # Lógica de recuo
        if not self.is_minion and not self.is_final_form and self.vida <= self.vida_limite:
            self.estado_respawn = 'desaparecendo'
            self.is_animating_respawn = True
            return

        # Miasma
        if self.is_final_form and not self.gas_invocado and not self.is_minion:
            MiasmaGas(self.posicao, self.raio_safezone, self.game, (entity_manager.all_sprites,), self)
            self.gas_invocado = True

        # FSM - Seleção de Habilidade
        if self.estado_habilidade == 'idle':
            if self.tipo == 'final' and not self.is_minion and agora - self.ultima_cabeca >= self.cooldown_cabecas:
                self.estado_habilidade = 'heads'
                self.cabecas_restantes = 2
            elif agora - self.ultima_baforada >= self.cooldown_acido:
                self.estado_habilidade = 'acid'
                self.tiros_restantes = 15 if self.is_final_form else 8
                self.estado_animacao = 'atacando'
            elif agora - self.ultima_infeccao >= self.cooldown_infeccao:
                self.estado_habilidade = 'infection'
                self.spawns_restantes = 5

        # Execução dos ataques
        if self.estado_habilidade == 'acid': self.acid_breath_attack()
        elif self.estado_habilidade == 'infection': self.spawn_infection_attack()
        elif self.estado_habilidade == 'heads': self.spawn_heads_attack()

        self.animar()

    def acid_breath_attack(self):
        agora = pygame.time.get_ticks()
        if self.tiros_restantes > 0:
            if agora - self.ultimo_tiro_burst >= 150:
                self.tiros_restantes -= 1
                self.ultimo_tiro_burst = agora
                AcidBreath(posicao_inicial=self.posicao, 
                           grupos=(entity_manager.all_sprites,), 
                           jogador=self.jogador, game=self.game,
                           dono='INIMIGO',
                           velocidade=self.velocidade_baforada)
        else:
            self.ultima_baforada = agora
            self.cooldown_acido = random.randint(2500, 5000)
            self.estado_habilidade = 'idle'
            self.estado_animacao = 'normal'

    def spawn_infection_attack(self):
        agora = pygame.time.get_ticks()
        if self.spawns_restantes > 0:
            if agora - self.ultimo_spawn_tick >= 200:
                self.spawns_restantes -= 1
                self.ultimo_spawn_tick = agora
                pos_spawn = self.posicao + pygame.math.Vector2(random.randint(-300, 300), random.randint(-300, 300))
                Infection(posicao=pos_spawn, game=self.game)
        else:
            self.ultima_infeccao = agora
            self.cooldown_infeccao = random.randint(3500, 6000)
            self.estado_habilidade = 'idle'

    def spawn_heads_attack(self):
        agora = pygame.time.get_ticks()
        if self.cabecas_restantes > 0:
            if agora - self.intervalo_cabeca_tick >= 1500: # Intervalo entre cabeças
                self.cabecas_restantes -= 1
                self.intervalo_cabeca_tick = agora
                
                angulo = random.uniform(0, 2 * math.pi)
                distancia = random.uniform(200, self.raio_safezone - 150)
                pos_spawn = self.posicao + pygame.math.Vector2(math.cos(angulo) * distancia, math.sin(angulo) * distancia)
                FloodWarning(posicao=pos_spawn, game=self.game, spawn_minion=True)
        else:
            self.ultima_cabeca = agora
            self.cooldown_cabecas = random.randint(22000, 30000)
            self.estado_habilidade = 'idle'

    def atualizar_animacao_respawn(self, delta_time):
        agora = pygame.time.get_ticks()
        sprite_base = self.sprites['left'][0]
        
        if self.estado_respawn == 'reaparecendo':
            self.altura_atual += 300 * delta_time
            if agora - self.timer_particula > 50:
                self.timer_particula = agora
                for _ in range(3):
                    off_x = random.randint(-self.tamanho_sprite[0]//4, self.tamanho_sprite[0]//4)
                    DustParticle((self.posicao_chao.x + off_x, self.posicao_chao.y), (entity_manager.all_sprites,))
            
            if self.altura_atual >= self.tamanho_sprite[1]:
                self.altura_atual = self.tamanho_sprite[1]
                self.is_animating_respawn = False
                self.estado_respawn = None    
                self.estado_animacao = 'normal'

        elif self.estado_respawn == 'desaparecendo':
            self.altura_atual -= 300 * delta_time
            if self.altura_atual <= 0: 
                self.respawn_logic()
                return

        self.game.camera.shake(intensidade=self.intensidade_shake)

        # Renderização com recorte para fixar o spawn
        h = int(max(1, self.altura_atual))
        self.image = pygame.Surface((self.tamanho_sprite[0], h), pygame.SRCALPHA).convert_alpha()
        area_recorte = pygame.Rect(0, self.tamanho_sprite[1] - h, self.tamanho_sprite[0], h)
        self.image.blit(sprite_base, (0, 0), area_recorte)
        self.rect = self.image.get_rect(centerx=self.posicao_chao.x, bottom=self.posicao_chao.y)
        self.posicao = pygame.math.Vector2(self.rect.center)

    def animar(self):
        agora = pygame.time.get_ticks()
        direcao = 'left' if self.jogador.posicao.x < self.posicao.x else 'right'
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            if self.estado_animacao == 'atacando':
                self.image = self.sprites[f'attack_{direcao}']
            else:
                self.frame_atual = (self.frame_atual + 1) % 2
                self.image = self.sprites[direcao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.rect.center)

    def respawn_logic(self):
        if self.game.gravemind_reborns > 1 and not self.is_minion:
            self.game.gravemind_reborns -= 1
            FloodWarning(self.jogador.posicao, self.game)
        elif self.game.gravemind_reborns == 1:
            self.game.gravemind_reborns = 0
            ProtoGravePit(self.jogador.posicao, self.game)
        self.kill()


class FloodWarning(pygame.sprite.Sprite):
    def __init__(self, posicao, game, spawn_minion=False, grupos=None):
        if grupos is None: grupos = (entity_manager.all_sprites,)
        super().__init__(grupos)
        self.spawn_minion = spawn_minion
        self.game = game
        self.posicao = pygame.math.Vector2(posicao)
        self.timer_vida = 2.5
        self.raio = 300
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 100, 0, 100), (self.raio, self.raio), self.raio)
        self.rect = self.image.get_rect(center=self.posicao)

    def update(self, delta_time):
        self.timer_vida -= delta_time
        if self.timer_vida <= 0:
            # Garante que minions nasçam como 'proto' e is_minion=True
            Gravemind(posicao=self.posicao, game=self.game, is_minion=self.spawn_minion, is_final_form=False)
            self.kill()

class ProtoGravePit(pygame.sprite.Sprite):
    def __init__(self, posicao, game, grupos=None):
        if grupos is None: grupos = (entity_manager.all_sprites,)
        super().__init__(grupos)
        self.game = game; self.posicao = pygame.math.Vector2(posicao); self.timer_pit = 2.5; self.raio = 400
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 0, 0, 150), (self.raio, self.raio), self.raio)
        self.rect = self.image.get_rect(center=self.posicao)

    def update(self, delta_time):
        self.timer_pit -= delta_time
        if self.timer_pit <= 0:
            novo = Gravemind(posicao=self.posicao, game=self.game, is_final_form=True)
            self.game.boss_atual = novo 
            self.kill()

class MiasmaGas(pygame.sprite.Sprite):
    def __init__(self, posicao_boss, raio_seguro, game, grupos, boss):
        super().__init__(grupos)
        self.game = game; self.boss = boss; self.posicao_boss = pygame.math.Vector2(posicao_boss)
        self.raio_seguro = raio_seguro
        self.dano_por_segundo = 300
        tamanho = 2500
        self.image = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
        self.image.fill((50, 120, 50, 150)) 
        pygame.draw.circle(self.image, (0, 0, 0, 0), (tamanho//2, tamanho//2), self.raio_seguro)
        self.rect = self.image.get_rect(center=self.posicao_boss)
        self.ultimo_dano_tick = pygame.time.get_ticks()

    def update(self, delta_time):
        if not self.boss.alive(): self.kill(); return
        agora = pygame.time.get_ticks()
        if self.game.player.posicao.distance_to(self.posicao_boss) > self.raio_seguro:
            if agora - self.ultimo_dano_tick >= 1000:
                self.game.player.vida_atual -= self.dano_por_segundo; self.ultimo_dano_tick = agora