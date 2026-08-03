import pygame

class GuardianAI:
    def executar_estados(self, agora, delta_time, dist_sq):
        
        if self.estado_habilidade == 'idle':
            
            # Respeita a trava global pós-ataques
            if agora < getattr(self, 'trava_global', 500):
                return
            
        if agora - self.tempo_ultimo_emp >= self.cooldown_emp:
            self.disparar_emp()
            self.tempo_ultimo_emp = agora
