"""Validação central de dados (roteiro D5): os dados reais passam e cada regra pega o seu erro.

Substitui os testes de integridade que ficavam espalhados (registro de armas, pools, bosses,
manifesto): as regras deles vivem agora em `source/data/validacao.py`.
"""
import dataclasses
import json

import pytest

from source.data import validacao
from source.data.enemy_data import DROP_PADRAO, INIMIGOS, _fixo
from source.data.manifesto_assets import Imagem
from source.data.validacao import (validar_armas, validar_inimigos, validar_manifesto, validar_mapas,
                                   validar_motor_de_bosses, validar_spawner, validar_tudo)
from source.data.weapon_data import COMPANION_DATA, VEHICLES_DATA, WEAPON_DATA, WeaponProfile
from source.enemies.base.boss import BossBase, FaseBoss
from source.enemies.standard.grunt import GruntRed
from source.systems.levelup.constants import (ARMAS_REGISTRO)
from source.systems.spawner.spawner_bosses import BOSS_CLASSES, CRONOGRAMA_BOSSES, PHASE_BOSSES


def test_dados_do_jogo_sao_validos():
    assert validar_tudo() == []


def um_erro(erros, trecho):
    """Exatamente um erro, e ele fala do que foi quebrado."""
    assert len(erros) == 1, erros
    assert trecho in erros[0], erros[0]


# ------------------------------------------------------------------ #
def _armas(**trocas):
    dados = {'armas': WEAPON_DATA, 'companheiros': COMPANION_DATA, 'veiculos': VEHICLES_DATA,
             'registro': ARMAS_REGISTRO}
    dados.update(trocas)
    return validar_armas(**dados)


def test_nome_repetido_entre_categorias():
    um_erro(_armas(veiculos={**VEHICLES_DATA, 'assault_rifle': WEAPON_DATA['assault_rifle']}),
            '"assault_rifle" está em armas e em veículos')


def test_stat_que_diminui_sem_piso():
    stats = dict(WEAPON_DATA['assault_rifle'].stats)
    stats['cooldown'] = dataclasses.replace(stats['cooldown'], min_val=None)
    um_erro(_armas(armas={**WEAPON_DATA, 'assault_rifle': WeaponProfile(stats=stats)}),
            'assault_rifle.cooldown diminui a cada nível e não tem min_val')


@pytest.mark.parametrize('range_val', [0, None, []])
def test_upgrade_que_nenhum_nivel_aplica(range_val):
    """O `duracao` da Energy Sword estava assim: +200 por nível no papel, zero no jogo."""
    stats = dict(WEAPON_DATA['energy_sword'].stats)
    stats['duracao'] = dataclasses.replace(stats['duracao'], range_val=range_val)
    um_erro(validacao.validar_armas(armas={**WEAPON_DATA, 'energy_sword': WeaponProfile(stats=stats)}),
            f'energy_sword.duracao tem label e increase {stats["duracao"].increase:+}, mas o range_val')


@pytest.mark.parametrize('troca, trecho', [
    ({'id': 'outro'}, 'id "outro" diferente da chave'),
    ({'raridade': 'mitica'}, 'raridade "mitica" fora de PALETA_RARIDADE'),
])
def test_registro_invalido(troca, trecho):
    info = dataclasses.replace(ARMAS_REGISTRO['assault_rifle'], **troca)
    um_erro(_armas(registro={**ARMAS_REGISTRO, 'assault_rifle': info}), trecho)


def _brick_com_cooldown(**troca):
    stats = dict(WEAPON_DATA['brick'].stats)
    stats['cooldown'] = dataclasses.replace(stats['cooldown'], **troca)
    return {**WEAPON_DATA, 'brick': WeaponProfile(stats=stats)}


def test_min_val_que_nunca_e_alcancado():
    # Brick é lendária (máximo 5: 4 subidas). Com -100 por nível, 2000 só chega a 1600: o piso 1000 é de mentira.
    um_erro(_armas(armas=_brick_com_cooldown(increase=-100)),
            'brick.cooldown: min_val 1000 não bate com o nível máximo 5 (2000 -100 × 4 = 1600: nunca chega a ele)')


def test_min_val_que_trava_antes_do_fim():
    # -300 × 4 = 1200 > 1000: o limite segura no nível 5, mas o último upgrade dá só 100 (e não 300)
    um_erro(_armas(armas=_brick_com_cooldown(increase=-300)),
            'brick.cooldown: min_val 1000 não bate com o nível máximo 5 (2000 -300 × 4 = 800: passa dele e trava')


