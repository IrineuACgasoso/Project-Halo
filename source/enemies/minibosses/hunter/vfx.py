"""Efeitos visuais do Hunter: brilho vermelho de vulnerável e poeira.

- Brilho: uma silhueta vermelha por frame de sprite (criada 1× e guardada em cache), desenhada por
  cima dele no `draw_extras` com alpha pulsando. Por frame, só `set_alpha` e um blit: zero alocação.
- Poeira: padrões sobre `particulas.emitir` (imagens em cache, teto global de partículas). As funções
  de módulo recebem o aviso da habilidade (gancho `ao_explodir`), não o Hunter: a poeira sai mesmo
  se ele já tiver morrido quando o morteiro cai.
"""
import math
import random
import weakref

import pygame

from source.feats import particulas
from source.systems.gameclock import relogio
from source.utils.superficies import mascara_de

from .config import CFG

V2 = pygame.math.Vector2

_SILHUETAS = weakref.WeakKeyDictionary()   # frame do sprite -> silhueta vermelha do mesmo tamanho

CORES_POEIRA = ((120, 100, 70), (95, 80, 55), (140, 120, 90), (80, 70, 50))
TAMANHOS_POEIRA = (4, 6, 8)


def silhueta(frame):
    """Silhueta vermelha (cor `CFG.brilho_cor`) do `frame`, em cache."""
    sil = _SILHUETAS.get(frame)
    if sil is None:
        sil = mascara_de(frame).to_surface(setcolor=(*CFG.brilho_cor, 255), unsetcolor=(0, 0, 0, 0))
        _SILHUETAS[frame] = sil
    return sil


def alpha_do_brilho(agora):
    """Alpha do brilho em `agora` (ms): pulsa entre os limites de `CFG.brilho_alpha`."""
    minimo, maximo = CFG.brilho_alpha
    onda = 0.5 + 0.5 * math.sin(agora * 2 * math.pi / CFG.brilho_periodo_ms)
    return round(minimo + (maximo - minimo) * onda)


# ── Poeira ───────────────────────────────────────────────────────────────────
def poeira(posicao, direcao, quantidade, abertura_graus=360, velocidade=(60, 160), duracao_ms=(450, 750)):
    """`quantidade` grãos saindo de `posicao` em direções sorteadas no leque de `abertura_graus`
    em volta de `direcao` (com 360, para todos os lados)."""
    base = V2(direcao) if V2(direcao).length_squared() > 0 else V2(1, 0)
    base.normalize_ip()
    meia = abertura_graus / 2
    for _ in range(quantidade):
        # Sorteia tudo antes de consultar o teto (a sequência do random não depende do descarte)
        cor = random.choice(CORES_POEIRA)
        tamanho = random.choice(TAMANHOS_POEIRA)
        vel = base.rotate(random.uniform(-meia, meia)) * random.uniform(*velocidade)
        duracao = random.uniform(*duracao_ms)
        particulas.emitir(posicao, particulas.imagem_pixel(cor, tamanho, 'circulo'), vel, duracao)


def poeira_na_area_do_cone(origem, direcao, raio, abertura_graus, quantidade):
    """Grãos nascendo espalhados dentro do cone (a área atingida) e indo para fora dele."""
    base = V2(direcao) if V2(direcao).length_squared() > 0 else V2(1, 0)
    base.normalize_ip()
    meia = abertura_graus / 2
    for _ in range(quantidade):
        cor = random.choice(CORES_POEIRA)
        tamanho = random.choice(TAMANHOS_POEIRA)
        sentido = base.rotate(random.uniform(-meia, meia))
        ponto = V2(origem) + sentido * (raio * math.sqrt(random.random()))   # sqrt: densidade uniforme
        vel = sentido * random.uniform(30, 110)
        duracao = random.uniform(500, 850)
        particulas.emitir(ponto, particulas.imagem_pixel(cor, tamanho, 'circulo'), vel, duracao)


def poeira_da_explosao(aviso):
    """Gancho `ao_explodir` do morteiro: anel de poeira na borda da explosão."""
    poeira(aviso.posicao, V2(1, 0), CFG.poeira_explosao, 360, velocidade=(80, 200))


def poeira_do_slam(cone):
    """Gancho `ao_explodir` do shield slam: poeira em toda a área do cone."""
    poeira_na_area_do_cone(cone.posicao, cone.direcao, cone.cfg.raio, cone.cfg.angulo_spray, CFG.poeira_slam)


class HunterVFX:
    def iniciar_vfx(self):
        self.proxima_poeira_dash = 0
        for frames in self.sprites.values():          # silhuetas prontas no spawn, não no 1º brilho
            for frame in frames:
                silhueta(frame)

    def draw_extras(self, tela, deslocamento):
        """Chamado pelo renderer depois dos sprites: o brilho vermelho enquanto vulnerável."""
        if not self.vulneravel:
            return
        sil = silhueta(self.sprites[self.estado_animacao][self.frame_atual])
        sil.set_alpha(alpha_do_brilho(relogio.agora()))
        tela.blit(sil, (self.rect.x - deslocamento.x, self.rect.y - deslocamento.y))

    def poeira_do_dash(self, agora, direcao):
        """Alguns grãos para os dois lados dos pés, a cada `poeira_dash_intervalo_ms`."""
        if agora < self.proxima_poeira_dash:
            return
        self.proxima_poeira_dash = agora + CFG.poeira_dash_intervalo_ms
        pes = V2(self.posicao.x, self.rect.bottom - 12)
        lateral = V2(-direcao.y, direcao.x)
        for lado in (lateral, -lateral):
            poeira(pes, lado - direcao * 0.3, CFG.poeira_dash_por_lado, 50, velocidade=(70, 150))
