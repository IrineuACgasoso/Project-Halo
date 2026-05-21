import pygame
import math
import os
from os.path import join

from .ranking_draw import RankingDraw
from .ranking_constants import *


class Ranking(RankingDraw):
    def __init__(self, game):
        self.game   = game
        self.scores = []
        self.timer  = 0

        # ── Estado de input ────────────────────────────────────────────────────
        self.input_mode    = False
        self.player_name   = ""
        self.current_score = 0

        # ── Fontes ─────────────────────────────────────────────────────────────
        font_path = join('assets', 'fonts', 'orbitron', 'Orbitron-Bold.ttf')
        try:
            if os.path.exists(font_path):
                self.font_titulo = pygame.font.Font(font_path, 48)
                self.font_label  = pygame.font.Font(font_path, 20)
                self.font_valor  = pygame.font.Font(font_path, 16)
                self.font_input  = pygame.font.Font(font_path, 28)
                self.font_dica   = pygame.font.Font(font_path, 13)
            else:
                raise FileNotFoundError
        except Exception:
            self.font_titulo = pygame.font.SysFont('Consolas', 48, bold=True)
            self.font_label  = pygame.font.SysFont('Consolas', 20, bold=True)
            self.font_valor  = pygame.font.SysFont('Consolas', 16)
            self.font_input  = pygame.font.SysFont('Consolas', 28, bold=True)
            self.font_dica   = pygame.font.SysFont('Consolas', 13)

        # ── Ranks coloridos (top 3) ────────────────────────────────────────────
        self.RANK_CORES = {
            0: COR_OURO,
            1: COR_PRATA,
            2: COR_BRONZE,
        }
        self.RANK_LABELS = {0: "01", 1: "02", 2: "03"}

        # ── Scanlines ──────────────────────────────────────────────────────────
        from source.windows.settings import largura_tela, altura_tela
        self.largura = largura_tela
        self.altura  = altura_tela
        self._scanlines = self._gerar_scanlines()

    
    # ── Interface pública ───────────────────────────────────────────────────────

    def start_name_input(self, score):
        self.input_mode    = True
        self.player_name   = ""
        self.current_score = score

    def _confirmar_nome(self):
        nome = self.player_name.strip() or "OPERADOR"
        self.scores.append({'name': nome.upper(), 'score': self.current_score})
        self.scores = sorted(self.scores, key=lambda x: x['score'], reverse=True)[:10]
        self.input_mode = False

    def handle_event(self, evento):
        if self.input_mode:
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN:
                    self._confirmar_nome()
                elif evento.key == pygame.K_BACKSPACE:
                    self.player_name = self.player_name[:-1]
                elif len(self.player_name) < 16:
                    if evento.unicode.isprintable():
                        self.player_name += evento.unicode.upper()
            return None

        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            return 'exit_to_menu'
        return None