def test_arma_registrada_sem_perfil_de_dados():
    sem_perfil = {k: v for k, v in WEAPON_DATA.items() if k != 'assault_rifle'}
    um_erro(_armas(armas=sem_perfil), 'NOME_ASSET "assault_rifle" sem perfil em weapon_data')


# ------------------------------------------------------------------ #
POOL_OK = {'classes': [GruntRed], 'pesos': [1]}


def _spawner(**trocas):
    dados = {'pools': {0: POOL_OK}, 'pool_padrao': POOL_OK, 'bosses_por_fase': PHASE_BOSSES,
             'classes_de_boss': BOSS_CLASSES, 'cronograma': CRONOGRAMA_BOSSES}
    dados.update(trocas)
    return validar_spawner(**dados)


@pytest.mark.parametrize('pool, trecho', [
    ({'classes': [GruntRed], 'pesos': [1, 2]}, '1 classes e 2 pesos'),
    ({'classes': [], 'pesos': []}, '0 classes e 0 pesos'),
    ({'classes': [GruntRed], 'pesos': [0]}, 'peso 0'),
    ({'classes': [GruntRed], 'pesos': ['10']}, "peso '10'"),
    ({'classes': [str], 'pesos': [1]}, "não é um inimigo"),
])
def test_pool_invalido(pool, trecho):
    erros = _spawner(pools={3: pool})
    um_erro(erros, trecho)
    assert erros[0].startswith('pool da fase 3: ')


@pytest.mark.parametrize('dicionario', ['classes_de_boss', 'cronograma'])
def test_boss_fora_de_um_dos_tres_dicts(dicionario):
    original = {'classes_de_boss': BOSS_CLASSES, 'cronograma': CRONOGRAMA_BOSSES}[dicionario]
    sem_hunter = {k: v for k, v in original.items() if k != 'hunter'}
    nome_dict = {'classes_de_boss': 'BOSS_CLASSES', 'cronograma': 'CRONOGRAMA_BOSSES'}[dicionario]
    um_erro(_spawner(**{dicionario: sem_hunter}), f'boss "hunter": falta em {nome_dict}')


# ------------------------------------------------------------------ #
def _boss(**atributos):
    """Classe de boss sobre a BossBase com os atributos trocados (não é instanciada)."""
    base = {'FASES': (FaseBoss('A', 1.0, 1.0, 1.0), FaseBoss('B', 0.5, 1.0, 1.0)),
            'COOLDOWNS': {'golpe': (1000, 2000)}, 'COOLDOWN_INICIAL': {'golpe': 500}}
    return validar_motor_de_bosses({'teste': type('BossTeste', (BossBase,), {**base, **atributos})})


@pytest.mark.parametrize('fases, trecho', [
    ((), 'sequência não vazia de FaseBoss'),
    (('A',), 'sequência não vazia de FaseBoss'),
    ((FaseBoss('A', 0.9, 1.0, 1.0),), '1ª fase precisa ter limiar_vida 1.0 (tem 0.9)'),
    ((FaseBoss('A', 1.0, 1.0, 1.0), FaseBoss('B', 1.0, 1.0, 1.0)), 'limiar da fase "B" (1.0) não é menor'),
    ((FaseBoss('A', 1.0, 1.0, 1.0), FaseBoss('B', 0.3, 1.0, 1.0), FaseBoss('C', 0.6, 1.0, 1.0)),
     'limiar da fase "C" (0.6) não é menor que o de "B" (0.3)'),
])
def test_fases_de_boss_invalidas(fases, trecho):
    erros = _boss(FASES=fases)
    um_erro(erros, trecho)
    assert erros[0].startswith('boss "teste": ')


# ------------------------------------------------------------------ #
def _inimigo(**campos):
    return validar_inimigos({'teste': dataclasses.replace(INIMIGOS['grunt_red'], **campos)})


