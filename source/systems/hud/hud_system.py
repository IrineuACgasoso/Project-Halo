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
    _draw_player_bars,
    _draw_corner_ornaments,
    _draw_coletaveis,
    _draw_timer,
    _draw_xp
)


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

        # Cache do boss e alvos
        self._ultimo_check_boss   = 0
        self._intervalo_check_boss = 500
        
        self.foco_barra_vida = None  # Controla estritamente o que aparece na tela

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
        
        # A HUD foca apenas em quem tem título para desenhar a barra de vida inferior
        todos_com_titulo = [s for s in entity_manager.inimigos_grupo if hasattr(s, 'titulo')]
        if todos_com_titulo:
            self.foco_barra_vida = min(
                todos_com_titulo, key=lambda b: b.posicao.distance_squared_to(self.game.player.posicao)
            )
        else:
            self.foco_barra_vida = None

    

    # ── Público ──────────────────────────────────────────────────────────────

    def draw(self, tela):
        _draw_player_bars(tela, self.game.player)
        _draw_xp(tela, self.game.player, self._font_xp)

        # O timer do jogo só some se houver um chefe real na arena
        if not self.game.boss_atual:
            _draw_timer(tela, self.game.timer_jogo, self._font_timer)

        _draw_coletaveis(tela, self.game.player.coletaveis, self._icones, self._font_hud)

        self._atualizar_boss_foco()
        
        # Passamos o 'foco_barra_vida' em vez de 'boss_atual'. 
        draw_boss_hud(tela, self.foco_barra_vida, self._font_boss, self._font_hud, largura_tela, altura_tela)

        # Varre os sprites para desenhar elementos extras na interface (como o timer do Halo)
        for sprite in entity_manager.all_sprites:
            if hasattr(sprite, 'hud_draw'):
                sprite.hud_draw(tela)