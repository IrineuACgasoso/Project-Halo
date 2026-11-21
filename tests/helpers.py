"""Utilitários compartilhados pelos testes (importe com `from helpers import ...`)."""
import pygame

from source.feats.assets import ASSETS
from source.systems.entitymanager import entity_manager
from source.systems.mapmanager import Mapa
from source.systems.mapmanager.map_collision import MapCollision
from source.systems.mapmanager.map_feats import MapFeats
from source.systems.mapmanager.map_loader import MapLoader
from source.systems.mapmanager.map_utils import MapUtils
from source.utils.paths import path

DT = 1 / 60   # passo fixo de simulação (segundos)


def simular(game, segundos, desenhar_a_cada=0):
    """Roda o loop real (update e, opcionalmente, draw) por `segundos` de jogo."""
    frames = int(segundos / DT)
    for i in range(frames):
        game.update(DT)
        if desenhar_a_cada and i % desenhar_a_cada == 0:
            game.draw()


def blindar_jogador(player):
    """Smoke tests longos: vida enorme (sem game over) e XP inalcançável (sem a tela de
    level-up, que congela o update e esconderia o resto da simulação)."""
    player.vida_maxima = player.vida_atual = 10 ** 9
    player.experiencia_level_up = 10 ** 12


def ir_para_fase(game, fase):
    """Troca o mapa como o StageManager faz, sem a animação de fade. Fase sem mapa usa o da 0."""
    game.fase_atual = fase
    mapa_fase = fase if str(fase) in ASSETS['maps'] else 0
    game.mapa = Mapa(path('assets', 'img', 'map', str(mapa_fase), f'm{mapa_fase}.tmj'),
                     mapa_fase, all_sprites=entity_manager.all_sprites)
    game.camera.mapa = game.mapa
    pos = game.mapa.get_player_spawn_pos()
    game.player.posicao.update(pos)
    game.player.rect.center = game.player.hitbox.center = pos


class MapaSemImagem(MapLoader, MapCollision, MapUtils, MapFeats):
    """Os mesmos mixins de `Mapa`, sem depender de ASSETS['maps'] (testes de .tmj sintético)."""

    def __init__(self, largura=2000, altura=2000):
        self.largura_mapa_pixels = largura
        self.altura_mapa_pixels = altura
        self.paredes = []
        self.zonas_void = []
        self.void_points = []
        self.navigation_zones = []
        self.portal_pos = pygame.math.Vector2(largura / 2, altura / 2)
        self.player_spawn_manual = None
        self.pontos_de_spawn = []
