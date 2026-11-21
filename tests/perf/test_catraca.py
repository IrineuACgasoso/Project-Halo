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

import pygame
import pytest

from helpers import DT, blindar_jogador, contar_alocacoes, ir_para_fase
from source.systems.entitymanager import entity_manager
from source.systems.spawner.spawner_bosses import PHASE_BOSSES

TAMANHO_HORDA = 150
AQUECIMENTO_S = 1     # caches de sprite/HUD se enchem aqui, fora da conta
FOLGA_AVISO = 0.10    # medida 10% abaixo do teto: avisa para baixar o teto

# Alocações por frame (update + draw) medidas na A2. Só podem descer.
TETOS = {
    'horda_150': 20.0,
    'fase0': 8.2,
    'boss_hunter': 9.1,
    'boss_zealot': 9.3,
    'boss_guilty': 10.1,
    'boss_scarab': 10.1,
    'boss_arbiter': 9.2,
    'boss_tartarus': 9.6,
    'boss_gravemind': 9.6,
    'boss_knight': 9.1,
    'boss_didact': 10.1,
    'boss_warden': 12.0,
    'boss_guardian': 9.4,
    'boss_jega': 9.1,
    'boss_escharum': 10.3,
    'boss_harbinger': 9.2,
    'boss_atriox': 9.6,
}


# ------------------------------------------------------------------ #
# O contador
# ------------------------------------------------------------------ #
def test_contador_conta_cada_tipo():
    base = pygame.Surface((4, 4))
    with contar_alocacoes() as c:
        s = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.mask.from_surface(s)
        pygame.transform.scale(s, (2, 2))
        pygame.transform.flip(s, True, False)
        pygame.font.Font(None, 12)
    assert c.por_tipo == {'Surface': 1, 'mask.from_surface': 1, 'transform.scale': 1,
                          'transform.flip': 1, 'font.Font': 1}
    assert c.total == 5
    assert isinstance(base, pygame.Surface)


def test_surface_contada_e_surface_de_verdade():
    antiga = pygame.Surface((2, 2))
    with contar_alocacoes():
        nova = pygame.Surface((3, 3))
        assert type(nova) is type(antiga)
        assert isinstance(antiga, pygame.Surface)   # criada antes do patch
        assert isinstance(nova, pygame.Surface)
        assert issubclass(type(antiga), pygame.Surface)
        assert not isinstance(object(), pygame.Surface)


def test_transform_sem_alocacao_nao_conta():
    s = pygame.Surface((4, 4))
    with contar_alocacoes() as c:
        pygame.transform.average_color(s)
        pygame.transform.get_smoothscale_backend()
    assert c.total == 0


def test_trecho_pausado_nao_conta():
    with contar_alocacoes() as c:
        with c.pausado():
            pygame.Surface((1, 1))
        pygame.Surface((1, 1))
    assert c.total == 1


def test_pausa_aninhada_nao_reativa_a_externa():
    with contar_alocacoes() as c:
        with c.pausado():
            with c.pausado():
                pygame.Surface((1, 1))
            pygame.Surface((1, 1))   # ainda dentro da pausa externa
        pygame.Surface((1, 1))
    assert c.total == 1


def test_restaura_pygame_ao_sair_mesmo_com_erro():
    originais = (pygame.Surface, pygame.mask.from_surface, pygame.transform.scale,
                 pygame.font.Font, pygame.font.SysFont)
    with pytest.raises(RuntimeError):
        with contar_alocacoes() as c:
            with c.pausado():
                raise RuntimeError('falha no meio')
    assert (pygame.Surface, pygame.mask.from_surface, pygame.transform.scale,
            pygame.font.Font, pygame.font.SysFont) == originais
    assert c.ativo   # o pausado também se desfaz no erro


# ------------------------------------------------------------------ #
# Cenários fixos
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


@pytest.mark.integration
def test_alocacao_nova_no_frame_aparece_na_medida(novo_jogo, monkeypatch):
    """A catraca pega o caso típico: alguém cria uma Surface por frame no HUD."""
    blindar_jogador(novo_jogo.player)
    novo_jogo.spawner.update = lambda dt: None   # mesma cena nas duas medidas
    sem, _ = _medir_por_frame(novo_jogo, 0.5)
    draw_original = novo_jogo.hud.draw

    def draw_com_vazamento(tela):
        pygame.Surface((10, 10), pygame.SRCALPHA)
        draw_original(tela)

    monkeypatch.setattr(novo_jogo.hud, 'draw', draw_com_vazamento)
    com, por_tipo = _medir_por_frame(novo_jogo, 0.5)
    assert com - sem == pytest.approx(1.0), por_tipo


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
    if por_frame < teto * (1 - FOLGA_AVISO):
        warnings.warn(f'{nome} melhorou ({detalhe}): baixe o teto para '
                      f'{_teto_sugerido(por_frame):.1f}', stacklevel=1)
