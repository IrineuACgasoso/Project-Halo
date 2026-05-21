import pygame
import math
import os
from os.path import join
from random import randint
from abc import ABC, abstractmethod
from .settings_draw import SettingsDraw
from .settings_constants import *


class Settings(SettingsDraw):
    def __init__(self, game):
        self.game = game
        self.timer = 0

        # ── Fontes ─────────────────────────────────────────────────────────────
        font_path = join('assets', 'fonts', 'orbitron', 'Orbitron-Bold.ttf')
        try:
            if os.path.exists(font_path):
                self.font_titulo  = pygame.font.Font(font_path, 52)
                self.font_label   = pygame.font.Font(font_path, 22)
                self.font_valor   = pygame.font.Font(font_path, 18)
                self.font_dica    = pygame.font.Font(font_path, 14)
            else:
                raise FileNotFoundError
        except Exception:
            self.font_titulo = pygame.font.SysFont('Consolas', 52, bold=True)
            self.font_label  = pygame.font.SysFont('Consolas', 22, bold=True)
            self.font_valor  = pygame.font.SysFont('Consolas', 18)
            self.font_dica   = pygame.font.SysFont('Consolas', 14)

        

        # ── Estado das opções ───────────────────────────────────────────────────
        self.volume           = pygame.mixer.music.get_volume()  # 0.0 ~ 1.0
        self.resolucao_idx    = self._resolucao_atual_idx()
        self.fullscreen       = False

        # Controle de foco (qual "linha" está selecionada: 0=volume, 1=resolução, 2=fullscreen)
        self.foco = 0
        self.num_opcoes = 3

        # ── Superfície de fundo com scanlines ──────────────────────────────────
        self._scanlines = self._gerar_scanlines()

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _resolucao_atual_idx(self):
        tela_info = pygame.display.get_surface().get_size()
        try:
            return RESOLUCOES.index(tela_info)
        except ValueError:
            return 0

    def _gerar_scanlines(self):
        """Gera uma surface semitransparente com linhas horizontais estilo CRT."""
        surf = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
        for y in range(0, altura_tela, 3):
            pygame.draw.line(surf, (0, 0, 0, 40), (0, y), (largura_tela, y))
        return surf

    def _aplicar_resolucao(self):
        res = RESOLUCOES[self.resolucao_idx]
        flags = pygame.FULLSCREEN if self.fullscreen else 0
        pygame.display.set_mode(res, flags)

    def _aplicar_volume(self):
        pygame.mixer.music.set_volume(self.volume)

    # ── Eventos ────────────────────────────────────────────────────────────────

    def handle_event(self, evento):
        if evento.type != pygame.KEYDOWN:
            return None

        key = evento.key

        # Navega entre opções
        if key in (pygame.K_w, pygame.K_UP):
            self.foco = (self.foco - 1) % self.num_opcoes

        elif key in (pygame.K_s, pygame.K_DOWN):
            self.foco = (self.foco + 1) % self.num_opcoes

        # Altera valor da opção focada
        elif key in (pygame.K_a, pygame.K_LEFT):
            self._diminuir()

        elif key in (pygame.K_d, pygame.K_RIGHT):
            self._aumentar()

        # Confirma/toggle
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.foco == 2:  # fullscreen é toggle
                self.fullscreen = not self.fullscreen
                self._aplicar_resolucao()

        # Sai
        elif key == pygame.K_ESCAPE:
            return 'sair'

        return None

    def _diminuir(self):
        if self.foco == 0:   # volume
            self.volume = max(0.0, round(self.volume - 0.1, 1))
            self._aplicar_volume()
        elif self.foco == 1:  # resolução
            self.resolucao_idx = (self.resolucao_idx - 1) % len(RESOLUCOES)
            self._aplicar_resolucao()

    def _aumentar(self):
        if self.foco == 0:   # volume
            self.volume = min(1.0, round(self.volume + 0.1, 1))
            self._aplicar_volume()
        elif self.foco == 1:  # resolução
            self.resolucao_idx = (self.resolucao_idx + 1) % len(RESOLUCOES)
            self._aplicar_resolucao()

    