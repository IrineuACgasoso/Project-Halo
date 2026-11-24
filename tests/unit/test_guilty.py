"""Guilty Spark reformulado: barreira, as 3 fases, invocações, feixes, teleporte, sprites e vfx."""
import math

import pygame
import pytest

from helpers import DT, blindar_jogador, ir_para_fase
from source.enemies.bosses.guilty.config import CFG, FASES
from source.enemies.standard.sentinel import Sentinel
from source.feats.projetil import BurstRifle
from source.feats.skills.artilharia import ArtilhariaAviso
from source.systems.dano import AREA, AURA, CONTATO, PROJETIL, Dano
from source.systems.entitymanager import entity_manager
from source.systems.eventos import INIMIGO_MORREU, eventos
from source.systems.gameclock import relogio
from source.systems.mapmanager.grade_paredes import GradeParedes

V = pygame.math.Vector2
CENTRO = V(1500, 1500)
NUNCA = float('inf')
# Cada acerto da luz tira uma fração fixa: quantos levam do começo da fase 2 ao da fase 3
ACERTOS_DA_FASE_2 = math.ceil(round((FASES[1].limiar_vida - FASES[2].limiar_vida) / CFG.luz_dano_no_guilty, 6))


@pytest.fixture
def guilty(novo_jogo):
    novo_jogo.spawner.spawnar('guilty')
    g = novo_jogo.sessao.boss_atual
    g.posicao.update(CENTRO)
    g.sync_rect()
    g.verificar_posicao_valida = lambda p: True
    g.travamento = None
    _esperas(g, NUNCA)      # nada dispara sozinho
    blindar_jogador(novo_jogo.player)
    novo_jogo.player.armas.clear()
    g.jogador.posicao.update(CENTRO + V(800, 0))
    return g


def _esperas(g, quando):
    g.cd = {nome: quando for nome in g.cd}
    g.proxima_invocacao = {nome: quando for nome in g.proxima_invocacao}


def _passo(g, paredes=None):
    """Relógio, boss e os sprites dele (sem spawner, colisão nem os outros inimigos)."""
    relogio.avancar(DT)
    g.update(DT, paredes)
    for s in list(entity_manager.all_sprites):
        if s is not g and s is not g.jogador and s not in entity_manager.inimigos_grupo and s.alive():
            s.update(DT)


def _ate(g, condicao, limite_s=20):
    for i in range(round(limite_s / DT)):
        if condicao():
            return i * DT
        _passo(g)
    raise AssertionError('não aconteceu')


def _ir_para_fase(g, fase):
    g.vida = g.vida_maxima * (FASES[fase - 1].limiar_vida - 1e-6)
    _passo(g)
    _esperas(g, NUNCA)
    g.wait = NUNCA if fase == 2 else g.wait
    assert g.fase == fase


def _sem_barreira_fase1(g):
    for _ in range(CFG.sentinelas_para_cair):
        eventos.emitir(INIMIGO_MORREU, inimigo=Sentinel(V(0, 0), g.game))
    assert g.fase == 1 and not g.barreira_ativa


# ── Barreira ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize('tipo', [PROJETIL, AREA, AURA, CONTATO])
def test_com_barreira_nada_o_fere(guilty, tipo):
    """Artilharia, cone, companheiro e espinhos não checam `invulneravel`: o contrato barra."""
    for fase in (1, 2):
        if fase == 2:
            _ir_para_fase(guilty, 2)
        vida = guilty.vida
        guilty.receber_dano(Dano(10 ** 9, tipo, guilty.jogador))
        assert guilty.vida == vida


def test_com_barreira_ninguem_mira_nele(guilty):
    assert guilty.vivo and not guilty.alvejavel
    _sem_barreira_fase1(guilty)
    assert guilty.alvejavel


def _tiro(g, deslocamento, direcao=V(0, 0), velocidade=100):
    return BurstRifle(posicao_inicial=g.posicao + deslocamento, grupos=(entity_manager.all_sprites,),
                      jogador=g.jogador, game=g.game, dono='PLAYER', tamanho=(24, 24), dano=7,
                      velocidade=velocidade, direcao_spread=direcao)


def test_tiros_morrem_na_borda_da_barreira(guilty):
    dentro = _tiro(guilty, V(CFG.barreira_raio - 5, 0))
    fora = _tiro(guilty, V(CFG.barreira_raio + 60, 0))
    guilty.barreira.update(DT)
    assert not dentro.alive() and fora.alive()


