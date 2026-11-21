"""Dados dos inimigos comuns (roteiro D4): equivalência com os valores que viviam nas classes.

`tests/golden/inimigos.json` foi gravado com os valores fixos nas classes, ANTES da troca por
`data/enemy_data.py`: para cada classe, os stats logo depois de criada, as faixas pedidas a
`novo_cooldown` em 30 s de update (perto do jogador) e os drops da morte, na ordem.
Regravar (só em mudança de balanceamento declarada, com o motivo em docs/log.md):
    .venv\\Scripts\\python.exe -m pytest tests/unit/test_dados_inimigos.py --atualizar-golden
"""
import dataclasses
import json
import os
import random

import pygame
import pytest

from helpers import DT, voltar_ao_menu
from source.data.enemy_data import DROP_COVENANT_FORTE, DROP_PADRAO, INIMIGOS, PerfilInimigo
from source.enemies.base.enemy_combat import EnemyCombat
from source.enemies.standard.brute import Brute
from source.enemies.standard.crawler import Crawler
from source.enemies.standard.elite import Elite, Halo4Elite, ReachElite
from source.enemies.standard.grunt import GruntBlue, GruntRed, SpaceGrunt
from source.enemies.standard.infection import FloodCarry, FloodElite, FloodMarine, Infection
from source.enemies.standard.jackal import Jackal, JackalSniper
from source.enemies.standard.sentinel import Sentinel, SentinelMajor
from source.enemies.standard.soldier import Soldier
from source.enemies.standard.watcher import SuperWatcher, Watcher
from source.feats.items import Items
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio

CAMINHO_REGISTRO = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'golden', 'inimigos.json')

CLASSES = [GruntRed, GruntBlue, SpaceGrunt, Jackal, JackalSniper, Elite, ReachElite, Halo4Elite,
           Brute, Infection, FloodElite, FloodCarry, FloodMarine, Sentinel, SentinelMajor,
           Crawler, Soldier, Watcher, SuperWatcher]
STATS = ('vida_base', 'vida', 'vida_maxima', 'dano_base', 'dano', 'velocidade_base', 'velocidade',
         'escudo_maximo')
SEGUNDOS_DE_UPDATE = 30


def _lista(valor):
    """Tuplas aninhadas viram listas (o formato do JSON)."""
    return [_lista(v) for v in valor] if isinstance(valor, (tuple, list)) else valor


def registrar(game, classe, monkeypatch):
    faixas, drops = set(), []
    novo_cooldown = EnemyCombat.novo_cooldown

    def espiao_cooldown(self, minimo, maximo):
        faixas.add((minimo, maximo))
        return novo_cooldown(self, minimo, maximo)

    def espiao_drop(cls, posicao, grupos, id_arma_alvo=None, **tabela):
        # na ordem dos kwargs: spawn_drop sorteia item por item, e a ordem muda a sequência aleatória
        drops.append([[item, _lista(config)] for item, config in tabela.items()])

    monkeypatch.setattr(EnemyCombat, 'novo_cooldown', espiao_cooldown)
    monkeypatch.setattr(Items, 'spawn_drop', classmethod(espiao_drop))

    random.seed(7)
    inimigo = classe(game.player.posicao + pygame.math.Vector2(300, 0), game)
    stats = {nome: getattr(inimigo, nome) for nome in STATS}
    paredes = game.mapa.grade_paredes
    for _ in range(int(SEGUNDOS_DE_UPDATE / DT)):
        relogio.avancar(DT)
        inimigo.update(DT, paredes)
    inimigo.morrer((entity_manager.all_sprites, entity_manager.items_grupo))
    return {'stats': stats, 'cooldowns': sorted(_lista(f) for f in faixas), 'drops': drops}


def test_classes_equivalentes_ao_registro(novo_jogo, monkeypatch, request):
    obtido = {}
    for classe in CLASSES:
        voltar_ao_menu(novo_jogo)
        novo_jogo.iniciar_novo_jogo()   # cada classe numa partida limpa (relógio, grupos)
        obtido[classe.__name__] = registrar(novo_jogo, classe, monkeypatch)
    if request.config.getoption('--atualizar-golden'):
        with open(CAMINHO_REGISTRO, 'w', encoding='utf-8') as f:
            json.dump(obtido, f, indent=1, sort_keys=True)
        pytest.skip(f'registro regravado em {CAMINHO_REGISTRO}: registre o motivo em docs/log.md')
    with open(CAMINHO_REGISTRO, encoding='utf-8') as f:
        esperado = json.load(f)
    for nome in esperado:
        assert obtido[nome] == esperado[nome], nome
    assert set(obtido) == set(esperado)


