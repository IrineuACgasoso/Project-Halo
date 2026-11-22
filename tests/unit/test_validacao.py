"""Validação central de dados (roteiro D5): os dados reais passam e cada regra pega o seu erro.

Substitui os testes de integridade que ficavam espalhados (registro de armas, pools, bosses,
manifesto): as regras deles vivem agora em `source/data/validacao.py`.
"""
import dataclasses
import json
import os
import subprocess
import sys

import pytest

from source.data import validacao
from source.data.enemy_data import DROP_PADRAO, INIMIGOS, PerfilInimigo, _fixo
from source.data.manifesto_assets import Imagem
from source.data.validacao import (validar_armas, validar_inimigos, validar_manifesto, validar_mapas,
                                   validar_motor_de_bosses, validar_spawner, validar_tudo)
from source.data.weapon_data import COMPANION_DATA, VEHICLES_DATA, WEAPON_DATA, WeaponProfile, WeaponStats
from source.enemies.base.boss import BossBase, Clip, FaseBoss
from source.enemies.standard.grunt import GruntRed
from source.systems.levelup.constants import (ARMAS_REGISTRO, NIVEL_MAXIMO_POR_RARIDADE,
                                              PESO_SORTEIO_POR_RARIDADE)
from source.systems.spawner.spawner_bosses import BOSS_CLASSES, CRONOGRAMA_BOSSES, PHASE_BOSSES


def test_dados_do_jogo_sao_validos():
    assert validar_tudo() == []


def test_validar_nao_inicia_o_pygame():
    # Roda na abertura do jogo (MCE_DEBUG) e na suíte: não pode depender de display.
    codigo = ('import pygame\n'
              'from source.data.validacao import validar_tudo\n'
              'print(len(validar_tudo()), pygame.get_init())')
    feito = subprocess.run([sys.executable, '-c', codigo], capture_output=True, text=True, timeout=120,
                           env={**os.environ, 'SDL_VIDEODRIVER': 'dummy',
                                'PYGAME_HIDE_SUPPORT_PROMPT': '1'})
    assert feito.returncode == 0, feito.stderr
    assert feito.stdout.split() == ['0', 'False']


def um_erro(erros, trecho):
    """Exatamente um erro, e ele fala do que foi quebrado."""
    assert len(erros) == 1, erros
    assert trecho in erros[0], erros[0]


# ------------------------------------------------------------------ #
# Armas
# ------------------------------------------------------------------ #
def _armas(**trocas):
    dados = {'armas': WEAPON_DATA, 'companheiros': COMPANION_DATA, 'veiculos': VEHICLES_DATA,
             'registro': ARMAS_REGISTRO}
    dados.update(trocas)
    return validar_armas(**dados)


def test_nome_repetido_entre_categorias():
    um_erro(_armas(veiculos={**VEHICLES_DATA, 'assault_rifle': WEAPON_DATA['assault_rifle']}),
            '"assault_rifle" está em armas e em veículos')


def test_stat_que_nao_e_weaponstats():
    perfil = WeaponProfile(stats={**WEAPON_DATA['assault_rifle'].stats, 'dano': 5})
    um_erro(_armas(armas={**WEAPON_DATA, 'assault_rifle': perfil}), 'assault_rifle.dano não é WeaponStats')


def test_stat_que_diminui_sem_piso():
    stats = dict(WEAPON_DATA['assault_rifle'].stats)
    stats['cooldown'] = dataclasses.replace(stats['cooldown'], min_val=None)
    um_erro(_armas(armas={**WEAPON_DATA, 'assault_rifle': WeaponProfile(stats=stats)}),
            'assault_rifle.cooldown diminui a cada nível e não tem min_val')


def test_stat_sem_label_pode_diminuir_sem_piso():
    # Sem label o stat não aparece no level-up: a regra antiga também o ignorava.
    stats = {'x': WeaponStats(value=10, increase=-1, range_val=2)}
    assert _armas(armas={**WEAPON_DATA, 'teste': WeaponProfile(stats=stats)}) == []


