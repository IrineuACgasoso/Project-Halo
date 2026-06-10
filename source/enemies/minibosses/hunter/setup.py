import pygame

class HunterSetup:
    def inicializar_habilidades(self):
        self.estado_habilidade = 'idle'
        self.trava_global = 0 
        
        self._setup_run()
        self._setup_burst()
        self._setup_cannon()

    def _setup_run(self):
        self.cooldown_run = 7000
        self.tempo_ultima_run = 0
        self.duracao_run = 2500          # Tempo (ms) que ele fica correndo em linha reta
        self.velocidade_corrida = 500    # Mais rápido para ser ameaçador
        self.vetor_investida = pygame.math.Vector2(0, 0)
        
        self.duracao_stun = 2000         # 2 segundos parado recuperando o fôlego

    def _setup_burst(self):
        self.cooldown_burst = 4000
        self.tempo_ultimo_burst = 0
        self.contagem_burst = 10
        self.burst_restante = 0
        self.intervalo_burst = 150
        self.cronometro_burst = 0

    def _setup_cannon(self):
        self.cooldown_cannon = 3000
        self.tempo_ultimo_cannon = 0