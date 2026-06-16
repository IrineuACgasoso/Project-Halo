# No seu arquivo de setup do boss (ex: setup.py)
import pygame
from source.feats.effects import ContinuousBeam

class GuiltySetup:
    def inicializar_habilidades(self):
        # === MÁQUINA DE ESTADOS DE FASE ===
        self.estado_fase = 'FASE1' 
        self.estado_habilidade = 'idle'
        self.enrage = False
        self.imune = False
        self.velocidade_anterior = self.velocidade_base
        self.wait = 0 

        self.terminais = []
        self.sentinelas_majors = [] 

        # === CONFIGURAÇÃO DO LASER RASTREÁVEL ===
        self.beam_principal = ContinuousBeam(
            self, color=(0, 150, 255), largura_base=25, dano_por_segundo=200, suavizacao=0.1
        )
        self.duracao_laser_rastreavel = 4000
        self.tempo_inicio_laser = 0
        self.cooldown_laser = self.novo_cooldown(4000, 8000)
        self.ultimo_laser = pygame.time.get_ticks()

        # === CONFIGURAÇÃO DA GRADE DE PURGA (BULLET HELL) ===
        self.purge_cooldown = 3000
        self.ultimo_purge = pygame.time.get_ticks()
        self.ataque_purga = None  # Receberá o Worker lógico invisível

        self._setup_sentinels()
        self._setup_tp()

    def _setup_sentinels(self):
        self.start_sentinel = pygame.time.get_ticks()
        self.cooldown_invocacao = self.novo_cooldown(4000, 9000)
        self.ultima_invocacao = pygame.time.get_ticks()
        self.offset_invocacao = 180

    def _setup_tp(self):
        self.cooldown_tp = 2500
        self.ultimo_tp = pygame.time.get_ticks()