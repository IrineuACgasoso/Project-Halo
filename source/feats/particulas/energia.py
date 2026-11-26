"""Energia que vaza do chão: durante o aviso de um golpe, fios de energia sobem de pontos sorteados
na área (cada vez mais) e uma fissura brilhante se abre; no fim, a energia é liberada de uma vez
(coluna de partículas subindo e um clarão na área).

Serve para qualquer golpe de área: `energia_no_retangulo` (o RectStrike) e `energia_no_circulo`
(artilharia, pontos do Purge Grid). Só visual: sorteio próprio, desenho numa camada reaproveitada
(`camada_alpha`), partículas no teto global. A fissura é sorteada uma vez, no nascimento."""
import math
import random

import pygame

from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.utils.superficies import SUPERFICIE_VAZIA, camada_alpha

from .motor import emitir, imagem_pixel, preparar

V2 = pygame.math.Vector2
SORTEIO = random.Random()

# (cores das partículas, cor da fissura, cor do miolo, cor do clarão)
PALETAS = {
    'gravidade': (((70, 140, 255), (120, 190, 255), (200, 230, 255), (140, 110, 255)),
                  (80, 150, 255), (225, 240, 255), (150, 200, 255)),
    'vortice':   (((150, 70, 255), (190, 120, 255), (230, 200, 255), (110, 40, 200)),
                  (160, 90, 255), (240, 225, 255), (200, 160, 255)),
    'furia':     (((255, 70, 40), (255, 140, 60), (255, 220, 150), (200, 30, 30)),
                  (255, 90, 40), (255, 235, 200), (255, 150, 90)),
}
TAMANHOS = (4, 6, 8)
PARTICULAS_POR_PX2 = 1 / 1000      # fios por segundo, por px² de área, no começo do aviso...
CRESCIMENTO = 3.0                  # ...e tantas vezes mais no fim
MAX_POR_SEGUNDO = 340
LIBERACAO_POR_PX2 = 1 / 650        # partículas da liberação
LIBERACAO_LIMITES = (12, 90)
CLARAO_MS = 260
PASSO_FISSURA = 38                 # px entre os pontos da fissura


def preparar_energia(paleta='gravidade'):
    """Pinta já as partículas da `paleta` (no spawn de quem usa o efeito)."""
    preparar(PALETAS[paleta][0], TAMANHOS)


class _Retangulo:
    def __init__(self, origem, direcao, comprimento, largura):
        self.origem = V2(origem)
        eixo = V2(direcao)
        self.eixo = eixo.normalize() if eixo.length_squared() > 0 else V2(1, 0)
        self.lado = V2(-self.eixo.y, self.eixo.x)
        self.comprimento, self.largura = comprimento, largura
        self.area = comprimento * largura
        meia = self.lado * (largura / 2)
        fim = self.eixo * comprimento
        self.cantos = (self.origem + meia, self.origem - meia, self.origem - meia + fim, self.origem + meia + fim)

    def sortear(self):
        return (self.origem + self.eixo * SORTEIO.uniform(0, self.comprimento)
                + self.lado * SORTEIO.uniform(-self.largura / 2, self.largura / 2))

    def fissuras(self):
        """Uma fissura ao longo do eixo e galhos curtos para os lados."""
        passos = max(2, round(self.comprimento / PASSO_FISSURA))
        tronco = [self.origem + self.eixo * (self.comprimento * i / passos)
                  + self.lado * (SORTEIO.uniform(-1, 1) * self.largura * 0.12 if 0 < i < passos else 0)
                  for i in range(passos + 1)]
        galhos = []
        for i in range(1, passos, 2):
            lado = SORTEIO.choice((-1, 1))
            ponta = tronco[i] + (self.lado * lado * SORTEIO.uniform(0.2, 0.42) * self.largura
                                 + self.eixo * SORTEIO.uniform(-0.3, 0.6) * PASSO_FISSURA)
            galhos.append((i / passos, [tronco[i], ponta]))
        return [(0.0, tronco)], galhos

    def caixa(self, margem):
        xs, ys = [c.x for c in self.cantos], [c.y for c in self.cantos]
        return pygame.Rect(int(min(xs)) - margem, int(min(ys)) - margem,
                           int(max(xs) - min(xs)) + 2 * margem, int(max(ys) - min(ys)) + 2 * margem)

    def preencher(self, camada, cor, deslocamento):
        pygame.draw.polygon(camada, cor, [c - deslocamento for c in self.cantos])


