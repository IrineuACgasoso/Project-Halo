import pygame
import math

from source.windows.settings import largura_tela, altura_tela


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


def _chanfrado(rect, corte=8):
    """Retorna polígono com cantos cortados (estilo Halo)."""
    x, y, w, h = rect.x, rect.y, rect.width, rect.height
    c = corte
    return [
        (x + c, y),
        (x + w - c, y),
        (x + w, y + c),
        (x + w, y + h - c),
        (x + w - c, y + h),
        (x + c, y + h),
        (x, y + h - c),
        (x, y + c),
    ]


def draw_barra_escudo(surface, rect, pct, cor=(80, 160, 255), cor_borda=(180, 220, 255), brilho=True):
    """Barra de escudo azul estilo Halo com cortes nos cantos."""
    corte = 7
    # Fundo escuro
    fundo_poly = _chanfrado(rect, corte)
    pygame.draw.polygon(surface, (10, 20, 40, 180), fundo_poly)

    # Preenchimento
    if pct > 0:
        fill_rect = pygame.Rect(rect.x, rect.y, max(0, int(rect.width * pct)), rect.height)
        # Clip para não vazar
        fill_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        fill_poly_local = _chanfrado(pygame.Rect(0, 0, max(1, int(rect.width * pct)), rect.height), corte)
        pygame.draw.polygon(fill_surf, (*cor, 220), fill_poly_local)

        # Linha de brilho no topo
        if brilho and pct > 0.02:
            bw = max(1, int(rect.width * pct) - corte * 2)
            bx = corte
            pygame.draw.line(fill_surf, (200, 230, 255, 160), (bx, 2), (bx + bw, 2), 2)

        surface.blit(fill_surf, rect.topleft)

    # Borda chanfrada
    pygame.draw.polygon(surface, cor_borda, fundo_poly, 2)

    # Ícone de escudo à esquerda (cruz pequena — símbolo médico/escudo Halo)
    ix = rect.x - 18
    iy = rect.centery
    pygame.draw.rect(surface, cor_borda, (ix - 1, iy - 5, 3, 11))
    pygame.draw.rect(surface, cor_borda, (ix - 5, iy - 1, 11, 3))


def draw_barra_vida(surface, rect, pct, cor=(200, 40, 40), cor_borda=(255, 140, 140)):
    """Barra de vida vermelha fina, estilo Halo."""
    corte = 5
    fundo_poly = _chanfrado(rect, corte)
    pygame.draw.polygon(surface, (30, 5, 5, 180), fundo_poly)

    if pct > 0:
        fill_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        fill_w = max(1, int(rect.width * pct))
        fill_poly_local = _chanfrado(pygame.Rect(0, 0, fill_w, rect.height), corte)
        pygame.draw.polygon(fill_surf, (*cor, 230), fill_poly_local)
        surface.blit(fill_surf, rect.topleft)

    pygame.draw.polygon(surface, cor_borda, fundo_poly, 1)


