"""Catraca de alocação (roteiro A2): o número de Surfaces/máscaras/fontes criadas por frame
não pode subir. Contagem é determinística (diferente de tempo), então vira asserção.

Como mexer nos tetos:
  - piorou (falhou): ache a alocação nova e ponha em cache; o teto NÃO sobe;
  - melhorou (aviso "baixe o teto"): troque o teto pelo valor sugerido no mesmo commit;
  - boss novo: o teste falha com a medida; grave o teto sugerido em TETOS.
Regra de arredondamento: teto = medida truncada em 0,1 + 0,1 (folga de 0,05 a 0,1 por frame,
acima da sobra de cache de módulo vista na A2: até 2 chamadas em 180 frames).
"""
import math
import warnings

import pytest

from helpers import DT, blindar_jogador, contar_alocacoes, ir_para_fase
from source.systems.entitymanager import entity_manager
from source.systems.spawner.spawner_bosses import PHASE_BOSSES

TAMANHO_HORDA = 150
AQUECIMENTO_S = 1     # caches de sprite/HUD se enchem aqui, fora da conta
FOLGA_AVISO = 0.10    # medida 10% abaixo do teto: avisa para baixar o teto

# Alocações por frame (update + draw). Medidas na A2; baixadas na C3 (máscaras e efeitos em
# cache: horda 20,0 -> 8,0) e na C4 (HUD sem Surface: ~0). O que sobra é aquecimento de cache
# (ângulo novo de projétil, base nova de partícula) e o Gravemind (F2/F5). Só podem descer.
TETOS = {
    'horda_150': 0.1,
    'fase0': 0.1,
    'boss_hunter': 0.1,
    'boss_zealot': 0.1,
    'boss_guilty': 0.1,
    'boss_scarab': 0.1,
    'boss_arbiter': 0.1,
    'boss_tartarus': 0.1,
    'boss_gravemind': 0.7,
    'boss_knight': 0.1,
    'boss_didact': 0.1,
    'boss_warden': 0.1,
    'boss_guardian': 0.1,
    'boss_jega': 0.1,
    'boss_escharum': 0.1,
    'boss_harbinger': 0.1,
    'boss_atriox': 0.1,
}


# ------------------------------------------------------------------ #
def _medir_por_frame(game, segundos, antes_do_frame=None):
    """Aquece AQUECIMENTO_S e conta as alocações de `segundos` de update + draw."""
    def frame():
        if antes_do_frame:
            with contador.pausado():
                antes_do_frame()
        game.update(DT)
        game.draw()

    with contar_alocacoes() as contador:
        with contador.pausado():
            for _ in range(round(AQUECIMENTO_S / DT)):
                frame()
        frames = round(segundos / DT)
        for _ in range(frames):
            frame()
    assert game.estado_do_jogo == 'jogando', 'a simulação parou: a medida não valeria'
    assert game.renderer._erros_logados == set()
    return contador.total / frames, contador.por_tipo


def _horda(game):
    """Horda constante (o gargalo do perf). Repor a horda não é custo do frame."""
    game.spawner.update = lambda dt: None

    def repor():
        while len(entity_manager.inimigos_grupo) < TAMANHO_HORDA:
            game.spawner.spawnar('normal')

    repor()
    return _medir_por_frame(game, 3, repor)


def _fase0(game):
    return _medir_por_frame(game, 5)


def _boss(game, nome, fase):
    ir_para_fase(game, fase)
    game.spawner.spawnar(nome)
    return _medir_por_frame(game, 2)


CENARIOS = [('horda_150', _horda), ('fase0', _fase0)] + [
    (f'boss_{nome}', lambda game, nome=nome, fase=fase: _boss(game, nome, fase))
    for fase, nomes in sorted(PHASE_BOSSES.items()) for nome in nomes]


def _teto_sugerido(por_frame):
    return math.floor(por_frame * 10) / 10 + 0.1


def test_todo_teto_tem_cenario():
    assert set(TETOS) == {nome for nome, _ in CENARIOS}, 'teto sem cenário ou cenário sem teto'


@pytest.mark.integration
@pytest.mark.parametrize('nome,cenario', CENARIOS, ids=[n for n, _ in CENARIOS])
def test_alocacoes_por_frame_nao_sobem(novo_jogo, nome, cenario):
    blindar_jogador(novo_jogo.player)
    por_frame, por_tipo = cenario(novo_jogo)
    detalhe = f'{por_frame:.2f}/frame; por tipo: {dict(por_tipo.most_common())}'

    teto = TETOS.get(nome)
    assert teto is not None, f'{nome} sem teto: medido {detalhe}; grave {_teto_sugerido(por_frame):.1f}'
    assert por_frame <= teto, (f'{nome} alocou mais que o teto {teto}: {detalhe}. '
                               'Ponha a alocação nova em cache; o teto não sobe.')
    # Só avisa se o teto pode mesmo descer (perto de zero, o mínimo pela regra é 0,1).
    if por_frame < teto * (1 - FOLGA_AVISO) and _teto_sugerido(por_frame) < teto:
        warnings.warn(f'{nome} melhorou ({detalhe}): baixe o teto para '
                      f'{_teto_sugerido(por_frame):.1f}', stacklevel=1)
