import pygame
import random

class GuiltyAI:
    def verificar_fases(self):
        if self.vida <= self.vida_base / 2 and not self.enrage:
            self.rage()

    def executar_estados(self, agora):
        # FSM: Tomada de Decisão
        if self.estado_habilidade == 'idle':
            self.velocidade = self.velocidade_anterior # Restaura velocidade bufada
            
            # OTIMIZAÇÃO: distance_squared_to evita raiz quadrada! (900 * 900 = 810000)
            distancia_sq = self.posicao.distance_squared_to(self.jogador.posicao)
            
            if agora - self.ultimo_laser >= self.cooldown_laser:
                self.estado_habilidade = 'laser'
                self.laser_restantes = self.num_laser
                self.start_laser = agora
                self.velocidade = 0 
                
            elif agora - self.ultima_invocacao >= self.cooldown_invocacao:
                self.estado_habilidade = 'sentinel'
                self.start_sentinel = agora
                self.velocidade = 0
                
            elif distancia_sq > 810000 and (agora - self.ultimo_tp >= self.cooldown_tp):
                self.estado_habilidade = 'teleporte'
                self.velocidade = 0

        # FSM: Execução
        if self.estado_habilidade == 'laser':
            self.laser_attack()
        elif self.estado_habilidade == 'sentinel':
            self.invocar_sentinelas()
        elif self.estado_habilidade == 'teleporte':
            self.teleporte()