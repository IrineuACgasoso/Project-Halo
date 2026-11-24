"""Camada alpha reaproveitada, máscaras em cache e partículas com teto global."""
import random

import pygame
import pytest

from helpers import DT, blindar_jogador, contar_alocacoes, simular
from source.feats import particulas
from source.feats.effects import emitir_poeira
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.utils.superficies import camada_alpha

V = pygame.math.Vector2
TELA = (1280, 720)


# ------------------------------------------------------------------ #


def test_camada_alpha_recorta_limpa_e_reaproveita():
    tela = pygame.Surface(TELA)
    camada, area = camada_alpha(tela, (-50, -20, 100, 60))
    assert area == pygame.Rect(0, 0, 50, 40)
    assert camada.get_size() == TELA and camada.get_flags() & pygame.SRCALPHA
    assert camada.get_clip() == area
    camada.fill((255, 0, 0, 255))   # sujeira de um uso anterior
    de_novo, area2 = camada_alpha(tela, (10, 10, 5, 5))
    assert de_novo is camada
    assert de_novo.get_at((12, 12)) == (0, 0, 0, 0)        # a área pedida vem limpa
    assert de_novo.get_at((40, 30))[3] == 255               # fora dela, ninguém garante nada


# ------------------------------------------------------------------ #


@pytest.mark.integration
def test_update_da_horda_nao_cria_mascara(novo_jogo):
    """O update da horda criava ~12 máscaras por frame (animação dos inimigos)."""
    blindar_jogador(novo_jogo.player)
    novo_jogo.spawner.update = lambda dt: None
    while len(entity_manager.inimigos_grupo) < 150:
        novo_jogo.spawner.spawnar('normal')
    simular(novo_jogo, 1)   # aquece os caches
    with contar_alocacoes() as c:
        simular(novo_jogo, 2)
    assert c.por_tipo['mask.from_surface'] <= 2, dict(c.por_tipo)   # só projétil em ângulo novo


# ------------------------------------------------------------------ #
def test_particula_anda_some_com_fade_e_morre(novo_jogo):
    base = particulas.imagem_pixel((255, 0, 0), 4)
    p = particulas.emitir(V(100, 100), base, (60, 0), 500)
    assert p in entity_manager.particulas_grupo and p in entity_manager.all_sprites
    alphas = []
    for _ in range(round(0.4 / DT)):
        relogio.avancar(DT)
        p.update(DT)
        alphas.append(p.image.get_alpha())
    assert p.posicao.x == pytest.approx(124, abs=0.5)
    assert alphas == sorted(alphas, reverse=True) and alphas[-1] < 100
    relogio.avancar(0.2)
    p.update(DT)
    assert not p.alive()


def test_teto_global_descarta_as_novas(novo_jogo, monkeypatch):
    monkeypatch.setattr(particulas, 'TETO_PARTICULAS', 5)
    base = particulas.imagem_pixel((0, 255, 0), 3)
    criadas = [particulas.emitir(V(0, 0), base, (0, 0), 1000) for _ in range(8)]
    assert sum(p is not None for p in criadas) == 5
    assert len(entity_manager.particulas_grupo) == 5
    criadas[0].kill()
    assert particulas.emitir(V(0, 0), base, (0, 0), 1000) is not None


def test_descarte_nao_muda_a_sequencia_do_random(novo_jogo, monkeypatch):
    random.seed(99)
    for _ in range(5):
        emitir_poeira(V(0, 0))
    esperado = random.random()
    monkeypatch.setattr(particulas, 'TETO_PARTICULAS', 0)
    random.seed(99)
    for _ in range(5):
        assert emitir_poeira(V(0, 0)) is None
    assert random.random() == esperado


def test_nova_partida_zera_as_particulas(game):
    from helpers import voltar_ao_menu
    voltar_ao_menu(game)
    game.iniciar_novo_jogo()
    emitir_poeira(V(0, 0))
    assert len(entity_manager.particulas_grupo) == 1
    voltar_ao_menu(game)
    game.iniciar_novo_jogo()
    assert len(entity_manager.particulas_grupo) == 0
