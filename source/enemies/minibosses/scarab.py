import pygame
import random
from feats.items import *
from player import *
from settings import *
from feats.projetil import PlasmaGun
from feats.effects import ContinuousBeam
from enemies.enemies import *
from entitymanager import entity_manager

class Scarab(InimigoBase):
    def __init__(self, posicao, grupos, game):
        # 1. Atributos Colossais
        super().__init__(posicao, vida_base=15000, dano_base=80, velocidade_base=35, 
                         game=game, sprite_key='scarab', flip_sprite=True)
        self.titulo = "SCARAB"
        
        # 2. Configuração de Animação e Imagem
        self.sprites = self.get_sprites('default')
        self.frame_atual = 0  
        self.estado_animacao = 'left'
        self.image = self.sprites[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))        
        self.velocidade_animacao = 700
        self.ultimo_update_animacao = pygame.time.get_ticks()
        
        # ATRIBUTOS PARA O COLLISION MANAGER/ Hitbox
        self.usar_circulo = True 
        self.radius = 250  # Define o tamanho da hitbox circular (ajuste como preferir)

        # 4. Sistema de Estados de Combate
        self.estado_combate = 'MOVENDO'
        self.tempo_inicio_carga = 0
        self.duracao_carga = 3000    # Tempo carregando o laser
        self.duracao_laser = 5000    # Tempo disparando o laser
        self.cooldown_laser = 12000  # Intervalo entre lasers
        self.ultimo_laser = pygame.time.get_ticks()
        
        self.fase_critica = False 

        # 5. Armamento de Plasma (Torretas Laterais)
        self.opcoes_cooldown = (4000, 6000, 8000, 10000)
        self.cooldown_plasma = random.choice(self.opcoes_cooldown)
        self.ultimo_tiro_plasma = pygame.time.get_ticks()
        
        self.tiros_restantes_rajada = 0
        self.pente_rajada = 6
        self.delay_entre_tiros = 250 
        self.ultimo_tiro_rajada = 0

        # 6. Canhão principal (Beam)
        self.beam_principal = ContinuousBeam(self, color=(100, 255, 100), largura_base=40, dano_por_segundo=200, suavizacao=0.08)

        self.intensidade_shake = 1

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()

        # --- LÓGICA DE FASES ---
        if not self.fase_critica and self.vida < self.vida_base * 0.5:
            self.fase_critica = True
            self.opcoes_cooldown = (2000, 3000, 4000, 5000)
            self.cooldown_plasma = random.choice(self.opcoes_cooldown)
            self.cooldown_laser = 8000
            self.velocidade *= 2
            self.velocidade_animacao /= 1.5
            self.delay_entre_tiros /= 1.5
            self.intensidade_shake *= 3
            # Dica: adicione som de alarme aqui!

        # --- IA DE ATAQUE ---
        self.logica_laser(agora, delta_time)
        self.gerenciar_rajada(agora)

        # --- MOVIMENTAÇÃO E FEEDBACK ---
        if self.estado_combate == 'MOVENDO':
            super().update(delta_time, paredes)
            self.aplicar_camera_shake()

        # --- DIREÇÃO DA SPRITE ---
        self.estado_animacao = 'left' if self.jogador.posicao.x < self.posicao.x else 'right'
        
        self.animar()

    def logica_laser(self, agora, delta_time): # Adicione delta_time aqui
        if self.estado_combate == 'MOVENDO':
            if agora - self.ultimo_laser > self.cooldown_laser:
                self.estado_combate = 'CARREGANDO'
                self.tempo_inicio_carga = agora
                # Reseta a mira do laser para a posição do Scarab antes de começar
                self.beam_principal.mira_atual = pygame.math.Vector2(self.posicao)
        
        elif self.estado_combate == 'CARREGANDO':
            self.game.camera.shake(intensidade= 5 * self.intensidade_shake)
            if agora - self.tempo_inicio_carga > self.duracao_carga:
                self.estado_combate = 'DISPARANDO_LASER'
                self.tempo_inicio_laser = agora

        elif self.estado_combate == 'DISPARANDO_LASER':
            self.game.camera.shake(intensidade= 10 * self.intensidade_shake)
            # Atualiza o feixe contínuo
            self.beam_principal.update(delta_time, self.jogador.posicao)
            
            if agora - self.tempo_inicio_laser > self.duracao_laser:
                self.estado_combate = 'MOVENDO'
                self.ultimo_laser = agora

    def draw_laser(self, superficie, deslocamento):
        if self.estado_combate == 'DISPARANDO_LASER':
            # Ajuste o offset para sair de onde quiser (ex: canhão frontal)
            offset_canhao = pygame.math.Vector2(0, -360) 
            self.beam_principal.draw(superficie, deslocamento, origem_offset=offset_canhao)

    def gerenciar_rajada(self, agora):
        if self.tiros_restantes_rajada > 0:
            if agora - self.ultimo_tiro_rajada >= self.delay_entre_tiros:
                self.plasma_array()
                self.tiros_restantes_rajada -= 1
                self.ultimo_tiro_rajada = agora
        else:
            if agora - self.ultimo_tiro_plasma >= self.cooldown_plasma:
                self.tiros_restantes_rajada = self.pente_rajada 
                self.cooldown_plasma = random.choice(self.opcoes_cooldown)
                self.ultimo_tiro_plasma = agora

    def plasma_array(self):
        # Dispara de dois "canhões laterais" simulados por offsets
        offsets = [pygame.math.Vector2(160, -40), pygame.math.Vector2(-160, -40)]
        for off in offsets:
            p_pos = self.posicao + off
            dir_tiro = (self.jogador.posicao - p_pos).normalize()
            
            PlasmaGun(
                posicao_inicial=p_pos,
                grupos=(entity_manager.all_sprites, entity_manager.projeteis_inimigos_grupo),
                jogador=self.jogador,
                game=self.game,
                tamanho=(96, 16), # Plasma "Heavy"
                dano= 20,
                velocidade=750,
                direcao_spread=dir_tiro
            )

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            frames = self.sprites[self.estado_animacao]
            self.frame_atual = (self.frame_atual + 1) % len(frames)
            self.image = frames[self.frame_atual]

    def aplicar_camera_shake(self):
        # O peso do Scarab: treme a cada passo
        if self.frame_atual in [0, 2]:
            self.game.camera.shake(intensidade= self.intensidade_shake)

    def morrer(self, grupos):
        # Explosão épica com muitos itens
        for _ in range(5):
            pos_offset = self.posicao + pygame.math.Vector2(random.randint(-100, 100), random.randint(-100, 100))
            Items(posicao=pos_offset, sheet_item=join('assets', 'img', 'bigShard.png'), 
                  tipo='big_shard', grupos=(entity_manager.all_sprites, entity_manager.item_group))
        self.kill()