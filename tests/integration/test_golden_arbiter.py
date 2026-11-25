"""Golden master do Arbiter (roteiro F1): 60 s de luta na fase 4 com seed fixa, jogador blindado
andando por um Roteiro e a vida do boss forçada abaixo dos limiares (passa pelas 3 fases).
Gravado ANTES da extração da BossBase: a refatoração passa aqui sem regerar o arquivo.
    .venv\\Scripts\\python.exe -m pytest tests/integration/test_golden_arbiter.py --atualizar-golden
"""
import os
import random

import pytest

from helpers import DT, blindar_jogador, ir_para_fase, voltar_ao_menu
from source.systems.entitymanager import entity_manager
from source.systems.entrada import ComandoJogador, Roteiro
from test_golden import carregar_golden, primeira_divergencia, salvar_golden

CAMINHO_GOLDEN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              'golden', 'arbiter.json')
PARAMETROS = {'cenario': 'arbiter', 'seed': 4321, 'segundos': 60, 'dt': DT}
CASAS = 3
# segundo -> fração da vida máxima imposta ao boss (0,55 segue na fase 1; 0,25 passa do limiar 0,40)
VIDA_FORCADA = {20: 0.55, 40: 0.25}


def _roteiro():
    """Circula o boss: ele precisa strafar, antecipar a mira e recalcular a distância."""
    s = round(1 / DT)
    return Roteiro([
        (3 * s, ComandoJogador(direcao=(1, 0))),
        (2 * s, ComandoJogador(direcao=(0, 1))),
        (3 * s, ComandoJogador(direcao=(-1, 0))),
        (2 * s, ComandoJogador()),
        (2 * s, ComandoJogador(direcao=(0, -1))),
        (3 * s, ComandoJogador(direcao=(1, 1))),
        (3 * s, ComandoJogador(direcao=(-1, -1))),
        (2 * s, ComandoJogador()),
    ] * 3)


def _amostra(game, boss, t):
    p = game.player
    return {
        't': t,
        'boss_vivo': boss.alive(),
        'x': round(boss.posicao.x, CASAS),
        'y': round(boss.posicao.y, CASAS),
        'vida': round(boss.vida, CASAS),
        'escudo': round(boss.escudo_atual, CASAS),
        'fase': boss.fase,
        'estado': boss.estado_habilidade,
        'ultima': boss.ultima_habilidade,
        'wait': round(boss.wait, CASAS),
        'cd': {k: round(v, CASAS) for k, v in sorted(boss.cd.items())},
        'invis': boss.fase_invisibilidade,
        # animação (F2): o quadro mostrado, o lado e o alpha da imagem (camuflagem)
        'quadro': boss.animador.quadro,
        'lado': boss.animador.lado,
        'alpha': boss.image.get_alpha(),
        'elites': len([e for e in boss.elites_invocados if e.alive()]),
        'inimigos': len(entity_manager.inimigos_grupo),
        'projeteis_inimigos': len(entity_manager.projeteis_inimigos_grupo),
        # soma das posições dos ataques do boss na tela: pega mudança de mira, não só de contagem
        'ataques_xy': round(sum(s.posicao.x + s.posicao.y for s in entity_manager.all_sprites
                                if getattr(s, 'fonte', None) is boss and hasattr(s, 'posicao')), CASAS),
        # sem as partículas: são só visuais e sorteiam por conta própria (regra de VFX)
        'sprites': len(entity_manager.all_sprites) - len(entity_manager.particulas_grupo),
        'jogador_vida': round(p.vida_atual, CASAS),
        'jogador_escudo': round(p.escudo_atual, CASAS),
        'jogador_x': round(p.posicao.x, CASAS),
        'jogador_y': round(p.posicao.y, CASAS),
    }


def simular_arbiter(game):
    random.seed(PARAMETROS['seed'])
    voltar_ao_menu(game)
    game.iniciar_novo_jogo()
    game.renderer._erros_logados.clear()
    ir_para_fase(game, 4)
    blindar_jogador(game.player)
    game.spawner.spawnar('arbiter')
    boss = game.sessao.boss_atual
    entrada_original = game.entrada
    game.entrada = _roteiro()
    try:
        meio_segundo = round(0.5 / DT)
        amostras = [_amostra(game, boss, 0)]
        for i in range(1, PARAMETROS['segundos'] * 2 + 1):
            t = i / 2
            if t - 0.5 in VIDA_FORCADA:
                boss.vida = boss.vida_maxima * VIDA_FORCADA[t - 0.5]
            for _ in range(meio_segundo):
                game.update(DT)
            amostras.append(_amostra(game, boss, t))
        assert game.estado_do_jogo == 'jogando', 'a simulação parou: o golden não valeria'
    finally:
        game.entrada = entrada_original
        voltar_ao_menu(game)
    return {**PARAMETROS, 'amostras': amostras}


@pytest.fixture(scope='module')
def rodada(game):
    return simular_arbiter(game)


@pytest.mark.integration
def test_arbiter_bate_com_o_golden(request, rodada):
    if request.config.getoption('--atualizar-golden'):
        salvar_golden(rodada, CAMINHO_GOLDEN)
        pytest.skip(f'golden regravado em {CAMINHO_GOLDEN}: registre o motivo em docs/log.md')
    esperado = carregar_golden(CAMINHO_GOLDEN)
    assert esperado is not None, f'{CAMINHO_GOLDEN} não existe: rode com --atualizar-golden'
    divergencia = primeira_divergencia(esperado, rodada)
    assert divergencia is None, (
        f'a luta do Arbiter mudou ({divergencia}). Refatoração: ache a causa. Mudança de '
        'comportamento declarada: rode com --atualizar-golden e registre no log.')
