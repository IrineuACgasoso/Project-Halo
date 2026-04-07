import pygame
import random
import math
from os.path import join
from source.enemies.enemies import *
from source.feats.assets import ASSETS
from source.systems.entitymanager import entity_manager


class Zealot(InimigoBase):
    def __init__(self, posicao, game, grupos):
        valor_vida = 1800
        super().__init__(posicao, vida_base=valor_vida, dano_base=80, velocidade_base=100, game=game, sprite_key='zealot')
        self.titulo = "ZEALOT, Soldado de Elite Covenant"

        self.posicao = pygame.math.Vector2(posicao)

        # Sprites e Animação
        self.sprites = self.get_sprites('default')
        self.frame_atual = 0  
        self.estado_animacao = 'right'
        self.image = self.sprites[self.estado_animacao][0]
        self.rect = self.image.get_rect(center=self.posicao)
        self.velocidade_animacao = 200
        self.ultimo_update_animacao = pygame.time.get_ticks()
        
        # FSM e Variáveis de Habilidade
        self.estado_habilidade = 'idle' 
        self.alpha = 255
        self.rage_mult = 4.0
        self.enrage = False
        self.last_stealth = pygame.time.get_ticks()
        
        # Cooldowns e Timers
        self.cooldown_stealth = random.randint(3000, 6000) # Cooldown inicial aleatório
        self.tempo_invisivel_perseguindo = 2500 # Quanto tempo (ms) ele corre invisível após o TP
        self.inicio_perseguicao_invisivel = 0

        self.hitbox = pygame.Rect(0, 0, self.rect.width / 2, self.rect.height)

    def stealth_dash(self, paredes):
        """Lógica de perseguição: 1s invisível + 0.5s aparecendo, sempre correndo."""
        agora = pygame.time.get_ticks()
        tempo_decorrido = agora - self.inicio_perseguicao_invisivel

        # 1. Fase de Fade Out (Sumindo)
        if self.estado_habilidade == 'stealth_out':
            if self.alpha > 0:
                self.alpha = max(0, self.alpha - 15)
            else:
                self.realizar_teleporte()
                self.estado_habilidade = 'stealth_hunting'
                self.inicio_perseguicao_invisivel = pygame.time.get_ticks()

        # 2. Fase de Perseguição
        elif self.estado_habilidade in ['stealth_hunting', 'stealth_in']:
            # MOVIMENTAÇÃO: Ele corre durante todo o processo (Hunting + In)
            direcao = (self.game.player.posicao - self.posicao)
            if direcao.length() > 5:
                direcao.normalize_ip()
                self.posicao += direcao * (self.velocidade * self.rage_mult) * self.dt
            
            # LÓGICA DE VISIBILIDADE
            if tempo_decorrido < 1500:
                # Primeiro 0.8 segundo: Totalmente invisível
                self.alpha = 0
            else:
                # Após 1 segundo: Começa o Fade In
                self.estado_habilidade = 'stealth_in'
                if self.alpha < 255:
                    self.alpha = min(255, self.alpha + 15)
                
            # FINALIZAÇÃO: Só encerra quando o tempo total (1.5s) bater E o alpha estiver cheio
            if tempo_decorrido > self.tempo_invisivel_perseguindo and self.alpha >= 255:
                self.finalizar_habilidade()
        
        # Aplica o alpha no frame atual
        self.image.set_alpha(self.alpha)


    def realizar_teleporte(self):
        raio_min = 500
        raio_max = 750
        tentativas = 40  # Quantas vezes ele tenta achar um ponto válido antes de desistir
        
        for _ in range(tentativas):
            # 1. Sorteia um ângulo e uma distância aleatória ao redor do PLAYER
            angulo = random.uniform(0, 2 * math.pi)
            distancia = random.uniform(raio_min, raio_max)
            
            # 2. Calcula a posição candidata
            nova_x = self.game.player.posicao.x + math.cos(angulo) * distancia
            nova_y = self.game.player.posicao.y + math.sin(angulo) * distancia
            pos_candidata = pygame.math.Vector2(nova_x, nova_y)

            # 3.  Pergunta para o mapa se esse ponto é seguro
            if self.game.mapa.posicao_e_valida(pos_candidata):
                # Se for válido, teleporta e encerra a função
                self.posicao = pos_candidata
                self.rect.center = (round(self.posicao.x), round(self.posicao.y))
                self.hitbox.center = self.rect.center
                return True # Sucesso!
                
        return False # Falhou em achar um lugar (player pode estar encurralado)

    def finalizar_habilidade(self):
        self.alpha = 255
        self.image.set_alpha(self.alpha)
        self.last_stealth = pygame.time.get_ticks()
        self.cooldown_stealth = random.randint(2500, 4500)  # Novo cooldown aleatório
        self.estado_habilidade = 'idle'

    def update(self, delta_time, paredes=None):
        self.dt = delta_time # Armazena para uso no stealth_dash
        agora = pygame.time.get_ticks()
        dist_player = (self.game.player.posicao - self.posicao).length()

        if self.vida <= self.vida_base / 2 and not self.enrage:
            self.enrage = True
            self.rage_mult *= 1.3

        # Máquina de Estados de Movimento
        if self.estado_habilidade == 'idle':
            direcao = (self.game.player.posicao - self.posicao)
            if direcao.length() > 20: # Não tremer em cima do player
                direcao.normalize_ip()
                self.posicao += direcao * self.velocidade * delta_time
            
            if dist_player < 500 and agora - self.last_stealth > self.cooldown_stealth:
                self.estado_habilidade = 'stealth_out'
        
        else:
            self.stealth_dash(paredes)

        # Colisões Físicas Constantes (Impede atravessar paredes empurrado)
        if paredes and self.estado_habilidade != 'stealth_out':
            self.aplicar_colisao_mapa(paredes, self.raio_colisao_mapa)
            
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        
        # Animação
        self.estado_animacao = 'left' if (self.game.player.posicao.x < self.posicao.x) else 'right'
        self.animar()
    
    def morrer(self, grupos = None):
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 3, 100)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 50)
        Items.spawn_drop(self.posicao, grupos, 'cafe', 1, 1)
        self.kill()

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            self.image.set_alpha(self.alpha) # Garante que o frame novo herde a invisibilidade
            self.rect = self.image.get_rect(center=self.posicao)
