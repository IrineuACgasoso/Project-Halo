"""Skill de invisibilidade (`feats/skills/invisibilidade`): fases, tempos, alpha, encerrar e clarão;
e a regra do jogo: invisível nunca é mirado, mas pode ser atingido e distorce o cenário."""

import pygame
import pytest

from helpers import DT, blindar_jogador, simular
from source.enemies.standard.grunt import GruntRed
from source.feats.projetil import M50, ProjetilNeedler
from source.feats.skills.invisibilidade import (FADE_IN, FADE_OUT, OCULTO,
                                                Invisibilidade, InvisibilidadeConfig)
from source.systems.entitymanager import entity_manager
from source.systems.levelup import ARMAS_REGISTRO

V = pygame.math.Vector2


@pytest.fixture
def grunt(novo_jogo):
    g = GruntRed(posicao=novo_jogo.player.posicao + V(300, 0), game=novo_jogo)
    g.invencivel = False
    return g


def _com(grunt, **kwargs):
    grunt.invisibilidade = Invisibilidade(grunt, config=InvisibilidadeConfig(**kwargs))
    return grunt.invisibilidade


def _passar(grunt, ms):
    for _ in range(round(ms / (DT * 1000))):
        grunt.atualizar_invisibilidade(DT)


# ── Fases e tempos ───────────────────────────────────────────────────────────
def test_duracao_nao_conta_os_fades(grunt):
    """Fade out 500 + 1000 invisível + fade in 250: cada fase dura o que o parâmetro diz."""
    inv = _com(grunt, fade_out_ms=500, duracao_ms=1000, fade_in_ms=250)
    quadros = {FADE_OUT: 0, OCULTO: 0, FADE_IN: 0}
    for _ in range(1000):
        quadros[inv.fase] += 1
        grunt.atualizar_invisibilidade(DT)
        if grunt.invisibilidade is None:
            break
    ms = {fase: n * DT * 1000 for fase, n in quadros.items()}
    assert ms[FADE_OUT] == pytest.approx(500, abs=20)
    assert ms[OCULTO] == pytest.approx(1000, abs=20)
    assert ms[FADE_IN] == pytest.approx(250, abs=20)


def test_so_o_fade_in_pode_ser_mirado(grunt):
    inv = _com(grunt, fade_out_ms=100, duracao_ms=100, fade_in_ms=200)
    vistos = {}
    while grunt.invisibilidade is not None:
        vistos.setdefault(inv.fase, set()).add(grunt.alvejavel)
        grunt.atualizar_invisibilidade(DT)
    assert vistos[FADE_OUT] == {False} and vistos[OCULTO] == {False}
    assert True in vistos[FADE_IN]
    assert grunt.alvejavel


def test_sem_duracao_fica_oculto_ate_encerrar(grunt):
    inv = _com(grunt, fade_out_ms=100, duracao_ms=None, fade_in_ms=100)
    _passar(grunt, 60_000)
    assert inv.fase == OCULTO
    grunt.encerrar_invisibilidade()
    assert inv.fase == FADE_IN
    _passar(grunt, 150)
    assert grunt.invisibilidade is None and grunt.alpha_atual == 255


# ── Regra: ninguém mira no invisível ─────────────────────────────────────────
def _ocultar(inimigo):
    """Invisível sem fim, já no meio do efeito."""
    inimigo.invisibilidade = Invisibilidade(inimigo, config=InvisibilidadeConfig(1, None, 100))
    inimigo.atualizar_invisibilidade(DT)
    assert inimigo.fase_invisibilidade == OCULTO
    return inimigo


# Não miram: giram em volta do jogador, são aura ou contra-ataque
SEM_MIRA = {'energy_sword', 'mk2_shield', 'mjolnir_punch', 'cortana'}


def _criar_arma(game, id_arma):
    arma = ARMAS_REGISTRO[id_arma].criar(game.player, game)
    game.player.armas.clear()
    game.player.armas[id_arma] = arma
    veiculo = getattr(arma, 'sprite_veiculo', None)
    if veiculo is not None:
        veiculo.entrar()
    for sprite in _aliados(arma):
        sprite.posicao.update(game.player.posicao)
    return arma


def _aliados(arma):
    """Os sprites que procuram alvo por conta própria: companheiros e veículo."""
    candidatos = [*getattr(arma, 'companions', []), getattr(arma, 'sprite_companion', None),
                  getattr(arma, 'sprite_veiculo', None)]
    return [s for s in candidatos if s is not None]


def _mirou(game, inimigo, arma, segundos=4):
    """O jogo real por alguns segundos, com o inimigo parado: alguém atirou ou o escolheu como alvo?"""
    game.spawner.update = lambda dt: None
    blindar_jogador(game.player)
    inimigo.vida = inimigo.vida_maxima = 10 ** 6
    inimigo.update = lambda dt, paredes=None: None
    for _ in range(round(segundos / DT)):
        game.update(DT)
        # `dono`: todo projétil do jogador, inclusive as granadas (fora do grupo de projéteis)
        if (any(getattr(s, 'dono', None) == 'PLAYER' for s in entity_manager.all_sprites)
                or any(s.alvo is inimigo for s in _aliados(arma))):
            return True
    return False


