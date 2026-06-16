import pygame

class ZealotAI:
    def verificar_fases(self):
        if self.vida <= self.vida_base / 2 and not getattr(self, 'enrage', False):
            self.enrage = True
            self.rage_mult *= 1.2

    def executar_estados(self, agora, delta_time, dist_sq):
        # Atualiza as outras fases da invisibilidade (fade_out e hold)
        if getattr(self, 'invis_phase', None) is not None:
            self.atualizar_invisibilidade(delta_time * 1000)

        # TRAVA CRÍTICA: Se estiver reaparecendo, não processa mais nada e mantém o estado atual
        if getattr(self, 'invis_phase', None) == 'fade_in':
            self.velocidade = self.velocidade_base * self.rage_mult
            self.velocidade_animacao = 80
            return
        
        self.checar_anti_stuck(agora, dist_sq)
        
        # --------------------------------------------------
        # 1. PENSADOR (Estado IDLE toma as decisões)
        # --------------------------------------------------
        if self.estado_habilidade == 'idle':
            self.velocidade = self.velocidade_base
            self.velocidade_animacao = 200
            
            # Decisão: Ataque Melee (Colado)
            if dist_sq < 4000:
                self.estado_habilidade = 'melee'
                self.tempo_ataque = agora

            # Decisão: Dash (Distância Média)
            elif 62500 < dist_sq < 250000 and (agora - getattr(self, 'last_dash', 0) > self.cooldown_dash):
                self.estado_habilidade = 'dash_prep'
                self.tempo_inicio_dash = agora
                
                vetor_alvo = self.jogador.posicao - self.posicao
                if vetor_alvo.length() > 0:
                    self.dash_direcao = vetor_alvo.normalize()
                else:
                    self.dash_direcao = pygame.math.Vector2(1, 0)
                    
            # Decisão: Stealth/Teleporte (Perto, mas não colado)
            elif dist_sq < 160000 and (agora - getattr(self, 'last_stealth', 0) > self.cooldown_stealth):
                self.estado_habilidade = 'stealth'
                self.ja_teleportou = False
                self.iniciar_invisibilidade(alpha_alvo=0, fade_out=500, fade_in=1500, duracao=4000)

            # Decisão: Sprint (Longe)
            elif dist_sq >= 250000:
                self.estado_habilidade = 'sprint'

        # --------------------------------------------------
        # 2. EXECUTOR (Chama os ataques do attacks.py)
        # --------------------------------------------------
        elif self.estado_habilidade == 'melee':
            self.processar_melee(agora, dist_sq)
            
        elif self.estado_habilidade == 'dash_prep':
            self.velocidade_animacao = 300
            self.processar_dash_prep(agora)
            
        elif self.estado_habilidade == 'dashing':
            self.velocidade_animacao = 40
            self.processar_dash(agora, delta_time, dist_sq)
            
        elif self.estado_habilidade == 'stealth':
            self.velocidade_animacao = 200
            self.processar_stealth(agora)
            
        elif self.estado_habilidade == 'sprint':
            self.velocidade_animacao = 120
            self.processar_sprint(dist_sq)