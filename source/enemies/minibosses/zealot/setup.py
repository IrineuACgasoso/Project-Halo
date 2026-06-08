import pygame

class ZealotSetup:
    def inicializar_habilidades(self):
        self.estado_habilidade = 'idle' 
        self.multiplicador_sprint = 2.0 # Fica 2x mais rápido correndo atrás do player

        self._setup_rage()
        self._setup_invisibility()
        self._setup_dash()
        self._setup_antistuck() 

    def _setup_rage(self):
        self.rage_mult = 4.2
        self.enrage = False
    
    def _setup_invisibility(self):
        self.last_stealth = pygame.time.get_ticks()
        self.cooldown_stealth = self.novo_cooldown(3000, 4000) 
        self.ja_teleportou = False 

    
    def _setup_dash(self):
        self.last_dash = 0
        self.cooldown_dash = self.novo_cooldown(2000, 3000)                   
        self.dash_speed = self.velocidade_base * 6  # 6x mais rápido que o normal!
        self.dash_direcao = pygame.math.Vector2(0, 0)
        self.tempo_inicio_dash = 0
        self.duracao_prep = 500                     # Meio segundo parado "mirando" antes do bote
        self.duracao_dash = 600                     # Tempo máximo de corrida do dash

    def _setup_antistuck(self):
        self.ultimo_check_posicao = pygame.time.get_ticks()
        self.posicao_anterior = pygame.math.Vector2(self.posicao.x, self.posicao.y)