@pytest.mark.parametrize('id_arma', sorted(set(ARMAS_REGISTRO) - SEM_MIRA))
def test_nada_mira_no_invisivel_mas_mira_no_visivel(novo_jogo, grunt, id_arma):
    """Toda arma, companheiro e veículo que procura alvo. A 2ª metade prova que o teste vale."""
    grunt.posicao.update(novo_jogo.player.posicao + V(150, 0))
    grunt.sync_rect()
    arma = _criar_arma(novo_jogo, id_arma)
    _ocultar(grunt)
    assert not _mirou(novo_jogo, grunt, arma)
    grunt.invisibilidade = None
    grunt._aplicar_alpha(255)
    assert _mirou(novo_jogo, grunt, arma)


def test_sem_mira_esta_certo():
    """Arma nova que procura alvo entra sozinha no teste acima; a lista só tem quem existe."""
    assert SEM_MIRA <= set(ARMAS_REGISTRO)


def test_companheiro_larga_o_alvo_que_sumiu(novo_jogo, grunt):
    _criar_arma(novo_jogo, 'marine')
    marine = novo_jogo.player.armas['marine'].sprite_companion
    grunt.posicao.update(marine.posicao + V(100, 0))
    marine.logica_de_decisao()
    assert marine.alvo is grunt
    _ocultar(grunt)
    marine.logica_de_decisao()
    assert marine.alvo is not grunt


def test_agulha_perde_o_alvo_que_sumiu_e_segue_reto(novo_jogo, grunt):
    p = novo_jogo.player
    grunt.posicao.update(p.posicao + V(400, 400))
    agulha = ProjetilNeedler(posicao_inicial=p.posicao, grupos=(entity_manager.all_sprites,), jogador=p,
                             game=novo_jogo, dono='PLAYER', tamanho=(20, 8), dano=1, velocidade=100,
                             direcao_spread=V(1, 0), alvo=grunt)
    agulha.update(DT)
    assert agulha.direcao.y > 0                        # curvou para o alvo
    _ocultar(grunt)
    direcao = V(agulha.direcao)
    for _ in range(20):
        agulha.update(DT)
    assert agulha.direcao == direcao
    grunt.invisibilidade = None                        # reapareceu: a agulha já o perdeu
    grunt._aplicar_alpha(255)
    agulha.update(DT)
    assert agulha.direcao == direcao


# ── Regra: invisível não é invulnerável ──────────────────────────────────────
def test_tiro_perdido_acerta_o_invisivel(novo_jogo, grunt):
    _ocultar(grunt)
    assert not grunt.invulneravel and not grunt.alvejavel
    grunt.vida = grunt.vida_maxima = 100
    tiro = M50(posicao_inicial=grunt.posicao, grupos=(entity_manager.all_sprites,), jogador=novo_jogo.player,
               game=novo_jogo, dono='PLAYER', tamanho=(20, 20), dano=7, velocidade=0, direcao_spread=V(1, 0))
    novo_jogo.collision_manager.update(DT)
    assert grunt.vida == 93 and not tiro.alive()


def test_aura_do_jogador_acerta_o_invisivel(novo_jogo, grunt):
    _criar_arma(novo_jogo, 'mk2_shield').equipar()
    grunt.vida = grunt.vida_maxima = 1000
    grunt.posicao.update(novo_jogo.player.posicao + V(40, 0))
    grunt.sync_rect()
    _ocultar(grunt)
    novo_jogo.player.escudo_atual = novo_jogo.player.escudo_maximo   # a aura só vale com escudo
    grunt.update = lambda dt, paredes=None: None
    simular(novo_jogo, 0.5)
    assert grunt.vida < 1000


def test_encostar_no_invisivel_machuca(novo_jogo, grunt):
    p = novo_jogo.player
    _ocultar(grunt)
    grunt.posicao.update(p.posicao)
    grunt.sync_rect()
    vida = p.vida_atual
    novo_jogo.collision_manager.update(DT)
    assert p.vida_atual < vida


@pytest.mark.parametrize('nome', ['knight', 'warden'])
def test_teleporte_nao_e_invisibilidade(novo_jogo, nome):
    """Knight e Warden somem viajando: fora do mundo (nem mirados, nem atingidos), como antes."""
    novo_jogo.spawner.spawnar(nome)
    boss = novo_jogo.sessao.boss_atual
    boss = boss.wardens_vivos[0] if nome == 'warden' else boss
    boss.invencivel = False
    boss.verificar_posicao_valida = lambda pos: True
    boss.executar_tp()
    assert boss.em_teleporte and boss.invulneravel and not boss.alvejavel
    boss.tp_orb.kill()
    boss.update_tp()
    assert not boss.em_teleporte and not boss.invulneravel and boss.alvejavel