class _Circulo:
    def __init__(self, centro, raio):
        self.centro, self.raio = V2(centro), raio
        self.area = math.pi * raio * raio

    def sortear(self):
        return self.centro + V2(self.raio * math.sqrt(SORTEIO.random()), 0).rotate(SORTEIO.uniform(0, 360))

    def fissuras(self):
        """Rachaduras do centro para a borda."""
        raios = []
        quantas = 5 if self.raio >= 90 else 3
        base = SORTEIO.uniform(0, 360)
        for i in range(quantas):
            direcao = V2(1, 0).rotate(base + i * 360 / quantas + SORTEIO.uniform(-20, 20))
            pontos = [self.centro]
            for passo in (0.35, 0.7, 0.95):
                pontos.append(self.centro + direcao.rotate(SORTEIO.uniform(-14, 14)) * self.raio * passo)
            raios.append((0.0, pontos))
        return raios, []

    def caixa(self, margem):
        r = int(self.raio) + margem
        return pygame.Rect(int(self.centro.x) - r, int(self.centro.y) - r, 2 * r, 2 * r)

    def preencher(self, camada, cor, deslocamento):
        pygame.draw.circle(camada, cor, self.centro - deslocamento, self.raio)


class EnergiaDoChao(pygame.sprite.Sprite):
    """Carrega por `duracao_ms` e libera sozinha no fim (ou antes, com `liberar()`)."""

    def __init__(self, area, duracao_ms, paleta='gravidade', densidade=1.0, fissura=True, grupos=None):
        super().__init__(*(grupos or (entity_manager.all_sprites,)))
        self.area = area
        self.duracao_ms = max(1.0, duracao_ms)
        self.cores, self.cor_fissura, self.cor_miolo, self.cor_clarao = PALETAS[paleta]
        self.densidade = densidade
        self.nascimento = relogio.agora()
        self.liberada_em = None
        self._acumulado = 0.0
        self._troncos, self._galhos = area.fissuras() if fissura else ([], [])
        self._caixa = area.caixa(12)
        self.image = SUPERFICIE_VAZIA                 # o draw é próprio
        self.rect = self._caixa.copy()
        self.y_desenho = self._caixa.top              # efeito de chão: por baixo de quem está na área

    @property
    def progresso(self):
        return min(1.0, (relogio.agora() - self.nascimento) / self.duracao_ms)

    def update(self, delta_time, *args):
        agora = relogio.agora()
        if self.liberada_em is not None:
            if agora - self.liberada_em >= CLARAO_MS:
                self.kill()
            return
        t = self.progresso
        por_segundo = min(MAX_POR_SEGUNDO, self.area.area * PARTICULAS_POR_PX2 * self.densidade
                          * (1 + (CRESCIMENTO - 1) * t))
        self._acumulado += por_segundo * delta_time
        while self._acumulado >= 1:
            self._acumulado -= 1
            subida = SORTEIO.uniform(50, 150) * (0.6 + t)
            emitir(self.area.sortear(), imagem_pixel(SORTEIO.choice(self.cores), SORTEIO.choice(TAMANHOS), 'circulo'),
                   (SORTEIO.uniform(-15, 15), -subida), SORTEIO.uniform(350, 700))
        if t >= 1.0:
            self.liberar()

    def liberar(self):
        """Solta a energia: coluna de partículas subindo (e caindo) e o clarão na área."""
        if self.liberada_em is not None:
            return
        self.liberada_em = relogio.agora()
        minimo, maximo = LIBERACAO_LIMITES
        quantidade = max(minimo, min(maximo, round(self.area.area * LIBERACAO_POR_PX2 * self.densidade)))
        for _ in range(quantidade):
            vel = (SORTEIO.uniform(-60, 60), -SORTEIO.uniform(220, 520))
            emitir(self.area.sortear(), imagem_pixel(SORTEIO.choice(self.cores), SORTEIO.choice(TAMANHOS), 'circulo'),
                   vel, SORTEIO.uniform(450, 850), gravidade=650)

    def draw(self, surface, offset):
        camada, area = camada_alpha(surface, self._caixa.move(-int(offset.x), -int(offset.y)))
        if camada is None:
            return
        if self.liberada_em is None:
            self._desenhar_fissuras(camada, offset, self.progresso, 1.0)
        else:
            resto = 1.0 - min(1.0, (relogio.agora() - self.liberada_em) / CLARAO_MS)
            self.area.preencher(camada, (*self.cor_clarao, round(120 * resto)), offset)
            self._desenhar_fissuras(camada, offset, 1.0, resto)
        surface.blit(camada, area.topleft, area)

    def _desenhar_fissuras(self, camada, offset, t, forca):
        if not self._troncos or t <= 0:
            return
        brilho = 0.55 + 0.45 * math.sin(relogio.agora() / 55)    # a fissura pulsa enquanto carrega
        halo = (*self.cor_fissura, round(140 * forca * brilho))
        miolo = (*self.cor_miolo, round(235 * forca))
        for _, pontos in self._troncos:
            visiveis = _ate_fracao(pontos, t)
            if len(visiveis) >= 2:
                tela = [p - offset for p in visiveis]
                pygame.draw.lines(camada, halo, False, tela, 14)
                pygame.draw.lines(camada, miolo, False, tela, 4)
        for inicio, pontos in self._galhos:
            if t >= inicio:
                tela = [p - offset for p in pontos]
                pygame.draw.lines(camada, halo, False, tela, 9)
                pygame.draw.lines(camada, miolo, False, tela, 3)