@pytest.mark.parametrize('troca, trecho', [
    ({'id': 'outro'}, 'id "outro" diferente da chave'),
    ({'raridade': 'mitica'}, 'raridade "mitica" fora de PALETA_RARIDADE'),
])
def test_registro_invalido(troca, trecho):
    info = dataclasses.replace(ARMAS_REGISTRO['assault_rifle'], **troca)
    um_erro(_armas(registro={**ARMAS_REGISTRO, 'assault_rifle': info}), trecho)


@pytest.mark.parametrize('dicionario, troca, trecho', [
    ('niveis_maximos', {'mitica': 3}, '"mitica": sobra em NIVEL_MAXIMO_POR_RARIDADE'),
    ('niveis_maximos', {'rara': None}, '"rara": falta em NIVEL_MAXIMO_POR_RARIDADE'),
    ('niveis_maximos', {'rara': 0}, 'nível máximo 0'),
    ('niveis_maximos', {'rara': 2.5}, 'nível máximo 2.5'),
    ('niveis_maximos', {'rara': True}, 'nível máximo True'),
    ('pesos', {'epica': None}, '"epica": falta em PESO_SORTEIO_POR_RARIDADE'),
    ('pesos', {'epica': 0}, 'peso no sorteio 0'),
    ('pesos', {'epica': -5}, 'peso no sorteio -5'),
    ('pesos', {'epica': float('nan')}, 'peso no sorteio nan'),
    ('pesos', {'epica': float('inf')}, 'peso no sorteio inf'),
    ('pesos', {'epica': '10'}, "peso no sorteio '10'"),
])
def test_raridade_invalida(dicionario, troca, trecho):
    # roteiro E6: nível máximo e peso de sorteio por raridade
    original = {'niveis_maximos': NIVEL_MAXIMO_POR_RARIDADE, 'pesos': PESO_SORTEIO_POR_RARIDADE}[dicionario]
    dic = {**original, **troca}
    dic = {k: v for k, v in dic.items() if v is not None}
    um_erro(_armas(**{dicionario: dic}), trecho)


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


def test_min_val_exato_no_ultimo_nivel_vale():
    assert _armas(armas=_brick_com_cooldown(increase=-250)) == []          # 2000 - 4 × 250 = 1000


def test_min_val_depende_do_maximo_da_raridade():
    # o mesmo dado bate se a raridade tiver mais níveis (lendária com 11: 10 subidas de -100)
    # (registro só com o Brick: as outras lendárias não batem com 11 níveis)
    niveis = {**NIVEL_MAXIMO_POR_RARIDADE, 'lendaria': 11}
    so_brick = {'brick': ARMAS_REGISTRO['brick']}
    assert _armas(armas=_brick_com_cooldown(increase=-100), registro=so_brick, niveis_maximos=niveis) == []
    um_erro(_armas(armas=_brick_com_cooldown(increase=-250), registro=so_brick, niveis_maximos=niveis),
            '× 10 = -500: passa dele e trava')


def test_min_val_conta_so_os_niveis_do_range_val():
    # a cada 2 níveis até o 5: sobe nos níveis 2 e 4 (2 subidas) -> 2000 - 2 × 500 = 1000
    assert _armas(armas=_brick_com_cooldown(increase=-500, range_val=2)) == []
    um_erro(_armas(armas=_brick_com_cooldown(increase=-250, range_val=2)), '× 2 = 1500: nunca chega a ele')


def test_arma_registrada_sem_perfil_de_dados():
    sem_perfil = {k: v for k, v in WEAPON_DATA.items() if k != 'assault_rifle'}
    um_erro(_armas(armas=sem_perfil), 'NOME_ASSET "assault_rifle" sem perfil em weapon_data')