def test_barreira_empurra_sem_atravessar_parede(guilty):
    """Espremido contra uma parede por 3 s, o jogador nunca passa para o outro lado."""
    parede_x = CENTRO.x + 300
    paredes = GradeParedes([{'pontos': [V(parede_x, CENTRO.y - 900), V(parede_x, CENTRO.y + 900)]}])
    j = guilty.jogador
    j.posicao.update(parede_x - 60, CENTRO.y)
    j.direcao.update(0, 0)
    for _ in range(round(3 / DT)):
        relogio.avancar(DT)
        guilty.posicao.x += 260 * DT
        j.mover_com_colisao(DT, paredes)
        guilty.barreira.update(DT)
        assert j.posicao.x < parede_x
        if guilty.posicao.x > parede_x - 60:
            break


# ── Fase 1: queda da barreira ────────────────────────────────────────────────
def test_quarenta_sentinelas_derrubam_a_barreira_e_religam_o_spawner(guilty):
    sentinela = Sentinel(V(0, 0), guilty.game)
    for _ in range(CFG.sentinelas_para_cair - 1):
        eventos.emitir(INIMIGO_MORREU, inimigo=sentinela)
    assert guilty.barreira_ativa and not guilty.permitir_spawns_normais
    aura = guilty.barreira
    eventos.emitir(INIMIGO_MORREU, inimigo=sentinela)
    assert not guilty.barreira_ativa and not aura.alive() and not guilty.invulneravel
    assert guilty.permitir_spawns_normais and guilty.fase == 1


def test_spawner_religado_nao_chama_outro_boss(guilty):
    game = guilty.game
    _sem_barreira_fase1(guilty)
    game.sessao.timer_jogo = 10 ** 6
    game.spawner.boss_flags = {nome: False for nome in game.spawner.boss_flags}
    chamadas = []
    game.spawner.spawnar = chamadas.append
    for _ in range(round(6 / DT)):
        game._atualizar_spawner(DT)
    assert set(chamadas) == {'normal'}


# ── Fases ────────────────────────────────────────────────────────────────────
def test_um_golpe_nao_pula_fase(guilty):
    _sem_barreira_fase1(guilty)
    guilty.receber_dano(Dano(10 ** 9, PROJETIL))
    assert guilty.vida / guilty.vida_maxima == pytest.approx(FASES[1].limiar_vida) and guilty.fase == 1
    _passo(guilty)
    assert guilty.fase == 2


def test_fase_2_ergue_a_barreira_desliga_o_spawner_e_corta_o_feixe(guilty):
    _sem_barreira_fase1(guilty)
    guilty.iniciar('proximidade')
    _passo(guilty)
    assert guilty.feixe_ativo is not None
    _ir_para_fase(guilty, 2)
    assert guilty.barreira_ativa and guilty.invulneravel and not guilty.permitir_spawns_normais
    assert guilty.feixe_ativo is None and guilty.rotina is None


def test_fase_3_e_vulneravel_e_morre(guilty):
    _ir_para_fase(guilty, 2)
    _ir_para_fase(guilty, 3)
    assert not guilty.barreira_ativa and not guilty.permitir_spawns_normais
    _ate(guilty, lambda: guilty.alvejavel and not guilty.em_teleporte)
    guilty.receber_dano(Dano(10 ** 9, PROJETIL))
    assert not guilty.vivo
    guilty.game.collision_manager.update(DT)
    assert not guilty.alive()


# ── Ronda ────────────────────────────────────────────────────────────────────


def test_antistuck_teleporta_para_perto(guilty):
    guilty.jogador.posicao.update(CENTRO + V(3000, 0))
    guilty.iniciar('antistuck')
    _ate(guilty, lambda: guilty.rotina is None)
    assert guilty.posicao.distance_to(guilty.jogador.posicao) <= CFG.tp_raio[1] + 10


# ── Fase 1: chuva de sentinelas ──────────────────────────────────────────────


def test_chuva_tem_teto_de_vivas(guilty):
    for _ in range(CFG.chuva_max_vivas):
        assert guilty.chover_sentinela() is not None
    assert guilty.chover_sentinela() is None


