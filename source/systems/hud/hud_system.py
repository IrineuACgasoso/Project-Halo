import pygame
from os.path import join

from source.windows.settings import largura_tela, altura_tela
from source.systems.entitymanager import entity_manager
from source.feats.assets import ASSETS
from .hud_draw import (
    draw_barra_escudo,
    draw_barra_vida,
    draw_barra_xp,
    draw_boss_hud,
)

# Constantes de layout (canto superior direito)
_ESCUDO_W  = 260
_ESCUDO_H  = 16
_VIDA_W    = 200
_VIDA_H    = 11
_MARGEM_X  = 24
_MARGEM_Y  = 28
_GAP       = 6          # espaço entre barra de escudo e vida

# XP (centro-topo)
_XP_W      = 320
_XP_H      = 10
_XP_Y      = 8


class HUD:
    def __init__(self, game):
        self.game = game

        # Fontes
        self._font_hud   = pygame.font.SysFont("Consolas", 13, bold=True)
        self._font_timer = pygame.font.SysFont("Arial",    34, bold=True)
        self._font_boss  = self._carregar_fonte(
            join('assets', 'fonts', 'cinzel', 'Cinzel-Regular.otf'), 22
        )
        self._font_xp    = pygame.font.SysFont("Consolas", 11)

        # Ícones de coletáveis (escalonados)
        _SZ = 26
        self._icones = {
            'life_orb' : pygame.transform.scale(ASSETS['items']['life_orb'],  (_SZ, _SZ)),
            'exp_shard': pygame.transform.scale(ASSETS['items']['exp_shard'], (_SZ, _SZ)),
            'big_shard': pygame.transform.scale(ASSETS['items']['big_shard'], (_SZ, _SZ)),
            'cafe'     : pygame.transform.scale(ASSETS['items']['cafe'],      (_SZ, _SZ)),
        }

        # Cache do boss
        self._ultimo_check_boss   = 0
        self._intervalo_check_boss = 500

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _carregar_fonte(path, size):
        try:
            import os
            if os.path.exists(path):
                return pygame.font.Font(path, size)
        except Exception:
            pass
        return pygame.font.SysFont("Georgia", size, bold=True)

    def _atualizar_boss_foco(self):
        agora = pygame.time.get_ticks()
        if agora - self._ultimo_check_boss < self._intervalo_check_boss:
            return
        self._ultimo_check_boss = agora
        bosses = [s for s in entity_manager.inimigos_grupo if hasattr(s, 'titulo')]
        if bosses:
            self.game.boss_atual = min(
                bosses, key=lambda b: b.posicao.distance_to(self.game.player.posicao)
            )
        else:
            self.game.boss_atual = None

    # ── Desenhos individuais ─────────────────────────────────────────────────

    def _draw_player_bars(self, tela):
        p = self.game.player
        rx = largura_tela - _MARGEM_X - _ESCUDO_W
        ry = _MARGEM_Y

        pct_escudo = max(0.0, min(1.0, p.escudo_atual / p.escudo_maximo)) if getattr(p, 'escudo_maximo', 0) > 0 else 0.0
        pct_vida   = max(0.0, min(1.0, p.vida_atual / p.vida_maxima))

        draw_barra_escudo(tela, pygame.Rect(rx, ry, _ESCUDO_W, _ESCUDO_H), pct_escudo)

        # Barra de vida alinhada à direita, abaixo do escudo
        vx = largura_tela - _MARGEM_X - _VIDA_W
        vy = ry + _ESCUDO_H + _GAP
        draw_barra_vida(tela, pygame.Rect(vx, vy, _VIDA_W, _VIDA_H), pct_vida)

    def _draw_xp(self, tela):
        p  = self.game.player
        cx = (largura_tela - _XP_W) // 2
        pct = max(0.0, min(1.0, p.experiencia_atual / p.experiencia_level_up))
        draw_barra_xp(
            tela,
            pygame.Rect(cx, _XP_Y, _XP_W, _XP_H),
            pct,
            p.contador_niveis,
            p.experiencia_atual,
            p.experiencia_level_up,
            fonte=self._font_xp,
        )

    def _draw_timer(self, tela):
        if self.game.boss_atual:
            return
        t  = self.game.timer_jogo
        txt = f"{int(t // 60):02d}:{int(t % 60):02d}"
        surf = self._font_timer.render(txt, True, (255, 255, 255))
        tela.blit(surf, surf.get_rect(center=(largura_tela // 2, 44)))

    def _draw_coletaveis(self, tela):
        col  = self.game.player.coletaveis
        itens = [
            ('life_orb',  col['life_orb']),
            ('exp_shard', col['exp_shard']),
            ('big_shard', col['big_shard']),
            ('cafe',      col['cafe']),
        ]
        y = 28
        for tipo, qtd in itens:
            tela.blit(self._icones[tipo], (18, y))
            surf = self._font_hud.render(str(qtd), True, (230, 230, 230))
            tela.blit(surf, (48, y + 6))
            y += 34

    # ── Público ──────────────────────────────────────────────────────────────

    def draw(self, tela):
        self._draw_player_bars(tela)
        self._draw_xp(tela)
        self._draw_timer(tela)
        self._draw_coletaveis(tela)

        self._atualizar_boss_foco()
        draw_boss_hud(tela, self.game.boss_atual, self._font_boss, self._font_hud, largura_tela, altura_tela)