# ------------------------------------------------------------------ #
# Spawner
# ------------------------------------------------------------------ #
POOL_OK = {'classes': [GruntRed], 'pesos': [1]}


def _spawner(**trocas):
    dados = {'pools': {0: POOL_OK}, 'pool_padrao': POOL_OK, 'bosses_por_fase': PHASE_BOSSES,
             'classes_de_boss': BOSS_CLASSES, 'cronograma': CRONOGRAMA_BOSSES}
    dados.update(trocas)
    return validar_spawner(**dados)


def test_spawner_valido():
    assert _spawner() == []


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


def test_pool_padrao_tambem_e_validado():
    um_erro(_spawner(pool_padrao={'classes': [GruntRed], 'pesos': [-1]}), 'pool da fase padrão: peso -1')


@pytest.mark.parametrize('dicionario', ['classes_de_boss', 'cronograma'])
def test_boss_fora_de_um_dos_tres_dicts(dicionario):
    original = {'classes_de_boss': BOSS_CLASSES, 'cronograma': CRONOGRAMA_BOSSES}[dicionario]
    sem_hunter = {k: v for k, v in original.items() if k != 'hunter'}
    nome_dict = {'classes_de_boss': 'BOSS_CLASSES', 'cronograma': 'CRONOGRAMA_BOSSES'}[dicionario]
    um_erro(_spawner(**{dicionario: sem_hunter}), f'boss "hunter": falta em {nome_dict}')


def test_boss_sem_fase():
    fases = {f: [n for n in nomes if n != 'atriox'] for f, nomes in PHASE_BOSSES.items()}
    um_erro(_spawner(bosses_por_fase=fases), 'boss "atriox": falta em PHASE_BOSSES')


def test_horario_de_boss_invalido():
    um_erro(_spawner(cronograma={**CRONOGRAMA_BOSSES, 'hunter': 0}), 'boss "hunter": horário 0')


def test_cronograma_fora_da_ordem_das_fases():
    um_erro(_spawner(cronograma={**CRONOGRAMA_BOSSES, 'zealot': 30}),
            'boss "zealot" (fase 1, 30 s) vem antes de "hunter"')


# ------------------------------------------------------------------ #
# Motor de bosses (F1)
# ------------------------------------------------------------------ #
def _boss(**atributos):
    """Classe de boss sobre a BossBase com os atributos trocados (não é instanciada)."""
    base = {'FASES': (FaseBoss('A', 1.0, 1.0, 1.0), FaseBoss('B', 0.5, 1.0, 1.0)),
            'COOLDOWNS': {'golpe': (1000, 2000)}, 'COOLDOWN_INICIAL': {'golpe': 500}}
    return validar_motor_de_bosses({'teste': type('BossTeste', (BossBase,), {**base, **atributos})})


def test_motor_de_bosses_valido():
    assert _boss() == []
    assert validar_motor_de_bosses() == []


def test_motor_ignora_boss_fora_da_base():
    assert validar_motor_de_bosses({'grunt': GruntRed, 'lixo': 3}) == []


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


@pytest.mark.parametrize('faixa', [(2000, 1000), (-1, 10), (1.5, 10), [1000, 2000], (1000,), (True, 10)])
def test_faixa_de_cooldown_invalida(faixa):
    um_erro(_boss(COOLDOWNS={'golpe': faixa}), 'cooldown de "golpe"')


def test_cooldown_inicial_sem_faixa():
    um_erro(_boss(COOLDOWN_INICIAL={'golpe': 500, 'outro': 100}), 'cooldown inicial de "outro" sem faixa')


@pytest.mark.parametrize('ms', [-1, 1.5, '500'])
def test_cooldown_inicial_invalido(ms):
    um_erro(_boss(COOLDOWN_INICIAL={'golpe': ms}), f'cooldown inicial de "golpe" {ms!r}')


