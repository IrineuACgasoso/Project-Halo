import pygame
import random
import math

class ZealotAttacks:
    def realizar_teleporte(self):
        raio_min = 550
        raio_max = 600
        tentativas = 40  
        
        for _ in range(tentativas):
            angulo = random.uniform(0, 2 * math.pi)
            distancia = random.uniform(raio_min, raio_max)
            
            nova_x = self.jogador.posicao.x + math.cos(angulo) * distancia
            nova_y = self.jogador.posicao.y + math.sin(angulo) * distancia
            pos_candidata = pygame.math.Vector2(nova_x, nova_y)

            if self.game.mapa.posicao_e_valida(pos_candidata):
                self.posicao = pos_candidata
                return True 
        return False 

    def processar_melee(self, agora, dist_sq):
        self.velocidade = 0 
        if agora - getattr(self, 'tempo_ataque', 0) > 500: 
            if dist_sq < 5000: 
                self.jogador.receber_dano(self.dano_base)
            self.estado_habilidade = 'idle' 

    def processar_dash_prep(self, agora):
        self.velocidade = 0 
        if agora - self.tempo_inicio_dash > self.duracao_prep:
            self.estado_habilidade = 'dashing'
            self.tempo_inicio_dash = agora

    def processar_dash(self, agora, delta_time, dist_sq):
        self.velocidade = 0 
        self.posicao += self.dash_direcao * self.dash_speed * delta_time
        
        if dist_sq < 4000: 
            self.jogador.receber_dano(self.dano_base * 1.5)
            self.estado_habilidade = 'idle'
            self.last_dash = agora
            
        elif agora - self.tempo_inicio_dash > self.duracao_dash: 
            self.cooldown_dash = self.novo_cooldown(300, 900)
            self.estado_habilidade = 'idle'
            self.last_dash = agora

    def processar_stealth(self, agora):
        if self.invisivel:
            if self.invis_phase == "fade_out" or self.invis_phase == "hold":
                self.velocidade = 0
                if self.invis_phase == "hold" and not self.ja_teleportou:
                    self.realizar_teleporte()
                    self.ja_teleportou = True
            elif self.invis_phase == "fade_in":
                self.velocidade = self.velocidade_base * self.rage_mult
        else:
            self.estado_habilidade = 'idle'
            self.last_stealth = agora
            self.cooldown_stealth = self.novo_cooldown(2500, 3500)


    def processar_sprint(self, dist_sq):
        self.velocidade = self.velocidade_base * self.multiplicador_sprint
        if dist_sq <= 240000:
            self.estado_habilidade = 'idle'


    def checar_anti_stuck(self, agora, dist_sq):
        """Sistema de desbugador de parede: Força um teleporte se ficar preso."""
        # Checa a cada 1600ms (1.6 segundos)
        if agora - getattr(self, 'ultimo_check_posicao', 0) > 1600:
            pos_anterior = getattr(self, 'posicao_anterior', self.posicao)
            
            # Quão longe ele andou nos últimos 2 segundos?
            dist_movida_sq = self.posicao.distance_squared_to(pos_anterior)
            
            # Se moveu menos de ~30 pixels (900 sq) E está fora da zona stealth normal (> 160000)
            # Evitamos resetar se ele estiver legitimamente parado (idle, dash_prep, atacando)
            if dist_movida_sq < 900 and dist_sq > 160000 and self.estado_habilidade in ['idle', 'sprint']:
                
                # FORÇA A INVISIBILIDADE/TELEPORTE PARA SAIR DA PAREDE!
                self.estado_habilidade = 'stealth'
                self.ja_teleportou = False
                self.iniciar_invisibilidade(alpha_alvo=0, fade_out=500, fade_in=1500, duracao=4000)
                self.last_stealth = agora # Atualiza o timer para ele não floodar teleportes
            
            # Salva a nova posição atual para o check dos próximos 2 segundos
            self.ultimo_check_posicao = agora
            self.posicao_anterior = pygame.math.Vector2(self.posicao.x, self.posicao.y)