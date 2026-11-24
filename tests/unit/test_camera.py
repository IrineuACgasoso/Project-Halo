"""Zoom da câmera: transição, limites do mapa, o mundo reduzido na tela e quem depende da área visível."""
import pygame
import pytest

from helpers import DT, MapaSemImagem, contar_alocacoes, simular
from source.systems.camera import Camera
from source.systems.gameclock import relogio

V = pygame.math.Vector2


def _camera(largura=4608, altura=3072):
    return Camera(1280, 720, MapaSemImagem(largura, altura))


# ── Camera ───────────────────────────────────────────────────────────────────


def test_zoom_anda_suave_e_so_para_um_lado():
    camera = _camera()
    camera.definir_zoom(0.5, 1000)
    valores = [camera.zoom]
    for _ in range(70):
        relogio.avancar(DT)
        camera.update(V(2000, 1500))
        valores.append(camera.zoom)
    assert valores[0] == 1 and valores[-1] == 0.5
    assert all(b <= a for a, b in zip(valores, valores[1:]))
    assert 0.5 < valores[30] < 1


@pytest.mark.parametrize('jogador', [(0, 0), (4608, 3072), (2300, 1500)])
def test_camera_afastada_nao_sai_do_mapa(jogador):
    camera = _camera()
    camera.definir_zoom(0.5)
    camera.update(V(jogador))
    assert 0 <= camera.offset.x <= 4608 - 2560 and 0 <= camera.offset.y <= 3072 - 1440


def test_zoom_congela_com_o_jogo(novo_jogo):
    novo_jogo.camera.definir_zoom(0.5, 1000)
    antes = novo_jogo.camera.zoom
    pygame.time.wait(5)
    novo_jogo.draw()
    assert novo_jogo.camera.zoom == antes


def test_partida_nova_e_fase_nova_voltam_ao_normal(novo_jogo):
    novo_jogo.camera.definir_zoom(0.5)
    novo_jogo.stage_manager._trocar_dados_fase()
    assert novo_jogo.camera.zoom == 1


# ── Desenho ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize('zoom', [1, 0.5625])
def test_desenhar_com_zoom_nao_aloca_por_frame(novo_jogo, zoom):
    novo_jogo.spawner.update = lambda dt: None
    novo_jogo.camera.definir_zoom(zoom)
    novo_jogo.update(DT)
    for _ in range(3):
        novo_jogo.draw()
    with contar_alocacoes() as contador:
        for _ in range(10):
            novo_jogo.draw()
    assert contador.total == 0, contador.por_tipo


def test_mundo_continua_rodando_com_zoom(novo_jogo):
    novo_jogo.camera.definir_zoom(0.6, 400)
    simular(novo_jogo, 1, desenhar_a_cada=4)
    assert novo_jogo.renderer._erros_logados == set()
