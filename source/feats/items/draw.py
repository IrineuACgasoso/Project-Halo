"""
items/draw.py

Tudo que é DESENHO dos coletáveis mora aqui: geração das sprites (uma vez,
cacheada — mesmo espírito do ProjetilUniversal), o halo neon externo, e a
partícula de coleta. A classe Items (em items.py) só chama essas funções;
não sabe desenhar nada sozinha.
"""

import math
import random

import pygame

# ------------------------------------------------------------------------ #
# CONFIG
# ------------------------------------------------------------------------ #

GLOBAL_CACHE = {}

TIPOS_XP = {'exp_shard', 'big_shard'}

TAMANHOS = {
    'exp_shard': (16, 16),
    'big_shard': (24, 24),
    'life_orb':  (14, 24),
    'upgrade':      (14, 24),
}

# Espaço extra ao redor do corpo pra caber o halo sem cortar nas bordas.
# Halo bem mais forte agora = precisa de bem mais espaço.
PADDING_GLOW = 18

# Cores do halo por categoria
COR_GLOW_XP    = (60, 190, 255)   # azul neon — dados/holograma
COR_GLOW_SAUDE = (255, 30, 50)    # vermelho neon — vida/suporte médico
COR_GLOW_UPG   = (40, 255, 60)


# ------------------------------------------------------------------------ #
# CACHE / DISPATCH
# ------------------------------------------------------------------------ #

def obter_imagem(tipo, tamanho_corpo, id_arma=None):
    """Retorna (e cacheia) o dict {'base':.., 'glow':..} pra esse tipo+tamanho,
    junto com a chave de cache usada. Para 'upgrade', o `id_arma` entra na
    própria chave de cache — cada arma tem seu ícone próprio cacheado
    separadamente, já que a sprite muda dependendo de qual arma o item vai upar."""
    sufixo_arma = f"_{id_arma}" if id_arma else ""
    chave = f"{tipo}_{tamanho_corpo[0]}x{tamanho_corpo[1]}{sufixo_arma}"
    if chave not in GLOBAL_CACHE:
        GLOBAL_CACHE[chave] = _desenhar_sprite(tipo, tamanho_corpo, id_arma)
    return GLOBAL_CACHE[chave], chave


def _desenhar_sprite(tipo, tamanho_corpo, id_arma=None):
    pad = PADDING_GLOW
    canvas_tamanho = (tamanho_corpo[0] + pad * 2, tamanho_corpo[1] + pad * 2)

    if tipo in ('exp_shard', 'big_shard'):
        return _desenhar_chip(tamanho_corpo, canvas_tamanho, grande=(tipo == 'big_shard'))
    elif tipo == 'life_orb':
        return _desenhar_bandagem(tamanho_corpo, canvas_tamanho)
    elif tipo == 'upgrade':
        return _desenhar_upgrade(tamanho_corpo, canvas_tamanho, id_arma)
    else:
        return _desenhar_fallback(tipo, canvas_tamanho)


def _desenhar_fallback(tipo, canvas_tamanho):
    """Tipo desconhecido: tenta o asset antigo; se não existir, placeholder
    magenta pra ficar óbvio no teste em vez de crashar."""
    from source.feats.assets import ASSETS
    img = ASSETS.get('items', {}).get(tipo)
    base = pygame.Surface(canvas_tamanho, pygame.SRCALPHA)
    if img:
        escalado = pygame.transform.scale(img, (canvas_tamanho[0] - 4, canvas_tamanho[1] - 4))
        base.blit(escalado, (2, 2))
    else:
        base.fill((255, 0, 255))
    glow = pygame.Surface(canvas_tamanho, pygame.SRCALPHA)
    return {'base': base, 'glow': glow}


# ------------------------------------------------------------------------ #
# HALO NEON
# ------------------------------------------------------------------------ #

