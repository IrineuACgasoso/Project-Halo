"""Motor das partículas: sem alocação por partícula nem por frame (roteiro C3).

A imagem base de cada (cor, tamanho, forma) é criada uma vez; o fade usa variantes da base
com alpha quantizado em `NIVEIS_ALPHA`, também em cache. Todas as partículas vivas ficam em
`entity_manager.particulas_grupo`; passando de `TETO_PARTICULAS`, as novas são descartadas.

Quem emite sorteia os parâmetros ANTES de consultar o teto: o descarte não muda a sequência do
`random` (a simulação continua determinística com ou sem descarte).
"""
import random
import weakref

import pygame

from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio

# Picos medidos na C3 (30 s por boss, 20 s de horda de 150 por fase): Warden 1504, Knight 781,
# Gravemind 30, hordas das fases 0–8 até 12. O teto não corta nenhum deles; limita o pior caso,
# como uma horda que teleporta (o pool da fase 9 passa de 2500).
TETO_PARTICULAS = 2000
NIVEIS_ALPHA = 16

_BASES = {}                                  # (cor, tamanho, forma) -> Surface
_VARIANTES = weakref.WeakKeyDictionary()     # base -> [Surface com set_alpha, por nível]


def imagem_pixel(cor, tamanho, forma='quadrado'):
    """Base em cache: quadrado `tamanho`×`tamanho` preenchido com `cor` ou um círculo
    de raio `tamanho // 2` nele (`forma='circulo'`)."""
    if tamanho <= 0:
        raise ValueError(f'tamanho de partícula inválido: {tamanho}')
    if forma not in ('quadrado', 'circulo'):
        raise ValueError(f'forma de partícula desconhecida: {forma!r}')
    chave = (tuple(cor), tamanho, forma)
    base = _BASES.get(chave)
    if base is None:
        base = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
        if forma == 'circulo':
            pygame.draw.circle(base, cor, (tamanho // 2, tamanho // 2), tamanho // 2)
        else:
            base.fill(cor)
        _BASES[chave] = base
    return base


def variantes_alpha(base):
    """As NIVEIS_ALPHA cópias de `base` com alpha de superfície de 0 a 255, criadas juntas
    na primeira vez que a base é usada."""
    variantes = _VARIANTES.get(base)
    if variantes is None:
        variantes = []
        for nivel in range(NIVEIS_ALPHA):
            variante = base.copy()
            variante.set_alpha(round(nivel * 255 / (NIVEIS_ALPHA - 1)))
            variantes.append(variante)
        _VARIANTES[base] = variantes
    return variantes


def preparar(cores, tamanhos):
    """Cria já as imagens das partículas redondas de `cores` × `tamanhos` (no spawn de um boss, para
    nenhuma nascer no meio da luta)."""
    for cor in cores:
        for tamanho in tamanhos:
            variantes_alpha(imagem_pixel(cor, tamanho, 'circulo'))


def _nivel(alpha):
    return int(max(0.0, min(255.0, alpha)) * (NIVEIS_ALPHA - 1) / 255 + 0.5)


def variante_alpha(base, alpha):
    """`base` com alpha de superfície ~`alpha` (0–255), quantizado em NIVEIS_ALPHA níveis."""
    return variantes_alpha(base)[_nivel(alpha)]


class Particula(pygame.sprite.Sprite):
    """Anda em linha reta (ou cai, com `gravidade` em px/s²) e some com fade linear em `duracao_ms` de jogo."""

    def __init__(self, posicao, imagem, velocidade, duracao_ms, grupos, y_desenho=None, gravidade=0):
        super().__init__(*grupos, entity_manager.particulas_grupo)
        self.y_desenho = y_desenho      # None: ordem de desenho comum (Renderer)
        self._variantes = variantes_alpha(imagem)   # guardadas: o update não consulta o cache
        self.posicao = pygame.math.Vector2(posicao)
        self.velocidade = pygame.math.Vector2(velocidade)
        self.gravidade = gravidade
        self.duracao_ms = duracao_ms
        self.nascimento = relogio.agora()
        self.image = self._variantes[-1]
        self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))

    def update(self, delta_time):
        decorrido = relogio.agora() - self.nascimento
        if decorrido >= self.duracao_ms:
            self.kill()
            return
        self.velocidade.y += self.gravidade * delta_time
        self.posicao += self.velocidade * delta_time
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        self.image = self._variantes[int((1 - decorrido / self.duracao_ms) * (NIVEIS_ALPHA - 1) + 0.5)]


def emitir(posicao, imagem, velocidade, duracao_ms, grupos=None, y_desenho=None, gravidade=0):
    """Cria uma partícula, ou devolve None se o teto global foi atingido. `y_desenho`: a linha usada na
    ordem de desenho (ex.: por cima de um boss que cobre o que está perto dele)."""
    if duracao_ms <= 0:
        raise ValueError(f'duração de partícula inválida: {duracao_ms}')
    if len(entity_manager.particulas_grupo) >= TETO_PARTICULAS:
        return None
    if grupos is None:
        grupos = (entity_manager.all_sprites,)
    elif isinstance(grupos, pygame.sprite.AbstractGroup):
        grupos = (grupos,)
    return Particula(posicao, imagem, velocidade, duracao_ms, grupos, y_desenho, gravidade)


def emitir_leque(posicao, direcao, quantidade, cores, tamanhos, abertura_graus=360, velocidade=(60, 160),
                 duracao_ms=(450, 750), y_desenho=None, gravidade=0, sorteio=random):
    """`quantidade` partículas redondas saindo de `posicao` em direções sorteadas no leque de
    `abertura_graus` em volta de `direcao` (com 360, para todos os lados). `sorteio`: um `random.Random`
    próprio, para o efeito não mexer na sequência da simulação."""
    base = pygame.math.Vector2(direcao)
    if base.length_squared() == 0:
        base.update(1, 0)
    base.normalize_ip()
    meia = abertura_graus / 2
    for _ in range(quantidade):
        # Sorteia tudo antes de consultar o teto (a sequência do random não depende do descarte)
        cor = sorteio.choice(cores)
        tamanho = sorteio.choice(tamanhos)
        vel = base.rotate(sorteio.uniform(-meia, meia)) * sorteio.uniform(*velocidade)
        duracao = sorteio.uniform(*duracao_ms)
        emitir(posicao, imagem_pixel(cor, tamanho, 'circulo'), vel, duracao, y_desenho=y_desenho, gravidade=gravidade)
