"""Leitura de mapas Tiled (.tmj), colisão com paredes, void e zonas de navegação."""
import json

import pygame
import pytest

from helpers import MapaSemImagem

V = pygame.math.Vector2


def _tmj(tmp_path, layers):
    arq = tmp_path / 'm.tmj'
    arq.write_text(json.dumps({'layers': layers}), encoding='utf-8')
    return str(arq)


def _grupo(nome, objetos):
    return {'type': 'objectgroup', 'name': nome, 'objects': objetos}


@pytest.fixture
def mapa_carregado(tmp_path):
    mapa = MapaSemImagem()
    mapa.carregar_json(_tmj(tmp_path, [
        {'type': 'tilelayer', 'name': 'Chao'},   # camadas desconhecidas são ignoradas
        _grupo('Colisoes', [
            {'x': 100, 'y': 100, 'width': 50, 'height': 20},
            {'x': 0, 'y': 0, 'polyline': [{'x': 0, 'y': 0}, {'x': 10, 'y': 0}]},
            {'x': 500, 'y': 500, 'polygon': [{'x': 0, 'y': 0}, {'x': 10, 'y': 0}, {'x': 0, 'y': 10}]},
        ]),
        _grupo('SpawnPoints', [
            {'x': 10, 'y': 20, 'point': True},
            {'x': 100, 'y': 100, 'width': 40, 'height': 60},
        ]),
        _grupo('SpawnPlayer', [{'x': 300, 'y': 300, 'point': True}, {'x': 1, 'y': 1, 'point': True}]),
        _grupo('Portal', [{'x': 800, 'y': 800, 'width': 100, 'height': 50}]),
        _grupo('Void', [{'x': 0, 'y': 1000, 'width': 200, 'height': 200}]),
        _grupo('VoidPoint', [{'x': 100, 'y': 1100}]),
        _grupo('Navigation', [{'x': 0, 'y': 0, 'width': 1000, 'height': 1000}]),
    ]))
    return mapa


def test_spawn_do_player_usa_so_o_primeiro(mapa_carregado):
    assert mapa_carregado.player_spawn_manual == V(300, 300)


def test_posicao_valida_respeita_navegacao(mapa_carregado):
    assert mapa_carregado.posicao_e_valida(V(500, 500))
    assert not mapa_carregado.posicao_e_valida(V(1500, 1500))


def test_void_puxa_para_o_ponto(mapa_carregado):
    forca, alvo, dist = mapa_carregado.calcular_puxo_void(V(100, 1000))
    assert alvo == V(100, 1100)
    assert dist == pytest.approx(100)
    assert forca.y > 0 and forca.length() == pytest.approx(2.5)


# ── MapCollision ─────────────────────────────────────────────────────────────
@pytest.fixture
def mapa_parede():
    mapa = MapaSemImagem()
    mapa.paredes = [{'tipo': 'linha', 'pontos': [V(100, 0), V(100, 200)]}]   # parede vertical x=100
    return mapa


def test_caminho_livre_bloqueado_pela_parede(mapa_parede):
    assert not mapa_parede.caminho_livre((0, 100), (200, 100))


def test_caminho_livre_quando_nao_cruza(mapa_parede):
    assert mapa_parede.caminho_livre((0, 100), (90, 100))
    assert mapa_parede.caminho_livre((0, 300), (200, 300))


def test_cache_de_bbox_invalida_quando_paredes_mudam(mapa_parede):
    assert mapa_parede.caminho_livre((5050, 4900), (5050, 5100))
    mapa_parede.paredes.append({'tipo': 'linha', 'pontos': [V(5000, 5000), V(5100, 5000)]})
    assert not mapa_parede.caminho_livre((5050, 4900), (5050, 5100))
