import pygame

class TartarusSetup:
    def inicializar_habilidades(self):
        """Configura os atributos iniciais, escudos e flags do Tartarus."""
        self.estado_habilidade = 'idle'
        self.escudo_ativo = True
        self.velocidade_anterior = self.velocidade_base
        self.wait = 0

        # === CONFIGURAÇÃO DO HAMMER RUN ===
        self.cooldown_hammer = 5000 
        self.ultimo_hammer = 0
        self.hammer_target = None
        self.hammer_start_time = 0
        self.hammer_duration_max = 2500 # Tempo limite para a corrida (failsafe)

        # --- SETUP DO SALTO ---
        self.cooldown_pulo = 8000 # Salto tem cooldown mais longo
        self.ultimo_pulo = 0
        self.duracao_pulo = 1200  # Tempo no ar em ms

        # --- ANTI-STUCK SETUP ---
        self.ultimo_check_posicao = 0
        self.posicao_anterior = pygame.math.Vector2(self.posicao.x, self.posicao.y)

        # === CONFIGURAÇÃO DO ENERGY SMASH ===
        self.cooldown_smash = 7000
        self.ultimo_smash = 0
        self.fase_smash = 0
        self.tempo_proximo_smash = 0

        # Habilidade: Burst burst
        self.cooldown_burst = 6000
        self.intervalo_burst = 50
        self.cronometro_burst = 0
        self.ultimo_burst = 0
        self.burst_restante = 0
        self.contagem_burst = 100

        # Habilidade: Spike (artilharia de aviso)
        self.ultimo_spike = 0
        self.cooldown_spike = 6000