import pygame

class HunterAI:
    def executar_estados(self, agora, delta_time, dist_sq):
        
        # ==========================================
        # MÁQUINA DE ESTADOS PRINCIPAL (EXCLUSIVA)
        # ==========================================
        if self.estado_habilidade == 'idle':
            
            # Respeita a trava global pós-ataques
            if agora < getattr(self, 'trava_global', 500):
                self.velocidade = self.velocidade_base
                return

            pode_run = agora - getattr(self, 'tempo_ultima_run', 0) >= getattr(self, 'cooldown_run', 6000)
            pode_cannon = agora - getattr(self, 'tempo_ultimo_cannon', 0) >= getattr(self, 'cooldown_cannon', 3000)
            pode_burst = agora - getattr(self, 'tempo_ultimo_burst', 0) >= getattr(self, 'cooldown_burst', 4000)

            # Prioridade 1: Investida (se estiver disponível)
            if pode_run:
                self.iniciar_run(agora)
            # Prioridade 2: Morteiro (Cannon)
            elif pode_cannon:
                self.estado_habilidade = 'cannon'
                self.tempo_ultimo_cannon = agora
            # Prioridade 3: Metralhadora (Burst)
            elif pode_burst:
                self.estado_habilidade = 'burst'
                self.burst_restante = self.contagem_burst
                self.tempo_ultimo_burst = agora

        elif self.estado_habilidade == 'stun':
            self.processar_stun(agora)

        elif self.estado_habilidade == 'burst':
            self.processar_burst(agora, delta_time)

        elif self.estado_habilidade == 'cannon':
            self.processar_cannon(agora)