def draw_barra_xp(surface, rect, pct, nivel, xp_atual, xp_max,
                  cor=(0, 200, 255), fonte=None):
    """Barra de XP estilo Halo: fina, central, com valores e nível."""
    corte = 4
    # Fundo
    fundo_poly = _chanfrado(rect, corte)
    pygame.draw.polygon(surface, (5, 15, 30, 200), fundo_poly)

    # Fill
    if pct > 0:
        fill_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        fw = max(1, int(rect.width * pct))
        fp = _chanfrado(pygame.Rect(0, 0, fw, rect.height), corte)
        pygame.draw.polygon(fill_surf, (*cor, 200), fp)
        # Reflexo
        pygame.draw.line(fill_surf, (180, 240, 255, 120), (corte, 1), (fw - corte, 1), 1)
        surface.blit(fill_surf, rect.topleft)

    pygame.draw.polygon(surface, (100, 200, 255, 180), fundo_poly, 1)

    if fonte:
        # Nível à esquerda
        txt_nivel = fonte.render(f"LVL {nivel}", True, (180, 230, 255))
        surface.blit(txt_nivel, (rect.x - txt_nivel.get_width() - 8, rect.centery - txt_nivel.get_height() // 2))
        # XP à direita
        txt_xp = fonte.render(f"{int(xp_atual)}/{int(xp_max)}", True, (120, 190, 220))
        surface.blit(txt_xp, (rect.right + 6, rect.centery - txt_xp.get_height() // 2))


def draw_boss_hud(surface, boss, font_titulo, font_barra, largura_tela, altura_tela):
    """Barra de boss Halo: moldura dourada com chanfros, nome estilizado."""
    if not boss or not hasattr(boss, 'vida'):
        return
    if getattr(boss, 'is_animating_respawn', False):
        return

    BAR_W = int(largura_tela * 0.55)
    BAR_H = 14
    x = (largura_tela - BAR_W) // 2
    y = altura_tela - 72
    corte = 6

    pct = max(0.0, min(1.0, boss.vida / boss.vida_maxima))
    cor_vida = (160, 0, 0) if not getattr(boss, 'is_final_form', False) else (110, 0, 160)

    # --- Nome ---
    sombra = font_titulo.render(boss.titulo, True, (0, 0, 0))
    nome   = font_titulo.render(boss.titulo, True, (215, 180, 60))
    nr = nome.get_rect(centerx=largura_tela // 2, bottom=y - 4)
    surface.blit(sombra, nr.move(2, 2))
    surface.blit(nome, nr)

    # --- Barra de vida ---
    bar_rect = pygame.Rect(x, y, BAR_W, BAR_H)
    poly_bg = _chanfrado(bar_rect, corte)
    pygame.draw.polygon(surface, (15, 5, 5), poly_bg)

    if pct > 0:
        fill_surf = pygame.Surface((BAR_W, BAR_H), pygame.SRCALPHA)
        fw = max(1, int(BAR_W * pct))
        fp = _chanfrado(pygame.Rect(0, 0, fw, BAR_H), corte)
        pygame.draw.polygon(fill_surf, (*cor_vida, 240), fp)
        surface.blit(fill_surf, bar_rect.topleft)

    # Escudo sobreposto
    if hasattr(boss, 'escudo_atual') and boss.escudo_atual > 0 and boss.escudo_maximo > 0:
        pct_e = max(0.0, min(1.0, boss.escudo_atual / boss.escudo_maximo))
        shield_surf = pygame.Surface((BAR_W, BAR_H), pygame.SRCALPHA)
        sw = max(1, int(BAR_W * pct_e))
        sp = _chanfrado(pygame.Rect(0, 0, sw, BAR_H), corte)
        pygame.draw.polygon(shield_surf, (60, 130, 255, 200), sp)
        surface.blit(shield_surf, bar_rect.topleft)

    # Moldura dourada
    pygame.draw.polygon(surface, (215, 175, 60), poly_bg, 2)

    # Ornamentos nos cantos
    _draw_corner_ornaments(surface, bar_rect, (255, 225, 100), corte)


def _draw_corner_ornaments(surface, rect, cor, corte):
    """Pequenos losangos/diamantes nos 4 cantos da barra."""
    size = 5
    pontos = [
        (rect.x, rect.centery),                 # esquerda
        (rect.right, rect.centery),              # direita
    ]
    for cx, cy in pontos:
        pts = [(cx, cy - size), (cx + size, cy), (cx, cy + size), (cx - size, cy)]
        pygame.draw.polygon(surface, cor, pts)
        pygame.draw.polygon(surface, (255, 255, 200), pts, 1)


# ── Desenhos individuais ─────────────────────────────────────────────────

def _draw_player_bars(tela, player):
    p = player
    rx = largura_tela - _MARGEM_X - _ESCUDO_W
    ry = _MARGEM_Y

    pct_escudo = max(0.0, min(1.0, p.escudo_atual / p.escudo_maximo)) if getattr(p, 'escudo_maximo', 0) > 0 else 0.0
    pct_vida   = max(0.0, min(1.0, p.vida_atual / p.vida_maxima))

    draw_barra_escudo(tela, pygame.Rect(rx, ry, _ESCUDO_W, _ESCUDO_H), pct_escudo)

    # Barra de vida alinhada à direita, abaixo do escudo
    vx = largura_tela - _MARGEM_X - _VIDA_W
    vy = ry + _ESCUDO_H + _GAP
    draw_barra_vida(tela, pygame.Rect(vx, vy, _VIDA_W, _VIDA_H), pct_vida)

def _draw_xp(tela, player, font_xp):
    p  = player
    cx = (largura_tela - _XP_W) // 2
    pct = max(0.0, min(1.0, p.experiencia_atual / p.experiencia_level_up))
    draw_barra_xp(
        tela,
        pygame.Rect(cx, _XP_Y, _XP_W, _XP_H),
        pct,
        p.contador_niveis,
        p.experiencia_atual,
        p.experiencia_level_up,
        fonte = font_xp,
    )

def _draw_timer(tela, timer_jogo, font_timer):
    t  = timer_jogo
    txt = f"{int(t // 60):02d}:{int(t % 60):02d}"
    surf = font_timer.render(txt, True, (255, 255, 255))
    tela.blit(surf, surf.get_rect(center=(largura_tela // 2, 44)))

def _draw_coletaveis(tela, coletaveis_player, icones, font_hud):
    col  = coletaveis_player
    itens = [
        ('life_orb',  col['life_orb']),
        ('exp_shard', col['exp_shard']),
        ('big_shard', col['big_shard']),
        ('cafe',      col['cafe']),
    ]
    y = 28
    for tipo, qtd in itens:
        tela.blit(icones[tipo], (18, y))
        surf = font_hud.render(str(qtd), True, (230, 230, 230))
        tela.blit(surf, (48, y + 6))
        y += 34