# ------------------------------------------------------------------ #
# Perfis
# ------------------------------------------------------------------ #
PERFIL_DA_CLASSE = {
    GruntRed: 'grunt_red', GruntBlue: 'grunt_blue', SpaceGrunt: 'space_grunt',
    Jackal: 'jackal', JackalSniper: 'jackal',
    Elite: 'elite', ReachElite: 'reach_elite', Halo4Elite: 'halo4_elite', Brute: 'brute',
}


def test_perfil_e_imutavel():
    perfil = INIMIGOS['grunt_red']
    with pytest.raises(dataclasses.FrozenInstanceError):
        perfil.vida = 999
    with pytest.raises(TypeError):
        perfil.cooldowns['plasma'] = (1, 2)
    with pytest.raises(TypeError):
        perfil.drops['exp_shard'] = (9, 100, 100)
    with pytest.raises(TypeError):
        INIMIGOS['novo'] = perfil


def test_perfil_padrao_nao_tem_cooldown_e_usa_o_drop_padrao():
    perfil = PerfilInimigo(1, 2, 3)
    assert dict(perfil.cooldowns) == {}
    assert perfil.drops is DROP_PADRAO


def test_chave_inexistente_e_keyerror():
    with pytest.raises(KeyError):
        INIMIGOS['nao_existe']


@pytest.mark.parametrize('classe', list(PERFIL_DA_CLASSE), ids=lambda c: c.__name__)
def test_classe_usa_o_seu_perfil(novo_jogo, classe):
    inimigo = classe(novo_jogo.player.posicao + pygame.math.Vector2(300, 0), novo_jogo)
    perfil = INIMIGOS[PERFIL_DA_CLASSE[classe]]
    assert inimigo.perfil is perfil
    assert inimigo.tabela_drop is perfil.drops


def test_mudar_o_perfil_muda_o_inimigo(novo_jogo, monkeypatch):
    # Prova que o balanceamento vem dos dados, não de um número que sobrou na classe.
    import source.enemies.standard.grunt as modulo_grunt
    outro = dataclasses.replace(INIMIGOS['grunt_red'], vida=40, dano=7, velocidade=10,
                                drops=DROP_COVENANT_FORTE)
    monkeypatch.setattr(modulo_grunt, 'INIMIGOS', {**INIMIGOS, 'grunt_red': outro})
    grunt = GruntRed(novo_jogo.player.posicao + pygame.math.Vector2(300, 0), novo_jogo)
    escala = 1 + novo_jogo.player.contador_niveis / 10
    assert grunt.vida_base == pytest.approx(40 * escala)
    assert grunt.dano_base == pytest.approx(7 * escala)
    assert grunt.tabela_drop is DROP_COVENANT_FORTE


def test_perfil_sem_o_cooldown_que_a_classe_usa_falha_ao_criar(novo_jogo, monkeypatch):
    import source.enemies.standard.grunt as modulo_grunt
    sem_plasma = dataclasses.replace(INIMIGOS['grunt_red'], cooldowns=INIMIGOS['brute'].cooldowns)
    monkeypatch.setattr(modulo_grunt, 'INIMIGOS', {**INIMIGOS, 'grunt_red': sem_plasma})
    with pytest.raises(KeyError, match='plasma'):
        GruntRed(novo_jogo.player.posicao, novo_jogo)


def test_inimigo_sem_perfil_usa_o_drop_padrao(novo_jogo, monkeypatch):
    # Bosses e minibosses sem morrer() próprio continuam com a tabela de sempre.
    from source.enemies.base.enemy_setup import EnemySetup

    class SemPerfil(EnemySetup, EnemyCombat):
        def kill(self):
            pass

    tabelas = []
    monkeypatch.setattr(Items, 'spawn_drop',
                        classmethod(lambda cls, pos, grupos, id_arma_alvo=None, **t: tabelas.append(t)))
    inimigo = SemPerfil()
    inimigo.setup_core(novo_jogo, sprite_key=None, variante=None)
    inimigo.posicao = pygame.math.Vector2(0, 0)
    inimigo.morrer(None)
    assert tabelas == [dict(DROP_PADRAO)]
    assert list(tabelas[0]) == ['exp_shard', 'big_shard', 'life_orb', 'upgrade']
