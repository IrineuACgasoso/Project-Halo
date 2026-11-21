"""Utilitários compartilhados pelos testes (importe com `from helpers import ...`)."""
from collections import Counter
from contextlib import contextmanager

import pygame

from source.feats.assets import ASSETS
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import PASSO_FIXO
from source.systems.mapmanager import Mapa
from source.systems.mapmanager.map_collision import MapCollision
from source.systems.mapmanager.map_feats import MapFeats
from source.systems.mapmanager.map_loader import MapLoader
from source.systems.mapmanager.map_utils import MapUtils
from source.utils.paths import path

DT = PASSO_FIXO   # o mesmo passo fixo do Game.run (segundos)


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


# Funções de pygame.transform que não criam Surface (devolvem número/cor ou só configuram).
_TRANSFORM_SEM_ALOCACAO = {'average_color', 'threshold', 'get_smoothscale_backend',
                           'set_smoothscale_backend'}


class ContadorDeAlocacoes:
    """Contagem por tipo ('Surface', 'mask.from_surface', 'transform.scale', 'font.Font'...)."""

    def __init__(self):
        self.por_tipo = Counter()
        self.ativo = True

    @property
    def total(self):
        return sum(self.por_tipo.values())

    @contextmanager
    def pausado(self):
        """Trecho que não entra na conta (ex.: repor a horda, que não é custo do frame).
        Pode ser aninhado: ao sair, volta ao estado anterior (não reativa uma pausa externa)."""
        anterior, self.ativo = self.ativo, False
        try:
            yield
        finally:
            self.ativo = anterior

    def _contar(self, tipo):
        if self.ativo:
            self.por_tipo[tipo] += 1


@contextmanager
def contar_alocacoes():
    """Conta as chamadas que criam Surface/máscara/fonte enquanto o bloco roda (roteiro A2).

    Cobre `pygame.Surface(...)`, `pygame.mask.from_surface`, `pygame.transform.*` e
    `pygame.font.Font`/`SysFont`. Funciona porque o código do jogo só usa a forma `pygame.X`.
    NÃO cobre métodos de tipos em C (`Surface.copy`, `convert_alpha`, `subsurface`,
    `Font.render`): o monkeypatch não alcança método de tipo embutido.
    """
    import pytest   # só em dev; quem importa helpers sem contar alocações não precisa dele
    contador = ContadorDeAlocacoes()
    surface_original = pygame.Surface

    class _MetaSurface(type):
        # Conta e devolve uma Surface original: isinstance(x, pygame.Surface) continua valendo
        # para as Surfaces criadas antes do patch (enemy_sprites e items/draw dependem disso).
        def __call__(cls, *args, **kwargs):
            contador._contar('Surface')
            return surface_original(*args, **kwargs)

        def __instancecheck__(cls, obj):
            return isinstance(obj, surface_original)

        def __subclasscheck__(cls, sub):
            return issubclass(sub, surface_original)

    def _envolver(tipo, funcao):
        def envolvida(*args, **kwargs):
            contador._contar(tipo)
            return funcao(*args, **kwargs)
        return envolvida

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(pygame, 'Surface', _MetaSurface('Surface', (), {}))
        mp.setattr(pygame.mask, 'from_surface',
                   _envolver('mask.from_surface', pygame.mask.from_surface))
        for nome in dir(pygame.transform):
            if nome.startswith('_') or nome in _TRANSFORM_SEM_ALOCACAO:
                continue
            mp.setattr(pygame.transform, nome,
                       _envolver(f'transform.{nome}', getattr(pygame.transform, nome)))
        for nome in ('Font', 'SysFont'):
            mp.setattr(pygame.font, nome, _envolver(f'font.{nome}', getattr(pygame.font, nome)))
        yield contador


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
