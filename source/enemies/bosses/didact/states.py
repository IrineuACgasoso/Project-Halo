# enemies/didact/states.py
import pygame
import random

class DidactAI:
    """Mixin que contém a máquina de estados, transição de fases e decisões (IA) do Didact."""

    @property
    def collision_rect(self):
        return self.hitbox

    def verificar_fases(self):
        percentual_vida = self.vida / self.vida_base
        
        # Fase Cryptum (25%)
        if percentual_vida <= 0.25 and not self.entrou_fase_cryptum:
            self.entrou_fase_cryptum = True
            self.ativar_cryptum()
            self.enrage = False 

        # Enrage (15%)
        if percentual_vida < 0.15 and not self.enrage:
            self.enrage = True
            self.cooldown_laser = self.enraged_laser
            self.duracao_aviso_laser = 200
            self.cooldown_pull = 9999999
            
        elif percentual_vida < 0.5 and not self.enrage:
            self.velocidade_animacao = 180
            self.velocidade_puxao = 600
            
        elif percentual_vida < 0.6 and not self.enrage:
            self.velocidade_base = 90
            self.velocidade_animacao = 200
            self.velocidade_puxao = 600
            
        elif percentual_vida < 0.75 and not self.enrage:
            self.velocidade_base = 70
            self.velocidade_animacao = 250
            self.velocidade_puxao = 550

    def executar_estados(self, agora, delta_time):
        distancia_sq = self.posicao.distance_squared_to(self.jogador.posicao)

        # CRYPTUM
        if self.estado_habilidade == 'crypt':
            self.velocidade = self.velocidade_cryptum
            if agora - self.tempo_ultimo_emp >= self.cooldown_emp:
                self.disparar_emp()
                self.tempo_ultimo_emp = agora
                
            if agora - self.tempo_ultima_artilharia >= self.cooldown_artilharia:
                self.disparar_artilharia()
                self.tempo_ultima_artilharia = agora

            escudo = getattr(self, 'escudo_atual', 0)
            if not self.enrage and escudo <= 0:
                self.estado_habilidade = 'parado'
                self.velocidade = self.velocidade_base
                self.tempo_ultimo_laser = agora
                self.tempo_ultimo_pull = agora

        # PULL
        elif self.estado_habilidade == 'ataque_pull':
            self.velocidade = 0
            if agora - self.tempo_ultimo_dano_pull >= self.intervalo_dano_pull:
                self.jogador.tomar_dano_direto(self.dano_pull)
                self.tempo_ultimo_dano_pull = agora
                
            if agora - self.tempo_inicio_pull >= self.duracao_pull:
                self.estado_habilidade = 'parado'
                self.velocidade = self.velocidade_base
            else:
                self.aplicar_efeito_pull(delta_time)

        # AVISO LASER
        elif self.estado_habilidade == 'aviso_laser':
            if agora - self.tempo_inicio_laser >= self.duracao_aviso_laser:
                self.estado_habilidade = 'disparo_laser'
                self.tempo_inicio_laser = agora
                self.disparar_laser()
                self.rect.center = self.posicao

        # DISPARO LASER
        elif self.estado_habilidade == 'disparo_laser':
            if agora - self.tempo_inicio_laser >= self.duracao_disparo_laser:
                self.velocidade = self.velocidade_base
                if not self.enrage:
                    self.cooldown_laser = self.novo_cooldown(4000, 5500)
                self.estado_habilidade = 'parado'

        # PARADO / DECIDINDO AÇÃO
        else:
            # OTIMIZAÇÃO: 500 elevado ao quadrado é 250000. 
            if distancia_sq > 250000 and (agora - self.tempo_ultimo_pull >= self.cooldown_pull):
                self.puxar_jogador()
            elif agora - self.tempo_ultimo_laser >= self.cooldown_laser:
                self.ativar_laser()

    