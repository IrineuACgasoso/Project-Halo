import pygame

class GuardianSetup:
    def inicializar_habilidades(self):
        self.estado_habilidade = 'idle'
        self.trava_global = 0 
        
        self._setup_emp()

    def _setup_emp(self):
        self.cooldown_emp = 3000
        self.tempo_ultimo_emp = 0