"""Golden master (roteiro A3): 60 s da fase 0 com seed fixa e jogador blindado, comparados
segundo a segundo com tests/golden/fase0.json.

Uma refatoração "sem mudança de comportamento" passa aqui SEM regerar o arquivo (roteiro §2,
regra 4). Mudança de comportamento declarada regera de propósito, com o motivo no log:
    .venv\\Scripts\\python.exe -m pytest tests/integration/test_golden.py --atualizar-golden
Só o update entra (o draw não pode mudar a simulação); o jogador não recebe input.
"""
import json
import os
import random

import pytest

from helpers import DT, blindar_jogador, voltar_ao_menu
from source.systems.entitymanager import entity_manager
from source.systems.entrada import ComandoJogador, Roteiro

CAMINHO_GOLDEN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              'golden', 'fase0.json')
PARAMETROS = {'cenario': 'fase0', 'seed': 1234, 'segundos': 60, 'dt': DT}
CASAS = 3   # floats arredondados: o arquivo fica legível e a comparação, exata


# ------------------------------------------------------------------ #
def _amostra(game, segundo):
    p = game.player
    return {
        't': segundo,
        'inimigos': len(entity_manager.inimigos_grupo),
        'projeteis_jogador': len(entity_manager.projeteis_jogador_grupo),
        'projeteis_inimigos': len(entity_manager.projeteis_inimigos_grupo),
        'itens': len(entity_manager.items_grupo),
        'vida': round(p.vida_atual, CASAS),
        'escudo': round(p.escudo_atual, CASAS),
        'xp': round(p.experiencia_atual, CASAS),
        'nivel': p.contador_niveis,
        'pontuacao': p.pontuacao,
        'x': round(p.posicao.x, CASAS),
        'y': round(p.posicao.y, CASAS),
    }


def simular_golden(game, segundos=PARAMETROS['segundos'], roteiro=None):
    """Partida nova da fase 0 e uma amostra por segundo de jogo (a do segundo 0 inclusa).
    Sem `roteiro`, a fonte é o Teclado (nada pressionado no SDL dummy)."""
    random.seed(PARAMETROS['seed'])
    voltar_ao_menu(game)
    game.iniciar_novo_jogo()
    game.renderer._erros_logados.clear()
    blindar_jogador(game.player)
    entrada_original = game.entrada
    if roteiro is not None:
        roteiro.reiniciar()
        game.entrada = roteiro
    try:
        quadros_por_segundo = round(1 / DT)
        amostras = [_amostra(game, 0)]
        for segundo in range(1, segundos + 1):
            for _ in range(quadros_por_segundo):
                game.update(DT)
            amostras.append(_amostra(game, segundo))
        assert game.estado_do_jogo == 'jogando', 'a simulação parou: o golden não valeria'
    finally:
        game.entrada = entrada_original
        voltar_ao_menu(game)
    return {**PARAMETROS, 'segundos': segundos, 'amostras': amostras}


# ------------------------------------------------------------------ #
def carregar_golden(caminho):
    """Golden gravado, ou None se não existir. Arquivo inválido é erro (nunca é ignorado)."""
    if not os.path.exists(caminho):
        return None
    try:
        with open(caminho, encoding='utf-8') as f:
            golden = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise ValueError(f'golden ilegível em {caminho}: {e}') from e
    if not isinstance(golden, dict) or not isinstance(golden.get('amostras'), list):
        raise ValueError(f'golden sem a lista "amostras" em {caminho}')
    return golden


def salvar_golden(golden, caminho):
    """Uma amostra por linha: o diff de uma regeneração mostra quais segundos mudaram."""
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    cabecalho = ''.join(f' {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)},\n'
                        for k, v in golden.items() if k != 'amostras')
    amostras = ',\n'.join(f'  {json.dumps(a, ensure_ascii=False)}' for a in golden['amostras'])
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(f'{{\n{cabecalho} "amostras": [\n{amostras}\n ]\n}}\n')


def primeira_divergencia(esperado, obtido):
    """Descrição da primeira diferença (parâmetro, quantidade de amostras ou métrica no segundo
    t), ou None se forem iguais."""
    for chave in PARAMETROS:
        if esperado.get(chave) != obtido.get(chave):
            return f'parâmetro {chave}: golden {esperado.get(chave)!r}, agora {obtido.get(chave)!r}'
    for amostra_esp, amostra_obt in zip(esperado['amostras'], obtido['amostras']):
        for metrica in sorted(amostra_esp.keys() | amostra_obt.keys()):
            if amostra_esp.get(metrica) != amostra_obt.get(metrica):
                return (f't={amostra_esp.get("t")} s, {metrica}: golden '
                        f'{amostra_esp.get(metrica)!r}, agora {amostra_obt.get(metrica)!r}')
    if len(esperado['amostras']) != len(obtido['amostras']):
        return (f'amostras: golden tem {len(esperado["amostras"])}, '
                f'agora {len(obtido["amostras"])}')
    return None


# ------------------------------------------------------------------ #
@pytest.fixture(scope='module')
def primeira_rodada(game):
    return simular_golden(game)


@pytest.mark.integration
def test_fase0_bate_com_o_golden(request, primeira_rodada):
    if request.config.getoption('--atualizar-golden'):
        salvar_golden(primeira_rodada, CAMINHO_GOLDEN)
        pytest.skip(f'golden regravado em {CAMINHO_GOLDEN}: registre o motivo em docs/log.md')
    esperado = carregar_golden(CAMINHO_GOLDEN)
    assert esperado is not None, f'{CAMINHO_GOLDEN} não existe: rode com --atualizar-golden'
    divergencia = primeira_divergencia(esperado, primeira_rodada)
    assert divergencia is None, (
        f'a simulação mudou ({divergencia}). Refatoração: ache a causa. Mudança de '
        'comportamento declarada: rode com --atualizar-golden e registre no log.')


def _roteiro_de_teste():
    """20 s: anda nas 4 direções e na diagonal, para, chama o veículo (sem veículo equipado)."""
    s = round(1 / DT)   # passos por segundo
    return Roteiro([
        (2 * s, ComandoJogador(direcao=(1, 0))),
        (2 * s, ComandoJogador(direcao=(0, 1))),
        (3 * s, ComandoJogador(direcao=(-1, -1))),
        (1 * s, ComandoJogador()),
        (5, ComandoJogador(veiculo=True)),
        (2 * s, ComandoJogador(direcao=(0, -1))),
        (4 * s, ComandoJogador(direcao=(-1, 1))),
    ])


@pytest.mark.integration
def test_replay_de_um_roteiro_e_deterministico(game, primeira_rodada):
    """Roteiro E3: o mesmo roteiro dá a mesma partida 2x, e o comando chega de fato ao jogador
    (a posição sai da do golden sem input já no 1º segundo)."""
    a = simular_golden(game, 20, _roteiro_de_teste())
    b = simular_golden(game, 20, _roteiro_de_teste())
    assert primeira_divergencia(a, b) is None
    sem_input = primeira_rodada['amostras'][1]
    assert (a['amostras'][1]['x'], a['amostras'][1]['y']) != (sem_input['x'], sem_input['y'])
