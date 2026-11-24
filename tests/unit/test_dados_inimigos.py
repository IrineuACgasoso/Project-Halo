"""Todo inimigo comum usa o seu perfil de `data/enemy_data.py`."""

import pygame
import pytest

from source.data.enemy_data import INIMIGOS
from source.enemies.standard.brute import Brute
from source.enemies.standard.crawler import Crawler
from source.enemies.standard.elite import Elite, Halo4Elite, ReachElite
from source.enemies.standard.grunt import GruntBlue, GruntRed, SpaceGrunt
from source.enemies.standard.infection import FloodCarry, FloodElite, FloodMarine, Infection
from source.enemies.standard.jackal import Jackal, JackalSniper
from source.enemies.standard.sentinel import Sentinel, SentinelMajor
from source.enemies.standard.soldier import Soldier
from source.enemies.standard.watcher import SuperWatcher, Watcher


CLASSES = [GruntRed, GruntBlue, SpaceGrunt, Jackal, JackalSniper, Elite, ReachElite, Halo4Elite,
           Brute, Infection, FloodElite, FloodCarry, FloodMarine, Sentinel, SentinelMajor,
           Crawler, Soldier, Watcher, SuperWatcher]


# ------------------------------------------------------------------ #
PERFIL_DA_CLASSE = {
    GruntRed: 'grunt_red', GruntBlue: 'grunt_blue', SpaceGrunt: 'space_grunt',
    Jackal: 'jackal', JackalSniper: 'jackal',
    Elite: 'elite', ReachElite: 'reach_elite', Halo4Elite: 'halo4_elite', Brute: 'brute',
    Infection: 'infection', FloodElite: 'flood_elite', FloodCarry: 'flood_carry',
    FloodMarine: 'flood_marine',
    Sentinel: 'sentinel', SentinelMajor: 'sentinel', Crawler: 'crawler', Soldier: 'soldier',
    Watcher: 'watcher', SuperWatcher: 'super_watcher',
}


def test_toda_classe_comum_tem_perfil():
    assert set(PERFIL_DA_CLASSE) == set(CLASSES)
    assert set(PERFIL_DA_CLASSE.values()) == set(INIMIGOS)   # nenhum perfil sobrando


@pytest.mark.parametrize('classe', list(PERFIL_DA_CLASSE), ids=lambda c: c.__name__)
def test_classe_usa_o_seu_perfil(novo_jogo, classe):
    inimigo = classe(novo_jogo.player.posicao + pygame.math.Vector2(300, 0), novo_jogo)
    perfil = INIMIGOS[PERFIL_DA_CLASSE[classe]]
    assert inimigo.perfil is perfil
    assert inimigo.tabela_drop is perfil.drops