@pytest.mark.parametrize('clips', [{}, None, {'andar': 200}, [Clip(200)], {'andar': Clip(200), 'x': (1, 2)}])
def test_clips_invalidos(clips):
    um_erro(_boss(CLIPS=clips, CLIP_INICIAL='andar'), 'CLIPS precisa ser um dict não vazio')


def test_clip_inicial_fora_dos_clips():
    um_erro(_boss(CLIPS={'andar': Clip(200)}, CLIP_INICIAL='correr'), 'CLIP_INICIAL "correr" não está em CLIPS')


# ------------------------------------------------------------------ #
# Inimigos comuns
# ------------------------------------------------------------------ #
def _inimigo(**campos):
    return validar_inimigos({'teste': dataclasses.replace(INIMIGOS['grunt_red'], **campos)})


def test_perfil_valido():
    assert _inimigo() == []


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


def test_drop_com_quantidade_variavel_valido():
    assert _inimigo(drops=_fixo({'exp_shard': ((1, 2, 3), (70, 20, 10), 100)})) == []


def test_perfil_que_nao_e_perfilinimigo():
    um_erro(validar_inimigos({'teste': {'vida': 1}}), 'não é PerfilInimigo')


def test_perfil_construido_direto_tambem_e_validado():
    um_erro(validar_inimigos({'teste': PerfilInimigo(1, 1, -5)}), 'velocidade -5')


# ------------------------------------------------------------------ #
# Manifesto
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


def test_manifesto_valido_com_repeticao():
    assert validar_manifesto({'a': Imagem('player/player1.png'), 'b': [Imagem('player/player1.png')]}) == []


# ------------------------------------------------------------------ #
# Mapas
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


def test_mapa_minimo_e_valido(mapa_falso):
    # Sem SpawnPlayer nem Portal: o jogo usa o centro do mapa
    assert mapa_falso(_tmj(MAPA_OK)) == []


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


@pytest.mark.parametrize('conteudo', ['{nao e json', {'layers': []}, _tmj([{'name': 'Colisoes'}])])
def test_tmj_ilegivel(mapa_falso, conteudo):
    um_erro(mapa_falso(conteudo), '.tmj ilegível')


def test_tmj_ausente(tmp_path, monkeypatch):
    monkeypatch.setattr(validacao, 'caminho_do_mapa', lambda chave: str(tmp_path / 'nao_existe.tmj'))
    um_erro(validar_mapas(['0']), '.tmj ilegível')


def test_fase_com_mapa_sem_pool_ou_boss(mapa_falso, monkeypatch):
    monkeypatch.setattr(validacao, 'PHASE_POOLS', {})
    monkeypatch.setattr(validacao, 'PHASE_BOSSES', {})
    erros = mapa_falso(_tmj(MAPA_OK))
    assert erros == ['mapa 0: fase 0 sem pool em PHASE_POOLS', 'mapa 0: fase 0 sem boss em PHASE_BOSSES']


# ------------------------------------------------------------------ #
# Abertura do jogo
# ------------------------------------------------------------------ #
@pytest.mark.parametrize('debug', ['1', '0'])
def test_main_valida_os_dados_so_com_mce_debug(debug):
    codigo = ('import main\n'
              'from source.game import Game\n'
              'Game.run = lambda self: None\n'   # só a abertura, sem o loop
              'main.main()\n')
    ambiente = {**os.environ, 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy',
                'PYGAME_HIDE_SUPPORT_PROMPT': '1', 'PYTHONIOENCODING': 'utf-8', 'MCE_DEBUG': debug}
    feito = subprocess.run([sys.executable, '-c', codigo], capture_output=True, text=True, timeout=120,
                           env=ambiente, encoding='utf-8')
    assert feito.returncode == 0, feito.stderr
    linhas = [linha for linha in feito.stdout.splitlines() if linha.startswith('[Valida')]
    assert linhas == (['[Validação] 0 erro(s) nos dados do jogo'] if debug == '1' else [])