# ── Fase 1: armadilha ────────────────────────────────────────────────────────
def _armar(g):
    g.armar_armadilha()
    return g.armadilha


def test_morte_do_guilty_desfaz_a_armadilha(guilty):
    a = _armar(guilty)
    guilty.kill()
    a.update(DT)
    assert not a.alive() and not any(e.alive() for e in a.esferas)


# ── Fase 2: luz visível ──────────────────────────────────────────────────────
def _luz_longe_do_guilty(g):
    """Uma cadeia em cima do jogador, com o Guilty a 800 px (fora de todas)."""
    g.invocar_luz()
    return g.luz


def _aviso_da_luz(g, preset, distancia):
    return ArtilhariaAviso(g.posicao + V(distancia, 0), (entity_manager.all_sprites,), g.game, dono='BOSS',
                           preset=preset, fonte=g)


def test_acertos_da_luz_derrubam_a_barreira_no_limiar_da_fase_3(guilty):
    _ir_para_fase(guilty, 2)
    for i in range(ACERTOS_DA_FASE_2):
        assert guilty.barreira_ativa and guilty.fase == 2, i
        guilty.atingido_pela_luz(_aviso_da_luz(guilty, 'guilty_luz_4', 0))
        _passo(guilty)
    assert guilty.fase == 3 and not guilty.barreira_ativa and guilty.vida > 0


def test_luz_so_o_fere_na_fase_2(guilty):
    vida = guilty.vida
    assert not guilty.atingido_pela_luz(_aviso_da_luz(guilty, 'guilty_luz_4', 0))
    assert guilty.vida == vida


# ── Fase 3 ───────────────────────────────────────────────────────────────────
def _fase3(g):
    _ir_para_fase(g, 2)
    g.wait = 0
    _ir_para_fase(g, 3)


def test_interromper_o_teleporte_devolve_ao_mundo(guilty):
    _fase3(guilty)
    _ate(guilty, lambda: guilty.em_teleporte)
    _passo(guilty)
    guilty.interromper_rotina()
    assert not guilty.em_teleporte and guilty.alpha_atual == 255


# ── VFX ──────────────────────────────────────────────────────────────────────


def test_partida_real_da_fase_2_do_spawn_a_morte(novo_jogo):
    """O loop do jogo (colisão, spawner, HUD e desenho) pelas 3 fases, sem erro no Renderer."""
    ir_para_fase(novo_jogo, 2)
    blindar_jogador(novo_jogo.player)
    novo_jogo.spawner.spawnar('guilty')
    g = novo_jogo.sessao.boss_atual

    def rodar(segundos):
        for i in range(round(segundos / DT)):
            novo_jogo.update(DT)
            if i % 6 == 0:
                novo_jogo.draw()

    rodar(6)
    assert g.sentinelas_derrotadas + len(g.sentinelas) >= 1
    g.sentinelas_derrotadas = CFG.sentinelas_para_cair - 1
    eventos.emitir(INIMIGO_MORREU, inimigo=Sentinel(V(0, 0), novo_jogo))
    rodar(4)
    g.receber_dano(Dano(10 ** 9, PROJETIL))
    rodar(12)
    assert g.fase == 2
    while g.fase == 2:
        g.receber_dano(Dano(g.vida_maxima * 0.05, AREA, g))
        rodar(0.1)
    rodar(6)
    assert g.fase == 3
    for _ in range(200):
        if not g.alive():
            break
        g.receber_dano(Dano(10 ** 9, PROJETIL))
        rodar(0.1)
    assert not g.alive() and novo_jogo.sessao.boss_atual is None
    rodar(2)
    assert novo_jogo.renderer._erros_logados == set()


def test_boss_morto_nao_invoca_mais_nada(guilty):
    chuva = guilty.chover_sentinela()
    _ir_para_fase(guilty, 2)
    flood = guilty.infestar()
    supers = guilty.chover_super_sentinelas()
    luz = _luz_longe_do_guilty(guilty)
    guilty.kill()
    for _ in range(round(3 / DT)):
        relogio.avancar(DT)
        for s in list(entity_manager.all_sprites):
            if s is not guilty.jogador and s not in entity_manager.inimigos_grupo:
                s.update(DT)
    assert all(a.explodiu for a in (chuva, flood, *supers)) and not luz.alive()
    assert not guilty.sentinelas and not guilty.floods and not guilty.super_sentinelas