@pytest.mark.parametrize('campos, trecho', [
    ({'vida': 0}, 'vida 0'),
    ({'vida': True}, 'vida True'),
    ({'dano': -1}, 'dano -1'),
    ({'velocidade': 0}, 'velocidade 0'),
    ({'cooldowns': _fixo({'plasma': (9000, 8000)})}, 'cooldown "plasma" (9000, 8000)'),
    ({'cooldowns': _fixo({'plasma': (0, 8000)})}, 'cooldown "plasma" (0, 8000)'),
    ({'cooldowns': _fixo({'plasma': (8000.5, 9000)})}, 'cooldown "plasma" (8000.5, 9000)'),
    ({'cooldowns': _fixo({'plasma': (8000,)})}, 'cooldown "plasma" (8000,)'),
    ({'drops': _fixo({**DROP_PADRAO, 'moeda': (1, 100, 100)})}, 'item desconhecido "moeda"'),
    ({'drops': _fixo({'exp_shard': (1, 100)})}, 'precisa ser (quantidade, chance, escala)'),
    ({'drops': _fixo({'exp_shard': (1, 100, 0)})}, 'escala 0'),
    ({'drops': _fixo({'exp_shard': (0, 100, 100)})}, 'quantidade 0'),
    ({'drops': _fixo({'exp_shard': (1, 150, 100)})}, 'chance 150'),
    ({'drops': _fixo({'exp_shard': (1, 0, 100)})}, 'chance 0'),
    ({'drops': _fixo({'exp_shard': ((1, 2), (90,), 100)})}, 'mesmo tamanho'),
    ({'drops': _fixo({'exp_shard': ((1, 0), (90, 10), 100)})}, 'quantidades (1, 0)'),
    ({'drops': _fixo({'exp_shard': ((1, 2), (90, -10), 100)})}, 'chances (90, -10)'),
])
def test_perfil_invalido(campos, trecho):
    um_erro(_inimigo(**campos), trecho)


# ------------------------------------------------------------------ #
@pytest.mark.parametrize('folha, trecho', [
    (Imagem('nao_existe/x.png'), 'arquivo ausente assets/img/nao_existe/x.png'),
    (Imagem('player\\player1.png'), 'relativo a assets/img e usar "/"'),
    (Imagem('/player/player1.png'), 'relativo a assets/img e usar "/"'),
    (Imagem('player/player1.png', (0, 10)), 'escala (0, 10)'),
    ('player/player1.png', 'não é Imagem'),
])
def test_manifesto_invalido(folha, trecho):
    um_erro(validar_manifesto({'player': [Imagem('player/player1.png', (10, 10)), folha]}), trecho)


# ------------------------------------------------------------------ #
def _camada(nome, objetos):
    return {'type': 'objectgroup', 'name': nome, 'objects': objetos}


def _tmj(camadas):
    return {'width': 10, 'height': 10, 'tilewidth': 100, 'tileheight': 100, 'layers': camadas}


PAREDE = {'x': 0, 'y': 0, 'width': 50, 'height': 50}
PONTO = {'x': 500, 'y': 500, 'point': True}
MAPA_OK = [_camada('Colisoes', [PAREDE]), _camada('SpawnPoints', [PONTO])]


@pytest.fixture
def mapa_falso(tmp_path, monkeypatch):
    """Grava o .tmj em tmp_path e aponta a validação para ele (fase 0: tem pool e boss)."""
    caminho = tmp_path / 'm0.tmj'
    monkeypatch.setattr(validacao, 'caminho_do_mapa', lambda chave: str(caminho))

    def gravar(conteudo):
        caminho.write_text(conteudo if isinstance(conteudo, str) else json.dumps(conteudo), encoding='utf-8')
        return validar_mapas(['0'])
    return gravar


@pytest.mark.parametrize('camadas, trecho', [
    ([_camada('SpawnPoints', [PONTO])], 'sem paredes'),
    ([_camada('Colisoes', []), _camada('SpawnPoints', [PONTO])], 'sem paredes'),
    ([_camada('Colisoes', [PAREDE])], 'sem pontos de spawn'),
    (MAPA_OK + [_camada('SpawnPlayer', [{'x': 1200, 'y': 10, 'point': True}])], 'spawn do jogador em (1200, 10)'),
    (MAPA_OK + [_camada('Portal', [{'x': 10, 'y': -5}])], 'portal em (10, -5)'),
    ([_camada('Colisoes', [PAREDE]), _camada('SpawnPoints', [PONTO, {'x': 5000, 'y': 5, 'point': True}])],
     'ponto de spawn 1 em (5000, 5)'),
])
def test_mapa_invalido(mapa_falso, camadas, trecho):
    um_erro(mapa_falso(_tmj(camadas)), trecho)


def test_fase_com_mapa_sem_pool_ou_boss(mapa_falso, monkeypatch):
    monkeypatch.setattr(validacao, 'PHASE_POOLS', {})
    monkeypatch.setattr(validacao, 'PHASE_BOSSES', {})
    erros = mapa_falso(_tmj(MAPA_OK))
    assert erros == ['mapa 0: fase 0 sem pool em PHASE_POOLS', 'mapa 0: fase 0 sem boss em PHASE_BOSSES']
