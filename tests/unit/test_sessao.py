"""Sessão separada do Game (roteiro B3): cada partida é um objeto novo, nada sobra da anterior."""
import dataclasses
import os
import re

from helpers import DT, voltar_ao_menu
from source.systems.gameclock import _OFFSET_INICIAL_MS, relogio
from source.systems.sessao import SessaoJogo

RAIZ_SOURCE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), 'source')
CAMPOS = [c.name for c in dataclasses.fields(SessaoJogo)]
GRUPOS = ('all_sprites', 'inimigos_grupo', 'projeteis_jogador_grupo', 'projeteis_inimigos_grupo',
          'items_grupo', 'auras_grupo')


def _sujar_partida(game):
    """Deixa a partida com estado em todos os campos da sessão e nos tempos."""
    s = game.sessao
    s.timer_jogo = 123.0
    s.fase_atual = 4
    game.spawner.spawnar('hunter')
    s.portal_atual = object()
    s.spawnar_portal_em_breve = True
    s.timer_portal = 999
    s.tela_de_upgrade_ativa = object()
    s.gravemind_reborns = 0
    relogio.avancar(30)
    game.hud._atualizar_boss_foco()
    assert game.hud.foco_barra_vida is not None


def test_sessao_nova_comeca_nos_valores_padrao():
    s = SessaoJogo()
    assert (s.timer_jogo, s.fase_atual, s.boss_atual, s.portal_atual) == (0.0, 0, None, None)
    assert not s.spawnar_portal_em_breve and s.tela_de_upgrade_ativa is None
    assert s.gravemind_reborns == 3


def test_duas_partidas_nao_compartilham_nada(novo_jogo):
    game = novo_jogo
    antes = {'sessao': game.sessao, 'hud': game.hud, 'player': game.player, 'mapa': game.mapa,
             'camera': game.camera, 'spawner': game.spawner, 'stage_manager': game.stage_manager}
    _sujar_partida(game)

    voltar_ao_menu(game)
    game.iniciar_novo_jogo()

    for nome, objeto in antes.items():
        assert getattr(game, nome) is not objeto, f'{nome} sobrou da partida anterior'
    assert game.sessao == SessaoJogo()
    for campo in CAMPOS:   # nenhum valor da sessão velha (mutável ou não) foi reaproveitado
        velho = getattr(antes['sessao'], campo)
        if velho is not None and not isinstance(velho, (bool, int, float)):
            assert getattr(game.sessao, campo) is not velho, campo


def test_partida_nova_zera_relogio_e_hud(novo_jogo):
    _sujar_partida(novo_jogo)
    voltar_ao_menu(novo_jogo)
    novo_jogo.iniciar_novo_jogo()
    assert relogio.agora() == _OFFSET_INICIAL_MS
    assert novo_jogo.hud.foco_barra_vida is None and novo_jogo.hud._ultimo_check_boss == 0


def test_partida_suja_nao_atrapalha_a_seguinte(novo_jogo):
    """Portal, boss e tela de upgrade da partida anterior não aparecem na nova."""
    _sujar_partida(novo_jogo)
    voltar_ao_menu(novo_jogo)
    novo_jogo.iniciar_novo_jogo()
    for _ in range(10):
        novo_jogo.update(DT)
    s = novo_jogo.sessao
    assert s.portal_atual is None and s.boss_atual is None and s.tela_de_upgrade_ativa is None
    assert s.timer_jogo > 0 and novo_jogo.estado_do_jogo == 'jogando'


def test_game_nao_guarda_mais_estado_de_sessao_nem_aliases(novo_jogo):
    for nome in CAMPOS + list(GRUPOS) + ['invocacao_protogravemind']:
        assert not hasattr(novo_jogo, nome), f'game.{nome} deveria estar em game.sessao/entity_manager'


def test_codigo_nao_usa_aliases_de_grupo_no_game():
    padrao = re.compile(r'\bgame\.(' + '|'.join(GRUPOS) + r')\b')
    for pasta, _, arquivos in os.walk(RAIZ_SOURCE):
        for nome in arquivos:
            if nome.endswith('.py'):
                with open(os.path.join(pasta, nome), encoding='utf-8') as f:
                    assert not padrao.search(f.read()), os.path.join(pasta, nome)
