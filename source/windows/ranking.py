import pygame
import math
import os
from os.path import join


class Ranking:
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

        # ── Cores ──────────────────────────────────────────────────────────────
        self.COR_CIANO       = (0, 255, 255)
        self.COR_CIANO_ESC   = (0, 120, 140)
        self.COR_BRANCO      = (255, 255, 255)
        self.COR_AZUL        = (70, 140, 210)
        self.COR_AMARELO     = (255, 200, 50)
        self.COR_OURO        = (215, 175, 55)
        self.COR_PRATA       = (192, 192, 192)
        self.COR_BRONZE      = (140, 90, 40)
        self.COR_BORDA       = (0, 180, 200)
        self.COR_VERMELHO    = (255, 60, 60)

        # ── Ranks coloridos (top 3) ────────────────────────────────────────────
        self.RANK_CORES = {
            0: self.COR_OURO,
            1: self.COR_PRATA,
            2: self.COR_BRONZE,
        }
        self.RANK_LABELS = {0: "01", 1: "02", 2: "03"}

        # ── Scanlines ──────────────────────────────────────────────────────────
        from source.windows.settings import largura_tela, altura_tela
        self.largura = largura_tela
        self.altura  = altura_tela
        self._scanlines = self._gerar_scanlines()

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _gerar_scanlines(self):
        surf = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        for y in range(0, self.altura, 3):
            pygame.draw.line(surf, (0, 0, 0, 35), (0, y), (self.largura, y))
        return surf

    def _desenhar_grade(self, tela):
        cor = (0, 35, 50)
        tam = 55
        for x in range(-tam, self.largura + tam, tam):
            for y in range(-tam, self.altura + tam, tam):
                offset = tam // 2 if (x // tam) % 2 == 0 else 0
                centro = (x, y + offset)
                pts = [
                    (centro[0] + tam // 2 * math.cos(math.radians(60 * i)),
                     centro[1] + tam // 2 * math.sin(math.radians(60 * i)))
                    for i in range(6)
                ]
                pygame.draw.polygon(tela, cor, pts, 1)

    def _desenhar_painel(self, tela, cx, cy, largura, altura):
        m = 3
        surf = pygame.Surface((largura + m * 2, altura + m * 2), pygame.SRCALPHA)
        surf.fill((5, 15, 25, 185))
        corte = 16
        pts = [
            (corte + m, m),              (largura - corte + m, m),
            (largura + m, corte + m),    (largura + m, altura - corte + m),
            (largura - corte + m, altura + m), (corte + m, altura + m),
            (m, altura - corte + m),     (m, corte + m)
        ]
        alpha_b = int(130 + math.sin(self.timer * 2) * 40)
        pygame.draw.polygon(surf, (*self.COR_BORDA, alpha_b), pts, 2)
        for px, py in [(m, m), (largura + m, m), (m, altura + m), (largura + m, altura + m)]:
            pygame.draw.circle(surf, (*self.COR_AMARELO, 200), (px, py), 4)
        tela.blit(surf, surf.get_rect(center=(cx, cy)))

    def _glow_text(self, tela, texto, fonte, cx, cy, cor, cor_glow=None, align='center'):
        if cor_glow is None:
            cor_glow = self.COR_CIANO
        for off in range(1, 3):
            g = fonte.render(texto, True, cor_glow)
            g.set_alpha(max(0, 70 // off))
            r = g.get_rect(**{align: (cx, cy)}) if align != 'center' else g.get_rect(center=(cx, cy))
            for dx, dy in [(-off,0),(off,0),(0,-off),(0,off)]:
                tela.blit(g, (r.x+dx, r.y+dy))
        txt = fonte.render(texto, True, cor)
        r = txt.get_rect(center=(cx, cy))
        tela.blit(txt, r)

    def _linha_divisoria(self, tela, cx, y, comprimento=500, alpha=120):
        surf = pygame.Surface((comprimento, 2), pygame.SRCALPHA)
        for x in range(comprimento):
            dist = abs(x - comprimento // 2) / (comprimento // 2)
            a = int(alpha * (1 - dist))
            surf.set_at((x, 0), (*self.COR_CIANO, a))
            surf.set_at((x, 1), (*self.COR_CIANO_ESC, a // 2))
        tela.blit(surf, surf.get_rect(center=(cx, y)))

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

    # ── Draw ───────────────────────────────────────────────────────────────────

    def draw(self, tela):
        self.timer += 0.012
        cx = self.largura // 2

        # Fundo
        tela.fill((4, 10, 18))
        self._desenhar_grade(tela)
        tela.blit(self._scanlines, (0, 0))

        if self.input_mode:
            self._draw_input(tela, cx)
        else:
            self._draw_tabela(tela, cx)

    def _draw_tabela(self, tela, cx):
        # ── Título ─────────────────────────────────────────────────────────────
        brilho = int(210 + math.sin(self.timer * 3) * 45)
        self._glow_text(tela, "HALL OF FAME", self.font_titulo, cx, 90,
                        self.COR_BRANCO, self.COR_CIANO)
        sub = self.font_dica.render("REGISTRO DE OPERADORES DISTINTOS — INSTALAÇÃO 04", True, self.COR_CIANO_ESC)
        tela.blit(sub, sub.get_rect(center=(cx, 138)))
        self._linha_divisoria(tela, cx, 165)

        # ── Painel da tabela ───────────────────────────────────────────────────
        painel_w = 750
        painel_h = 430
        painel_cy = 165 + 20 + painel_h // 2
        self._desenhar_painel(tela, cx, painel_cy, painel_w, painel_h)

        # Cabeçalho da tabela
        header_y = painel_cy - painel_h // 2 + 30
        for texto, offset in [("RANK", -290), ("OPERADOR", -120), ("PONTUAÇÃO", 200)]:
            h = self.font_dica.render(texto, True, self.COR_CIANO_ESC)
            tela.blit(h, h.get_rect(center=(cx + offset, header_y)))
        self._linha_divisoria(tela, cx, header_y + 18, comprimento=painel_w - 60, alpha=70)

        # Linhas de score
        if not self.scores:
            vazio = self.font_label.render("— SEM REGISTROS —", True, self.COR_CIANO_ESC)
            tela.blit(vazio, vazio.get_rect(center=(cx, painel_cy)))
        else:
            linha_h = 36
            for i, s in enumerate(self.scores):
                ly = header_y + 36 + i * linha_h

                # Destaque nas 3 primeiras linhas
                if i < 3:
                    dest_surf = pygame.Surface((painel_w - 60, linha_h - 4), pygame.SRCALPHA)
                    alpha_dest = int(30 + math.sin(self.timer * 2 + i) * 10)
                    cor_dest = self.RANK_CORES[i]
                    dest_surf.fill((*cor_dest, alpha_dest))
                    tela.blit(dest_surf, dest_surf.get_rect(center=(cx, ly + linha_h // 2 - 2)))

                cor_texto = self.RANK_CORES.get(i, self.COR_AZUL)

                # Rank
                rank_txt = f"#{i+1:02d}"
                r = self.font_label.render(rank_txt, True, cor_texto)
                tela.blit(r, r.get_rect(center=(cx - 290, ly + 12)))

                # Nome
                nome = self.font_label.render(s['name'][:16], True,
                                              self.COR_BRANCO if i < 3 else self.COR_AZUL)
                tela.blit(nome, nome.get_rect(midleft=(cx - 200, ly + 12)))

                # Score
                score_str = f"{s['score']:,}".replace(',', '.')
                sc = self.font_label.render(score_str, True, cor_texto)
                tela.blit(sc, sc.get_rect(midright=(cx + 330, ly + 12)))

                # Separador sutil
                if i < len(self.scores) - 1:
                    self._linha_divisoria(tela, cx, ly + linha_h - 2,
                                         comprimento=painel_w - 80, alpha=35)

        # ── Dica de saída ──────────────────────────────────────────────────────
        dica = self.font_dica.render("[ ESC ]  RETORNAR AO MENU", True, self.COR_CIANO_ESC)
        tela.blit(dica, dica.get_rect(center=(cx, self.altura - 50)))

    def _draw_input(self, tela, cx):
        cy = self.altura // 2

        # ── Título ─────────────────────────────────────────────────────────────
        self._glow_text(tela, "MISSÃO ENCERRADA", self.font_titulo,
                        cx, cy - 190, self.COR_BRANCO, self.COR_VERMELHO)
        self._linha_divisoria(tela, cx, cy - 148)

        # ── Painel ─────────────────────────────────────────────────────────────
        self._desenhar_painel(tela, cx, cy, 600, 280)

        # Score
        score_str = f"{self.current_score:,}".replace(',', '.')
        label_sc = self.font_dica.render("PONTUAÇÃO REGISTRADA", True, self.COR_CIANO_ESC)
        tela.blit(label_sc, label_sc.get_rect(center=(cx, cy - 95)))
        self._glow_text(tela, score_str, self.font_titulo,
                        cx, cy - 55, self.COR_OURO, self.COR_AMARELO)

        self._linha_divisoria(tela, cx, cy - 15, comprimento=500, alpha=60)

        # Label input
        lbl = self.font_dica.render("IDENTIFIQUE-SE, OPERADOR", True, self.COR_CIANO_ESC)
        tela.blit(lbl, lbl.get_rect(center=(cx, cy + 15)))

        # Campo de texto
        campo_w, campo_h = 440, 52
        campo_rect = pygame.Rect(cx - campo_w // 2, cy + 35, campo_w, campo_h)

        # Glow pulsante no campo
        alpha_g = int(40 + math.sin(self.timer * 6) * 20)
        glow_s = pygame.Surface((campo_w + 10, campo_h + 10), pygame.SRCALPHA)
        pygame.draw.rect(glow_s, (*self.COR_CIANO, alpha_g),
                         (0, 0, campo_w + 10, campo_h + 10), border_radius=6)
        tela.blit(glow_s, (campo_rect.x - 5, campo_rect.y - 5))

        pygame.draw.rect(tela, (8, 22, 32), campo_rect, border_radius=5)
        pygame.draw.rect(tela, self.COR_CIANO, campo_rect, 2, border_radius=5)

        # Texto digitado + cursor piscante
        cursor = "|" if int(self.timer * 60) % 30 < 15 else ""
        nome_surf = self.font_input.render(self.player_name + cursor, True, self.COR_BRANCO)
        tela.blit(nome_surf, nome_surf.get_rect(center=campo_rect.center))

        # Dica
        dica = self.font_dica.render("ENTER  para confirmar", True, self.COR_CIANO_ESC)
        tela.blit(dica, dica.get_rect(center=(cx, cy + 110)))