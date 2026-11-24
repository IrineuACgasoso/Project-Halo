"""Sessão separada do Game (roteiro B3): cada partida é um objeto novo, nada sobra da anterior."""
import dataclasses

from helpers import DT, voltar_ao_menu
from source.systems.gameclock import _OFFSET_INICIAL_MS, relogio
from source.systems.sessao import SessaoJogo

CAMPOS = [c.name for c in dataclasses.fields(SessaoJogo)]


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