def _desenhar_halo_externo(canvas_tamanho, rect_corpo, cor, camadas=7, raio_extra=15):
    """Halo neon contornando `rect_corpo`. Bem mais forte que um glow comum:
    muitas camadas com alpha alto (compostas depois com blend aditivo), mais
    um núcleo quase branco colado na silhueta pra dar aquele 'estouro' de
    luz de perto, como letreiro de neon.
    """
    glow = pygame.Surface(canvas_tamanho, pygame.SRCALPHA)

    for i in range(camadas, 0, -1):
        expansao = int((raio_extra / camadas) * i)
        alpha = int(150 * (1 - (i - 1) / camadas)) + 45
        halo_rect = rect_corpo.inflate(expansao * 2, expansao * 2)
        raio_borda = max(3, (rect_corpo.height // 2) + expansao // 2)
        largura_traco = 3 if i > camadas // 2 else 4
        pygame.draw.rect(
            glow, (*cor, alpha), halo_rect,
            width=largura_traco, border_radius=raio_borda
        )

    # Núcleo "quente": quase branco, bem colado no corpo — o brilho mais
    # intenso do letreiro de neon fica sempre perto da fonte.
    cor_nucleo = tuple(min(255, c + 140) for c in cor)
    pygame.draw.rect(
        glow, (*cor_nucleo, 235), rect_corpo.inflate(3, 3),
        width=3, border_radius=max(3, rect_corpo.height // 2)
    )

    return glow


def _compor_frame(entrada_cache, alpha_glow=255):
    """Monta o frame final: corpo opaco + halo em cima usando blend aditivo
    (BLEND_RGBA_ADD) — o que dá a sensação de luz "estourando" de verdade
    (neon), em vez de só uma sombra translúcida por baixo."""
    frame = entrada_cache['base'].copy()

    glow = entrada_cache['glow']
    if alpha_glow < 255:
        glow = glow.copy()
        glow.set_alpha(alpha_glow)

    frame.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return frame


def atualizar_frame_pulsando(chave_cache, fase, agora):
    """Recalcula o frame do item com o halo pulsando (seno). Chamado a cada
    frame pelo Items. Alpha nunca cai demais — o neon fica sempre aceso,
    só varia a intensidade do brilho."""
    entrada = GLOBAL_CACHE.get(chave_cache)
    if entrada is None:
        return None

    alpha = 190 + math.sin(agora / 240 + fase) * 65  # oscila ~125–255
    alpha = max(0, min(255, int(alpha)))

    return _compor_frame(entrada, alpha_glow=alpha)


def frame_inicial(entrada_cache):
    return _compor_frame(entrada_cache, alpha_glow=255)


# ------------------------------------------------------------------------ #
# SPRITES
# ------------------------------------------------------------------------ #

def _desenhar_chip(tamanho_corpo, canvas_tamanho, grande):
    """UNSC AI Chip: placa cinza-metálica com ranhura de dados interna e
    halo azul neon contornando toda a peça."""
    w, h = tamanho_corpo
    pad = PADDING_GLOW
    base = pygame.Surface(canvas_tamanho, pygame.SRCALPHA)

    rect_corpo = pygame.Rect(pad, pad, w, h)

    cor_corpo = (96, 100, 106) if not grande else (108, 112, 120)
    pygame.draw.rect(base, cor_corpo, rect_corpo, border_radius=3)
    pygame.draw.rect(base, (35, 37, 41), rect_corpo, 1, border_radius=3)

    # Pinos de contato laterais (silhueta de matriz de dados)
    cor_pino = (55, 58, 63)
    for i in range(3):
        y = rect_corpo.y + 2 + i * max(1, (h - 4) // 2)
        pygame.draw.line(base, cor_pino, (rect_corpo.x - 2, y), (rect_corpo.x, y))
        pygame.draw.line(base, cor_pino, (rect_corpo.right, y), (rect_corpo.right + 2, y))

    # Ranhura de dados interna
    cor_ranhura = COR_GLOW_XP if not grande else (180, 120, 255)
    ranhura = pygame.Rect(
        rect_corpo.x + int(w * 0.25), rect_corpo.y + int(h * 0.42),
        max(2, int(w * 0.5)), max(2, int(h * 0.18))
    )
    pygame.draw.rect(base, cor_ranhura, ranhura, border_radius=2)

    glow = _desenhar_halo_externo(
        canvas_tamanho, rect_corpo, cor_ranhura,
        camadas=7, raio_extra=17 if grande else 15
    )

    return {'base': base, 'glow': glow}


def _desenhar_bandagem(tamanho_corpo, canvas_tamanho):
    """Item de vida redesenhado: tubo BRANCO estilo bandagem/curativo, com
    uma cruz vermelha grande e bem definida no centro — alto contraste, feito
    de propósito pra chamar atenção. 'upgrade' ganha um pingo dourado no topo
    pra diferenciar do life_orb comum sem perder a leitura."""
    w, h = tamanho_corpo
    pad = PADDING_GLOW
    base = pygame.Surface(canvas_tamanho, pygame.SRCALPHA)

    corpo_rect = pygame.Rect(pad + int(w * 0.12), pad, int(w * 0.76), h)

    # Tubo branco (levemente off-white pra não estourar puro na tela)
    cor_corpo = (240, 238, 232)
    pygame.draw.rect(base, cor_corpo, corpo_rect, border_radius=5)
    pygame.draw.rect(base, (180, 178, 172), corpo_rect, 1, border_radius=5)

    # Faixas de "enrolamento" da bandagem (sutis, só textura)
    cor_faixa = (215, 212, 205)
    for y in range(corpo_rect.y + 4, corpo_rect.bottom - 3, 5):
        pygame.draw.line(base, cor_faixa, (corpo_rect.x + 1, y), (corpo_rect.right - 1, y), 1)

    # Cruz vermelha grande e sólida, bem no centro — o elemento que precisa
    # "gritar" à distância.
    cx, cy = corpo_rect.center
    braco_v = pygame.Rect(0, 0, max(3, int(corpo_rect.width * 0.32)), max(6, int(h * 0.6)))
    braco_v.center = (cx, cy)
    braco_h = pygame.Rect(0, 0, max(6, int(corpo_rect.width * 0.85)), max(3, int(h * 0.22)))
    braco_h.center = (cx, cy)

    cor_cruz = (225, 25, 35)
    cor_cruz_borda = (140, 10, 20)
    for r in (braco_v, braco_h):
        pygame.draw.rect(base, cor_cruz, r, border_radius=1)
        pygame.draw.rect(base, cor_cruz_borda, r, 1, border_radius=1)

    glow = _desenhar_halo_externo(
        canvas_tamanho, corpo_rect, COR_GLOW_SAUDE,
        camadas=7, raio_extra=15
    )

    return {'base': base, 'glow': glow}


def _desenhar_upgrade(tamanho_corpo, canvas_tamanho, id_arma=None):
    """Item de upgrade forçado de UMA arma específica. Busca o ícone dessa
    arma em ASSETS['icons'][id_arma] — o mesmo usado no slot equipado.
    Só cai no desenho vetorial (seta verde) quando não existir ícone
    cadastrado pra essa arma (ou quando não sabemos qual arma é ainda)."""
    from source.feats.assets import ASSETS

    w, h = tamanho_corpo
    pad = PADDING_GLOW
    base = pygame.Surface(canvas_tamanho, pygame.SRCALPHA)
    corpo_rect = pygame.Rect(pad + int(w * 0.12), pad, int(w * 0.76), h)

    sprite_real = None
    if id_arma is not None:
        candidato = ASSETS.get('icons', {}).get(id_arma)
        if isinstance(candidato, pygame.Surface):
            sprite_real = candidato
        elif candidato is not None:
            # Existe algo na chave, mas não é uma Surface válida — avisa
            # em vez de falhar silenciosamente pro fallback sem pista nenhuma.
            print(f"[AVISO] ASSETS['icons']['{id_arma}'] não é uma Surface válida: {type(candidato)}")

    if sprite_real is not None:
        # Sprite disponível: usa ela mesma, escalada pro tamanho do corpo.
        # ESCALA COM ALPHA: usa smoothscale se a imagem tiver per-pixel alpha
        # (ícones de arma normalmente têm fundo transparente).
        try:
            escalada = pygame.transform.smoothscale(sprite_real, corpo_rect.size)
        except (ValueError, pygame.error):
            # smoothscale exige 32bpp com alpha; se falhar, cai pro scale comum
            escalada = pygame.transform.scale(sprite_real, corpo_rect.size)
        base.blit(escalada, corpo_rect.topleft)
    else:
        # Fallback: o tubo + seta verde desenhados por código
        cor_corpo = (10, 25, 10)
        pygame.draw.rect(base, cor_corpo, corpo_rect, border_radius=6)
        pygame.draw.rect(base, (130, 190, 135), corpo_rect, 1, border_radius=5)

        cor_faixa = (40, 40, 40)
        for y in range(corpo_rect.y + 4, corpo_rect.bottom - 3, 5):
            pygame.draw.line(base, cor_faixa, (corpo_rect.x + 1, y), (corpo_rect.right - 1, y), 1)

        cx, cy = corpo_rect.center
        largura_seta = max(6, int(corpo_rect.width * 0.55))
        altura_seta = max(8, int(h * 0.6))
        largura_haste = max(3, int(largura_seta * 0.4))
        altura_cabeca = int(altura_seta * 0.55)

        topo_y = cy - altura_seta // 2
        base_y = topo_y + altura_seta
        quebra_y = topo_y + altura_cabeca

        pontos_seta = [
            (cx, topo_y),
            (cx + largura_seta // 2, quebra_y),
            (cx + largura_haste // 2, quebra_y),
            (cx + largura_haste // 2, base_y),
            (cx - largura_haste // 2, base_y),
            (cx - largura_haste // 2, quebra_y),
            (cx - largura_seta // 2, quebra_y),
        ]

        cor_seta = (25, 220, 35)
        cor_seta_borda = (210, 255, 230)
        pygame.draw.polygon(base, cor_seta, pontos_seta)
        pygame.draw.polygon(base, cor_seta_borda, pontos_seta, 1)

    glow = _desenhar_halo_externo(
        canvas_tamanho, corpo_rect, COR_GLOW_UPG,
        camadas=7, raio_extra=15
    )

    return {'base': base, 'glow': glow}

# ------------------------------------------------------------------------ #
# PARTÍCULA DE COLETA
# ------------------------------------------------------------------------ #

class ItemParticulaColeta(pygame.sprite.Sprite):
    """Pixel de despawn digital: sobe, perde alpha e some sozinho.
    Disparada quando um item é coletado."""

    def __init__(self, posicao, cor, grupos):
        super().__init__(grupos)

        tamanho = random.randint(2, 4)
        self.image = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
        self.image.fill(cor)
        self.rect = self.image.get_rect(center=posicao)

        self.posicao = pygame.math.Vector2(posicao)
        self.velocidade = pygame.math.Vector2(random.uniform(-25, 25), random.uniform(-95, -55))

        self.duracao_ms = random.randint(300, 450)
        self.spawn_time = pygame.time.get_ticks()

    def update(self, delta_time):
        self.posicao += self.velocidade * delta_time
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        decorrido = pygame.time.get_ticks() - self.spawn_time
        progresso = min(1.0, decorrido / self.duracao_ms)

        try:
            self.image.set_alpha(int(255 * (1 - progresso)))
        except pygame.error:
            self.kill()
            return

        if progresso >= 1.0:
            self.kill()


def emitir_particulas_coleta(posicao, tipo, grupos):
    if not grupos:
        return
    cor = COR_GLOW_XP if tipo in TIPOS_XP else COR_GLOW_SAUDE
    for _ in range(random.randint(3, 4)):
        ItemParticulaColeta(posicao, cor, grupos)