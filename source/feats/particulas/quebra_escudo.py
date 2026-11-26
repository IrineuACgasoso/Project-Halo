"""Quebra de escudo: o efeito padrão de todo escudo que acaba, do jogador e dos inimigos
(ganchos `zerar_escudo` e `ao_quebrar_escudo`)."""
import random

import pygame

from source.systems.gameclock import relogio

from .motor import emitir, imagem_pixel, variantes_alpha

SORTEIO = random.Random()   # só visual: não mexe na sequência da simulação

CORES_FAGULHA_AZUL = ((90, 190, 255), (40, 120, 255), (200, 240, 255))
CORES_FAGULHA_AMARELA = ((255, 235, 120), (255, 200, 50))
FAGULHAS_POR_PX = 0.45          # quantidade pelo tamanho do corpo
FAGULHAS_LIMITES = (26, 70)
MS_ENTRE_QUEBRAS = 400          # escudo que regenera um fio e cai de novo não vira uma chuva
TAMANHOS_FAGULHA = (4, 6, 8)


def preparar_quebra_de_escudo():
    """Pinta já as fagulhas (no início da partida): jogador e Elites quebram escudo no meio da horda."""
    for cor in CORES_FAGULHA_AMARELA + CORES_FAGULHA_AZUL:
        for tamanho in TAMANHOS_FAGULHA:
            variantes_alpha(imagem_pixel(cor, tamanho))


def quebra_de_escudo(alvo, cores=CORES_FAGULHA_AZUL, cores_destaque=CORES_FAGULHA_AMARELA):
    """Fagulhas (`cores`, com 1 em 3 de `cores_destaque`) que saltam em volta do corpo de `alvo` e
    caem. Devolve False se a última quebra dele foi há pouco (sem efeito)."""
    agora = relogio.agora()
    if agora < getattr(alvo, 'proxima_quebra_escudo', 0):
        return False
    alvo.proxima_quebra_escudo = agora + MS_ENTRE_QUEBRAS
    corpo = getattr(alvo, 'hitbox', alvo.rect)
    minimo, maximo = FAGULHAS_LIMITES
    quantidade = max(minimo, min(maximo, round((corpo.width + corpo.height) * FAGULHAS_POR_PX)))
    centro = pygame.math.Vector2(corpo.center)
    for i in range(quantidade):
        direcao = pygame.math.Vector2(1, 0).rotate(SORTEIO.uniform(0, 360))
        borda = pygame.math.Vector2(direcao.x * corpo.width, direcao.y * corpo.height) * SORTEIO.uniform(0.35, 0.6)
        velocidade = direcao * SORTEIO.uniform(60, 220) - (0, SORTEIO.uniform(40, 160))
        cor = SORTEIO.choice(cores_destaque if i % 3 == 0 else cores)
        emitir(centro + borda, imagem_pixel(cor, SORTEIO.choice(TAMANHOS_FAGULHA)), velocidade,
               SORTEIO.uniform(700, 1200), y_desenho=alvo.rect.bottom + 1, gravidade=620)
    return True
