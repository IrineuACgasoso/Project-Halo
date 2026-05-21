import pygame
import math

from .settings_constants import *

class SettingsDraw:
    # ── Draw ───────────────────────────────────────────────────────────────────

    def draw(self, tela):
        self.timer += 0.012

        # Fundo escuro com gradiente sutil
        tela.fill((4, 10, 18))
        self._desenhar_grade(tela)
        tela.blit(self._scanlines, (0, 0))

        cx = largura_tela // 2

        # ── Título ─────────────────────────────────────────────────────────────
        self._desenhar_titulo(tela, cx)

        # ── Linha divisória ────────────────────────────────────────────────────
        self._desenhar_linha_divisoria(tela, cx, 200)

        # ── Painel de opções ───────────────────────────────────────────────────
        painel_y = 240
        painel_h = 320
        self._desenhar_painel(tela, cx, painel_y, 700, painel_h)

        # ── Opções ─────────────────────────────────────────────────────────────
        opcao_y_base = painel_y + 40
        self._desenhar_volume(tela,    cx, opcao_y_base + 0,   foco=(self.foco == 0))
        self._desenhar_resolucao(tela, cx, opcao_y_base + 110, foco=(self.foco == 1))
        self._desenhar_fullscreen(tela,cx, opcao_y_base + 210, foco=(self.foco == 2))

        # ── Dica de controles ──────────────────────────────────────────────────
        self._desenhar_dica(tela, cx)

        pygame.display.update()

    def _desenhar_grade(self, tela):
        """Grade hexagonal sutil no fundo — visual Forerunner."""
        cor = (0, 40, 55)
        tamanho = 60
        for x in range(-tamanho, largura_tela + tamanho, tamanho):
            for y in range(-tamanho, altura_tela + tamanho, tamanho):
                offset = tamanho // 2 if (x // tamanho) % 2 == 0 else 0
                centro = (x, y + offset)
                pontos = [
                    (centro[0] + tamanho // 2 * math.cos(math.radians(60 * i)),
                     centro[1] + tamanho // 2 * math.sin(math.radians(60 * i)))
                    for i in range(6)
                ]
                pygame.draw.polygon(tela, cor, pontos, 1)

    def _desenhar_titulo(self, tela, cx):
        brilho = int(200 + math.sin(self.timer * 3) * 55)

        # Glow
        for off in range(1, 4):
            glow = self.font_titulo.render("CONFIGURAÇÕES", True, COR_CIANO)
            glow.set_alpha(max(0, 80 // off))
            r = glow.get_rect(center=(cx, 130))
            for dx, dy in [(-off,0),(off,0),(0,-off),(0,off)]:
                tela.blit(glow, (r.x+dx, r.y+dy))

        txt = self.font_titulo.render("CONFIGURAÇÕES", True, COR_BRANCO)
        txt.set_alpha(brilho)
        tela.blit(txt, txt.get_rect(center=(cx, 130)))

        # Subtítulo
        sub = self.font_dica.render("TERMINAL DE CONTROLE DO SISTEMA", True, COR_CIANO_ESCURO)
        tela.blit(sub, sub.get_rect(center=(cx, 175)))

    def _desenhar_linha_divisoria(self, tela, cx, y):
        alpha = int(150 + math.sin(self.timer * 2) * 50)
        comprimento = 600
        surf = pygame.Surface((comprimento, 2), pygame.SRCALPHA)
        for x in range(comprimento):
            # Gradiente: transparente nas pontas, sólido no centro
            dist = abs(x - comprimento // 2) / (comprimento // 2)
            a = int(alpha * (1 - dist))
            surf.set_at((x, 0), (*COR_CIANO, a))
            surf.set_at((x, 1), (*COR_CIANO_ESCURO, a // 2))
        tela.blit(surf, surf.get_rect(center=(cx, y)))

    def _desenhar_painel(self, tela, cx, y, largura, altura):
        # Margem extra para a borda não ser cortada na borda da surface
        m = 3
        surf = pygame.Surface((largura + m*2, altura + m*2), pygame.SRCALPHA)
        surf.fill((5, 15, 25, 180))

        # Borda com cantos cortados (estilo Forerunner)
        corte = 18
        pontos_borda = [
            (corte, 0), (largura - corte, 0),
            (largura, corte), (largura, altura - corte),
            (largura - corte, altura), (corte, altura),
            (0, altura - corte), (0, corte)
        ]
        pygame.draw.polygon(surf, (*COR_BORDA, 160), pontos_borda, 2)

        # Detalhes de canto
        cor_canto = (*COR_AMARELO, 200)
        for px, py in [(0, 0), (largura, 0), (0, altura), (largura, altura)]:
            pygame.draw.circle(surf, cor_canto, (px, py), 4)

        tela.blit(surf, surf.get_rect(center=(cx, y + altura // 2)))

    def _desenhar_volume(self, tela, cx, y, foco):
        label = self.font_label.render("VOLUME", True,
                                       COR_BRANCO if foco else COR_AZUL)
        tela.blit(label, label.get_rect(center=(cx, y)))

        # Corredor (slider)
        slider_w = 400
        slider_h = 22
        sx = cx - slider_w // 2
        sy = y + 30

        # Trilho de fundo
        trilho = pygame.Rect(sx, sy, slider_w, slider_h)
        pygame.draw.rect(tela, (20, 40, 50), trilho, border_radius=4)

        # Preenchimento proporcional ao volume
        fill_w = int(slider_w * self.volume)
        if fill_w > 0:
            # Gradiente ciano → azul
            for i in range(fill_w):
                t = i / max(fill_w, 1)
                r = int(0   + t * 70)
                g = int(200 + t * 55)
                b = int(255)
                pygame.draw.line(tela, (r, g, b),
                                 (sx + i, sy + 2), (sx + i, sy + slider_h - 2))

        # Borda do trilho
        cor_borda = COR_BORDA_SEL if foco else COR_BORDA
        pygame.draw.rect(tela, cor_borda, trilho, 2, border_radius=4)

        # Marcador deslizante
        handle_x = sx + fill_w
        handle_rect = pygame.Rect(handle_x - 6, sy - 4, 12, slider_h + 8)
        pygame.draw.rect(tela, COR_BRANCO if foco else COR_AZUL,
                         handle_rect, border_radius=3)

        # Tracinhos de segmento (10 divisões)
        for i in range(1, 10):
            tx = sx + int(slider_w * i / 10)
            pygame.draw.line(tela, (0, 80, 100), (tx, sy + 6), (tx, sy + slider_h - 6), 1)

        # Valor numérico
        pct = self.font_valor.render(f"{int(self.volume * 100):3d}%", True,
                                     COR_CIANO if foco else COR_AZUL)
        tela.blit(pct, (cx + slider_w // 2 + 15, sy))

        # Setas < >
        if foco:
            self._desenhar_setas(tela, cx, sy + slider_h // 2, slider_w + 60)

    def _desenhar_resolucao(self, tela, cx, y, foco):
        label = self.font_label.render("RESOLUÇÃO", True,
                                       COR_BRANCO if foco else COR_AZUL)
        tela.blit(label, label.get_rect(center=(cx, y)))

        # Botões de resolução
        btn_w = 180
        btn_h = 36
        gap = 12
        total = len(RESOLUCOES)
        total_w = total * btn_w + (total - 1) * gap
        start_x = cx - total_w // 2

        for i, res in enumerate(RESOLUCOES):
            bx = start_x + i * (btn_w + gap)
            by = y + 28
            rect = pygame.Rect(bx, by, btn_w, btn_h)

            selecionado = (i == self.resolucao_idx)
            cor_fundo  = (0, 80, 100)  if selecionado else (10, 25, 35)
            cor_borda  = COR_CIANO_ESCURO if selecionado else (40, 80, 100)
            cor_texto  = COR_BRANCO if selecionado else COR_AZUL

            # Glow pulsante no selecionado
            if selecionado and foco:
                alpha_g = int(60 + math.sin(self.timer * 6) * 30)
                glow_s = pygame.Surface((btn_w + 10, btn_h + 10), pygame.SRCALPHA)
                pygame.draw.rect(glow_s, (*COR_CIANO, alpha_g),
                                 (0, 0, btn_w + 10, btn_h + 10), border_radius=6)
                tela.blit(glow_s, (bx - 5, by - 5))

            pygame.draw.rect(tela, cor_fundo, rect, border_radius=4)
            pygame.draw.rect(tela, cor_borda, rect, 2, border_radius=4)

            label_res = RESOLUCAO_LABELS[res].split()[0]  # só "1280x720"
            txt = self.font_valor.render(label_res, True, cor_texto)
            tela.blit(txt, txt.get_rect(center=rect.center))

        if foco:
            self._desenhar_setas(tela, cx, y + 28 + btn_h // 2, total_w + 60)

    def _desenhar_fullscreen(self, tela, cx, y, foco):
        label = self.font_label.render("TELA CHEIA", True,
                                       COR_BRANCO if foco else COR_AZUL)
        tela.blit(label, label.get_rect(center=(cx, y)))

        # Indicador ON/OFF estilo LED
        led_w, led_h = 110, 36
        led_rect = pygame.Rect(cx - led_w // 2, y + 28, led_w, led_h)

        if self.fullscreen:
            cor_fundo = (0, 100, 80)
            cor_borda = (0, 255, 180)
            texto_led = "ON"
            cor_txt   = (0, 255, 180)
        else:
            cor_fundo = (60, 20, 20)
            cor_borda = (150, 50, 50)
            texto_led = "OFF"
            cor_txt   = (180, 60, 60)

        if foco:
            alpha_g = int(50 + math.sin(self.timer * 6) * 25)
            glow_s = pygame.Surface((led_w + 10, led_h + 10), pygame.SRCALPHA)
            pygame.draw.rect(glow_s, (*cor_borda, alpha_g),
                             (0, 0, led_w + 10, led_h + 10), border_radius=8)
            tela.blit(glow_s, (led_rect.x - 5, led_rect.y - 5))

        pygame.draw.rect(tela, cor_fundo, led_rect, border_radius=6)
        pygame.draw.rect(tela, cor_borda, led_rect, 2, border_radius=6)

        txt = self.font_label.render(texto_led, True, cor_txt)
        tela.blit(txt, txt.get_rect(center=led_rect.center))

        if foco:
            dica = self.font_dica.render("ENTER para alternar", True, COR_CIANO_ESCURO)
            tela.blit(dica, dica.get_rect(center=(cx, y + 28 + led_h + 14)))

    def _desenhar_setas(self, tela, cx, cy, largura_controle):
        """Setas animadas < > flanqueando o controle focado."""
        offset = int(math.sin(self.timer * 8) * 3)
        margem = largura_controle // 2 + 20

        for dx, char in [(-margem - offset, "<"), (margem + offset, ">")]:
            txt = self.font_label.render(char, True, COR_CIANO)
            tela.blit(txt, txt.get_rect(center=(cx + dx, cy)))

    def _desenhar_dica(self, tela, cx):
        dicas = [
            "W/S ou ↑/↓  Navegar",
            "A/D ou ←/→  Ajustar",
            "ENTER  Confirmar / Toggle",
            "ESC  Voltar",
        ]
        gap = 22
        y_base = altura_tela - 80
        for i, d in enumerate(dicas):
            surf = self.font_dica.render(d, True, (60, 120, 140))
            x = cx - (len(dicas) // 2 * 200) + i * 200
            tela.blit(surf, surf.get_rect(center=(x, y_base)))