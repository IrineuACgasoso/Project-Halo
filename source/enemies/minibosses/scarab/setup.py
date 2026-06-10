import pygame
from source.feats.effects import ContinuousBeam

class ScarabSetup:
    def inicializar_sistemas(self):
        # Hitbox Massiva
        self.usar_circulo = True 
        self.radius = 250

        # === SISTEMA DE ESCUDO E STUN ===
        self.escudo_maximo = 5000  # Ajuste conforme o balanceamento desejado
        self.adicionar_escudo(self.escudo_maximo)
        self.duracao_stun = 6000   # Fica 6 segundos vulnerável
        self.tempo_inicio_stun = 0

        # Estados e Fases
        self.estado_combate = 'MOVENDO'
        self.fase_desestabilizado = False
        self.fase_critica = False 
        self.intensidade_shake = 1

        # Armamentos
        self._setup_laser()
        self._setup_plasma()

    def _setup_laser(self):
        self.tempo_inicio_carga = 0
        self.duracao_carga = 3000
        self.duracao_laser = 5000
        self.cooldown_laser = 12000
        self.ultimo_laser = pygame.time.get_ticks()
        
        self.beam_principal = ContinuousBeam(
            self, color=(100, 255, 100), largura_base=40, dano_por_segundo=200, suavizacao=0.08
        )

    def _setup_plasma(self):
        self.cooldown_plasma = self.novo_cooldown(4000, 10000)
        self.ultimo_tiro_plasma = pygame.time.get_ticks()
        self.tiros_restantes_rajada = 0
        self.pente_rajada = 6
        self.delay_entre_tiros = 250 
        self.ultimo_tiro_rajada = 0