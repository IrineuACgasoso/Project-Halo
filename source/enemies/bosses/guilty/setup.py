import pygame
import random

class GuiltySetup:
    def inicializar_habilidades(self):
        self.estado_habilidade = 'idle'
        self.enrage = False
        self.velocidade_anterior = self.velocidade_base
        self.wait = 1000 # Tempo de "cast" antes de soltar a habilidade
        
        self._setup_sentinels()
        self._setup_laser()
        self._setup_tp()

    def _setup_sentinels(self):
        self.start_sentinel = pygame.time.get_ticks()
        self.cooldown_invocacao = self.novo_cooldown(3000, 10000)
        self.ultima_invocacao = pygame.time.get_ticks()
        self.offset_invocacao = 150

    def _setup_laser(self):
        self.num_laser = 1
        self.laser_restantes = 0
        self.intervalo_burst = 150
        self.cooldown_laser = self.novo_cooldown(3000, 10000)
        self.ultimo_laser = pygame.time.get_ticks()
        self.start_laser = 0

    def _setup_tp(self):
        self.cooldown_tp = 3000
        self.ultimo_tp = pygame.time.get_ticks()