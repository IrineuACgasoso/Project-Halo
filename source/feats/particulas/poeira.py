"""Poeira: a de terra que salta do chão (`emitir_poeira`, da simulação) e as nuvens só visuais de
impacto (área, retângulo, anel e rastro de corrida), com sorteio próprio."""
import random

import pygame

from .motor import emitir, emitir_leque, imagem_pixel, preparar

V2 = pygame.math.Vector2
SORTEIO = random.Random()      # só visual: não mexe na sequência da simulação

DURACAO_POEIRA_MS = 255 / 400 * 1000   # o alpha caía 400/s a partir de 255
CORES_TERRA = ((70, 50, 30), (40, 60, 30), (100, 80, 50))      # marrom esverdeado (lodo)
CORES_PEDRA = ((120, 108, 92), (92, 82, 70), (150, 138, 118), (70, 62, 54))   # poeira de impacto
TAMANHOS_NUVEM = (6, 9, 12, 16)


def emitir_poeira(posicao, grupos=None):
    """Partícula de terra/lodo que explode para os lados e para cima e some com fade.
    Usa o `random` global (mesma sequência da antiga DustParticle: a simulação depende dela)."""
    tamanho = random.randint(4, 8)
    cor = random.choice(CORES_TERRA)
    direcao = V2(random.uniform(-1, 1), random.uniform(-2, -0.5))
    velocidade = random.uniform(50, 150)
    return emitir(posicao, imagem_pixel(cor, tamanho, 'circulo'), direcao * velocidade, DURACAO_POEIRA_MS, grupos)


def preparar_poeira(cores=CORES_PEDRA, tamanhos=TAMANHOS_NUVEM):
    """Pinta já as imagens da nuvem (no spawn de quem levanta poeira)."""
    preparar(cores, tamanhos)


def _nuvem(ponto, cores, tamanhos, subida, duracao_ms):
    vel = V2(SORTEIO.uniform(-1, 1), SORTEIO.uniform(-1, 0.2)) * SORTEIO.uniform(*subida)
    emitir(ponto, imagem_pixel(SORTEIO.choice(cores), SORTEIO.choice(tamanhos), 'circulo'), vel,
           SORTEIO.uniform(*duracao_ms))


def poeira_em_area(centro, raio, quantidade, cores=CORES_PEDRA, tamanhos=TAMANHOS_NUVEM,
                   subida=(20, 90), duracao_ms=(600, 1300)):
    """Nuvem que sobe devagar de pontos sorteados num círculo de `raio` (impacto no chão)."""
    centro = V2(centro)
    for _ in range(quantidade):
        ponto = centro + V2(SORTEIO.uniform(0, raio), 0).rotate(SORTEIO.uniform(0, 360))
        _nuvem(ponto, cores, tamanhos, subida, duracao_ms)


def poeira_no_retangulo(origem, direcao, comprimento, largura, quantidade, cores=CORES_PEDRA,
                        tamanhos=TAMANHOS_NUVEM, subida=(20, 90), duracao_ms=(600, 1300)):
    """Nuvem em toda a área do retângulo que sai de `origem` na `direcao` (como o RectStrike)."""
    eixo = V2(direcao)
    if eixo.length_squared() == 0:
        eixo.update(1, 0)
    eixo.normalize_ip()
    lado = V2(-eixo.y, eixo.x)
    origem = V2(origem)
    for _ in range(quantidade):
        ponto = (origem + eixo * SORTEIO.uniform(0, comprimento)
                 + lado * SORTEIO.uniform(-largura / 2, largura / 2))
        _nuvem(ponto, cores, tamanhos, subida, duracao_ms)


def anel_de_poeira(centro, raio, quantidade, cores=CORES_PEDRA, tamanhos=TAMANHOS_NUVEM,
                   velocidade=(160, 380), duracao_ms=(450, 900)):
    """Onda de poeira que se abre para fora a partir da borda de um círculo (pouso, martelada)."""
    centro = V2(centro)
    for _ in range(quantidade):
        direcao = V2(1, 0).rotate(SORTEIO.uniform(0, 360))
        vel = direcao * SORTEIO.uniform(*velocidade)
        emitir(centro + direcao * raio * SORTEIO.uniform(0.2, 0.6),
               imagem_pixel(SORTEIO.choice(cores), SORTEIO.choice(tamanhos), 'circulo'), vel,
               SORTEIO.uniform(*duracao_ms))


def rastro_de_poeira(pes, direcao, quantidade=2, cores=CORES_PEDRA, tamanhos=(6, 9, 12)):
    """Poeira levantada para trás por quem corre (chame por passo de corrida)."""
    emitir_leque(pes, -V2(direcao) if V2(direcao).length_squared() else V2(0, -1), quantidade, cores,
                 tamanhos, abertura_graus=70, velocidade=(40, 140), duracao_ms=(350, 700), sorteio=SORTEIO)