def _ate_fracao(pontos, t):
    """Os pontos da polilinha até a fração `t` do caminho (a fissura cresce do dono para a ponta)."""
    if t >= 1.0:
        return pontos
    ultimo = (len(pontos) - 1) * t
    inteiro = int(ultimo)
    saida = pontos[:inteiro + 1]
    if inteiro + 1 < len(pontos):
        saida = saida + [pontos[inteiro].lerp(pontos[inteiro + 1], ultimo - inteiro)]
    return saida


def energia_no_retangulo(origem, direcao, comprimento, largura, duracao_ms, paleta='gravidade', densidade=1.0,
                         fissura=True):
    return EnergiaDoChao(_Retangulo(origem, direcao, comprimento, largura), duracao_ms, paleta, densidade, fissura)


def energia_no_circulo(centro, raio, duracao_ms, paleta='gravidade', densidade=1.0, fissura=True):
    return EnergiaDoChao(_Circulo(centro, raio), duracao_ms, paleta, densidade, fissura)


def sugar_para_o_centro(centro, raio, quantidade, paleta='vortice', giro=0.45):
    """Partículas que nascem na borda de um círculo e são sugadas para o centro girando (vórtice).
    `giro`: quanto da velocidade é de lado (0 = reto para o centro)."""
    centro = V2(centro)
    cores = PALETAS[paleta][0]
    for _ in range(quantidade):
        fora = V2(1, 0).rotate(SORTEIO.uniform(0, 360))
        distancia = raio * SORTEIO.uniform(0.75, 1.05)
        velocidade = SORTEIO.uniform(260, 420)
        para_dentro = -fora * (1 - giro) + V2(-fora.y, fora.x) * giro
        para_dentro.scale_to_length(velocidade)
        emitir(centro + fora * distancia, imagem_pixel(SORTEIO.choice(cores), SORTEIO.choice(TAMANHOS), 'circulo'),
               para_dentro, distancia / velocidade * 1000 * 0.9)
