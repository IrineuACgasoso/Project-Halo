"""Guilty Spark reformulado: barreira, as 3 fases, invocações, feixes, teleporte, sprites e vfx."""
import dataclasses
import math
import random
from collections import Counter

import pygame
import pytest

from helpers import DT, blindar_jogador, contar_alocacoes, ir_para_fase
from source.enemies.bosses.guilty import armadilha as mod_armadilha
from source.enemies.bosses.guilty.armadilha import BUSCA, DISPARO, PARADA, ArmadilhaForerunner
from source.enemies.bosses.guilty.config import CFG, FASES, FeixeConfig, GuiltyConfig
from source.enemies.bosses.guilty.luz_visivel import LuzVisivel
from source.enemies.bosses.guilty.vfx import FeixeDoCeu, TeleporteVFX
from source.enemies.standard.grunt import GruntRed
from source.enemies.standard.infection import FloodCarry, FloodElite, FloodMarine
from source.enemies.standard.sentinel import Sentinel, SentinelMajor
from source.feats.projetil import BurstRifle
from source.feats.skills.artilharia import ArtilhariaAviso
from source.feats.skills.artilharia.config import ARTILHARIA_PRESETS
from source.feats.skills.invisibilidade import FADE_IN, OCULTO
from source.systems.dano import AREA, AURA, CONTATO, PROJETIL, Dano
from source.systems.entitymanager import entity_manager
from source.systems.eventos import INIMIGO_MORREU, eventos
from source.systems.gameclock import relogio
from source.systems.mapmanager.grade_paredes import GradeParedes
from source.systems.status import Lentidao, Queimadura

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


def _avisos(preset=None):
    return [s for s in entity_manager.all_sprites if isinstance(s, ArtilhariaAviso)
            and (preset is None or s.cfg is ARTILHARIA_PRESETS[preset])]


def _sprites(classe):
    return [s for s in entity_manager.all_sprites if isinstance(s, classe)]


# ── Barreira ─────────────────────────────────────────────────────────────────
def test_nasce_com_a_barreira_impenetravel_e_spawner_desligado(guilty):
    assert guilty.barreira_ativa and guilty.barreira.impenetravel and guilty.barreira.alive()
    assert guilty.invulneravel and not guilty.permitir_spawns_normais and guilty.fase == 1


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


def test_o_tiro_nao_chega_a_encostar_no_sprite(guilty):
    """O mais rápido do jogo (2400 px/s) para bem antes do corpo."""
    tiro = _tiro(guilty, V(400, 0), V(-1, 0), 2400)
    mais_perto = 400.0
    for _ in range(30):
        relogio.avancar(DT)
        tiro.update(DT)
        guilty.barreira.update(DT)
        if not tiro.alive():
            break
        mais_perto = min(mais_perto, tiro.posicao.distance_to(guilty.posicao))
    assert not tiro.alive() and mais_perto > 60


def test_lamina_tijolo_e_granada_nao_sao_destruidos(guilty):
    infinito = _tiro(guilty, V(20, 0))
    infinito.piercing = float('inf')
    orbita = _tiro(guilty, V(20, 0), velocidade=0)
    guilty.barreira.update(DT)
    assert infinito.alive() and orbita.alive()


def test_aura_comum_nao_bloqueia_tiros(guilty):
    guilty.barreira.bloqueia_tiros = False
    tiro = _tiro(guilty, V(20, 0))
    guilty.barreira.update(DT)
    assert tiro.alive()


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


def test_barreira_empurra_para_a_borda(guilty):
    guilty.jogador.posicao.update(guilty.posicao + V(CFG.barreira_raio, 0))
    guilty.barreira.update(DT)
    assert guilty.jogador.posicao.distance_to(guilty.posicao) == pytest.approx(CFG.barreira_raio + 15)


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


def test_so_sentinela_conta_e_so_a_morta_em_combate(guilty):
    eventos.emitir(INIMIGO_MORREU, inimigo=GruntRed(posicao=V(0, 0), game=guilty.game))
    assert guilty.sentinelas_derrotadas == 0
    eventos.emitir(INIMIGO_MORREU, inimigo=SentinelMajor(V(0, 0), guilty.game))
    assert guilty.sentinelas_derrotadas == 1
    s = Sentinel(V(0, 0), guilty.game)
    s.receber_dano(Dano(9999, PROJETIL, guilty.jogador))
    guilty.game.collision_manager.update(DT)      # a morte de verdade emite o evento
    assert guilty.sentinelas_derrotadas == 2


def test_depois_da_queda_nao_conta_mais(guilty):
    _sem_barreira_fase1(guilty)
    eventos.emitir(INIMIGO_MORREU, inimigo=Sentinel(V(0, 0), guilty.game))
    assert guilty.sentinelas_derrotadas == CFG.sentinelas_para_cair
    _ir_para_fase(guilty, 2)
    eventos.emitir(INIMIGO_MORREU, inimigo=Sentinel(V(0, 0), guilty.game))
    assert guilty.sentinelas_derrotadas == CFG.sentinelas_para_cair and guilty.barreira_ativa


def test_spawner_do_jogo_para_com_o_boss_e_volta_sem_a_barreira(guilty):
    game = guilty.game
    chamadas = []
    game.spawner.spawnar = chamadas.append
    timer = game.sessao.timer_jogo
    for _ in range(round(6 / DT)):
        game._atualizar_spawner(DT)
    assert chamadas == []
    _sem_barreira_fase1(guilty)
    for _ in range(round(6 / DT)):
        game._atualizar_spawner(DT)
    assert chamadas and set(chamadas) == {'normal'}
    assert game.sessao.timer_jogo == timer        # o relógio dos bosses continua parado
    _ir_para_fase(guilty, 2)
    chamadas.clear()
    for _ in range(round(6 / DT)):
        game._atualizar_spawner(DT)
    assert chamadas == []


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


def test_sem_barreira_na_fase_1_so_o_feixe_de_proximidade(guilty):
    _sem_barreira_fase1(guilty)
    _esperas(guilty, 0)
    vistos = set()
    for _ in range(round(10 / DT)):
        _passo(guilty)
        vistos.add(guilty.estado_habilidade)
    assert vistos <= {'idle', 'feixe_proximidade'}
    assert _avisos() == [] and guilty.armadilha is None


def test_artilharia_que_ja_caia_so_estoura_depois_da_queda(guilty):
    aviso = guilty.chover_sentinela()
    _sem_barreira_fase1(guilty)
    antes = len(_sprites(Sentinel))
    _ate(guilty, lambda: aviso.explodiu)
    assert len(_sprites(Sentinel)) == antes and guilty.avisos_chuva == 0


# ── Fases ────────────────────────────────────────────────────────────────────
def test_um_golpe_nao_pula_fase(guilty):
    _sem_barreira_fase1(guilty)
    guilty.receber_dano(Dano(10 ** 9, PROJETIL))
    assert guilty.vida / guilty.vida_maxima == pytest.approx(FASES[1].limiar_vida) and guilty.fase == 1
    _passo(guilty)
    assert guilty.fase == 2


@pytest.mark.parametrize('nivel', [1, 7, 13, 33])
def test_limiares_valem_em_qualquer_nivel(novo_jogo, nivel):
    """A vida escala com o nível: a conta em float precisa cruzar os limiares exatos das fases."""
    novo_jogo.player.contador_niveis = nivel
    novo_jogo.spawner.spawnar('guilty')
    g = novo_jogo.sessao.boss_atual
    blindar_jogador(novo_jogo.player)
    _sem_barreira_fase1(g)
    g.receber_dano(Dano(10 ** 9, PROJETIL))
    _passo(g)
    assert g.fase == 2
    acertos = 0
    while g.fase == 2:
        g.receber_dano(Dano(g.vida_maxima * CFG.luz_dano_no_guilty, AREA, g))
        g.wait = NUNCA
        _passo(g)
        acertos += 1
    assert acertos == ACERTOS_DA_FASE_2 and g.fase == 3
    assert g.vida / g.vida_maxima == pytest.approx(FASES[2].limiar_vida)


def test_fase_2_ergue_a_barreira_desliga_o_spawner_e_corta_o_feixe(guilty):
    _sem_barreira_fase1(guilty)
    guilty.iniciar('proximidade')
    _passo(guilty)
    assert guilty.feixe_ativo is not None
    _ir_para_fase(guilty, 2)
    assert guilty.barreira_ativa and guilty.invulneravel and not guilty.permitir_spawns_normais
    assert guilty.feixe_ativo is None and guilty.rotina is None


def test_fase_2_comeca_com_os_cooldowns_iniciais_dela(guilty):
    guilty.vida = guilty.vida_maxima * 0.5
    _passo(guilty)
    assert guilty.cd['laser'] == guilty._agora + CFG.cooldown_inicial['laser']
    for nome in ('luz', 'chuva_super', 'infestacao'):
        assert guilty.proxima_invocacao[nome] == guilty._agora + CFG.intervalo_inicial[nome]


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
def _dist_do_caminho(origem, destino, ponto):
    d = destino - origem
    t = max(0.0, min(1.0, (ponto - origem).dot(d) / d.length_squared()))
    return (origem + d * t).distance_to(ponto)


def test_caminhos_da_ronda_passam_perto_do_jogador_e_variam(guilty):
    rumos = []
    for _ in range(300):
        destino = guilty._sortear_destino()
        assert _dist_do_caminho(guilty.posicao, destino, guilty.jogador.posicao) <= CFG.ronda_desvio + 1
        assert destino.distance_to(guilty.posicao) > guilty.jogador.posicao.distance_to(guilty.posicao) * 0.9
        rumos.append((destino - guilty.posicao).as_polar()[1])
    assert max(rumos) - min(rumos) > 10


def test_ronda_passa_perto_do_jogador_de_verdade(guilty):
    menor = 10 ** 9
    for _ in range(round(12 / DT)):
        _passo(guilty)
        guilty.jogador.posicao.update(CENTRO + V(800, 0))    # a barreira não o tira do lugar
        menor = min(menor, guilty.posicao.distance_to(guilty.jogador.posicao))
    assert menor < CFG.ronda_desvio + 20


def _velocidade_media(g, segundos=1.5):
    g.ronda_ate = 0
    antes, andou = V(g.posicao), 0.0
    for _ in range(round(segundos / DT)):
        _passo(g)
        andou += g.posicao.distance_to(antes)
        antes.update(g.posicao)
    return andou / segundos


def test_velocidades_da_ronda(guilty):
    base = guilty.velocidade_base
    assert _velocidade_media(guilty) == pytest.approx(base, rel=0.02)
    _sem_barreira_fase1(guilty)
    assert _velocidade_media(guilty) == pytest.approx(base * CFG.mult_sem_barreira, rel=0.02)
    _ir_para_fase(guilty, 2)
    assert _velocidade_media(guilty) == pytest.approx(base * 2, rel=0.02)


def test_preso_na_parede_sorteia_outro_caminho(guilty):
    pos = V(guilty.posicao)
    guilty.aplicar_colisao_mapa = lambda paredes: guilty.posicao.update(pos)
    destinos = set()
    for _ in range(round(2 / DT)):
        _passo(guilty, paredes=True)
        destinos.add(tuple(guilty.ronda_destino))
    assert len(destinos) >= 4


def test_sem_ponto_valido_vai_ate_o_jogador(guilty):
    guilty.verificar_posicao_valida = lambda p: False
    assert guilty._sortear_destino() == guilty.jogador.posicao


def test_antistuck_teleporta_para_perto(guilty):
    guilty.jogador.posicao.update(CENTRO + V(3000, 0))
    guilty.iniciar('antistuck')
    _ate(guilty, lambda: guilty.rotina is None)
    assert guilty.posicao.distance_to(guilty.jogador.posicao) <= CFG.tp_raio[1] + 10


# ── Fase 1: chuva de sentinelas ──────────────────────────────────────────────
def test_chuva_cai_o_tempo_todo_e_cada_aviso_vira_sentinela(guilty):
    guilty.proxima_invocacao['chuva'] = 0
    for _ in range(round(10 / DT)):
        _passo(guilty)
    n = len(guilty.sentinelas)
    assert 6 <= n <= 11 and all(type(s) is Sentinel for s in guilty.sentinelas)


def test_aviso_da_chuva_e_pequeno_machuca_e_treme(guilty):
    j = guilty.jogador
    aviso = guilty.chover_sentinela()
    assert aviso.cfg.raio_explosao <= 100 and aviso.cfg.dano > 0 and aviso.fonte is guilty
    aviso.posicao.update(j.posicao)
    vida = j.vida_atual
    _ate(guilty, lambda: aviso.explodiu)
    assert j.vida_atual == vida - aviso.cfg.dano
    assert guilty.game.camera.shake_intensidade == CFG.shake_chuva
    assert len(entity_manager.particulas_grupo) >= 14


def test_sentinela_nasce_invisivel_e_aparece_rapido(guilty):
    aviso = guilty.chover_sentinela()
    _ate(guilty, lambda: guilty.sentinelas)
    s = guilty.sentinelas[0]
    assert s.posicao.distance_to(aviso.posicao) < 1 and s.alpha_atual == 0 and not s.alvejavel
    fases = set()
    for i in range(120):
        relogio.avancar(DT)
        s.update(DT)
        fases.add(s.fase_invisibilidade)
        if s.invisibilidade is None:
            break
    assert {OCULTO, FADE_IN} <= fases
    assert s.alpha_atual == 255 and s.alvejavel and i * DT < 0.9


def test_alpha_da_sentinela_materializando_nao_vaza_para_as_outras(novo_jogo):
    """O quadro do cache é compartilhado: antes, o alpha de uma valia para todas."""
    visivel, nova = Sentinel(V(0, 0), novo_jogo), Sentinel(V(0, 0), novo_jogo)
    nova.materializar()
    relogio.avancar(DT)
    for s in (visivel, nova):
        s.update(DT)
    assert nova.image.get_alpha() == 0
    assert visivel.image.get_alpha() in (None, 255)


def test_aura_da_super_sentinela_aparece_junto(novo_jogo):
    s = SentinelMajor(V(0, 0), novo_jogo)
    s.materializar()
    relogio.avancar(DT)
    s.update(DT)
    assert s.aura.image.get_alpha() == 0
    for _ in range(90):
        relogio.avancar(DT)
        s.update(DT)
    assert s.aura.image.get_alpha() == 255


def test_chuva_tem_teto_de_vivas(guilty):
    for _ in range(CFG.chuva_max_vivas):
        assert guilty.chover_sentinela() is not None
    assert guilty.chover_sentinela() is None


def test_chuva_cai_em_chao_valido(guilty):
    guilty.verificar_posicao_valida = lambda p: p.x > guilty.jogador.posicao.x
    for _ in range(15):
        assert guilty.chover_sentinela().posicao.x >= guilty.jogador.posicao.x


# ── Fase 1: armadilha ────────────────────────────────────────────────────────
def _armar(g):
    g.armar_armadilha()
    return g.armadilha


def test_esferas_surgem_fora_da_tela_em_lados_opostos(guilty):
    a = _armar(guilty)
    tela = pygame.Rect(0, 0, 1280, 720)
    tela.center = guilty.jogador.posicao
    d = [e.posicao - guilty.jogador.posicao for e in a.esferas]
    assert all(not tela.collidepoint(e.posicao) for e in a.esferas)
    assert d[0].normalize().dot(d[1].normalize()) == pytest.approx(-1)


def test_esferas_nao_sao_alvo_nem_inimigo(guilty):
    a = _armar(guilty)
    assert not any(e in entity_manager.inimigos_grupo for e in a.esferas)


def test_fecham_a_linha_com_o_jogador_em_movimento(guilty):
    a = _armar(guilty)
    j = guilty.jogador
    for _ in range(round(3 / DT)):
        if a.estado != BUSCA:
            break
        j.posicao += V(0, 400 * DT)
        _passo(guilty)
    assert a.estado == PARADA
    assert _dist_do_caminho(a.esferas[0].posicao, a.esferas[1].posicao, j.posicao) < 15


def test_parado_na_linha_leva_um_golpe_so_e_queima(guilty):
    a, j = _armar(guilty), guilty.jogador
    golpes = []
    original = j.receber_dano
    j.receber_dano = lambda d: (golpes.append(d), original(d))
    _ate(guilty, lambda: not a.alive())
    del j.receber_dano
    assert [(d.valor, d.tipo, d.fonte) for d in golpes] == [(CFG.armadilha_dano, AREA, guilty)]
    (efeito, fonte, _), = j.status.ativos()
    assert efeito == Queimadura(CFG.armadilha_queimadura_dps, CFG.armadilha_queimadura_ms) and fonte is guilty


def test_quem_sai_da_linha_escapa(guilty):
    a, j = _armar(guilty), guilty.jogador
    _ate(guilty, lambda: a.estado == PARADA)
    j.posicao += V(-a.eixo.y, a.eixo.x) * 120
    vida = j.vida_atual
    _ate(guilty, lambda: not a.alive())
    assert j.vida_atual == vida and not a.acertou


def test_so_a_emissora_acende_e_o_feixe_vai_dela_a_outra(guilty):
    a = _armar(guilty)
    _ate(guilty, lambda: a.estado == DISPARO)
    assert a.emissora.image is mod_armadilha.imagem_da_esfera(azul=True)
    assert a.receptora.image is mod_armadilha.imagem_da_esfera(azul=False)
    assert a.feixe.owner is a.emissora
    for _ in range(20):
        _passo(guilty)
    assert a.feixe.mira_atual.distance_to(a.receptora.posicao) < 5


def test_qualquer_uma_das_duas_pode_disparar(guilty):
    lados = set()
    for _ in range(40):
        a = ArmadilhaForerunner(guilty)
        lados.add(a.esferas.index(a.emissora))
        a.desfazer()
    assert lados == {0, 1}


def test_tremor_da_armadilha_decresce(guilty):
    a = _armar(guilty)
    _ate(guilty, lambda: a.estado == DISPARO)
    tremores = []
    while a.estado == DISPARO:
        _passo(guilty)
        tremores.append(guilty.game.camera.shake_intensidade)
    assert tremores[0] > 0.8 * CFG.shake_armadilha and tremores[-1] < 0.2 * CFG.shake_armadilha
    assert tremores == sorted(tremores, reverse=True)


def test_sem_fechar_a_linha_a_armadilha_desiste_de_buscar(guilty):
    a = _armar(guilty)
    for _ in range(round((CFG.armadilha_busca_max_ms + 500) / 1000 / DT)):
        guilty.jogador.posicao += V(1, 0) * 3000 * DT
        _passo(guilty)
    assert a.estado != BUSCA


def test_morte_do_guilty_desfaz_a_armadilha(guilty):
    a = _armar(guilty)
    guilty.kill()
    a.update(DT)
    assert not a.alive() and not any(e.alive() for e in a.esferas)


# ── Fase 1: feixe de proximidade ─────────────────────────────────────────────
def _perto(g, folga=-10):
    g.jogador.posicao.update(g.posicao + V(CFG.proximidade_dist + folga, 0))


@pytest.mark.parametrize('folga, dispara', [(-10, True), (40, False)])
def test_proximidade_so_dispara_perto(guilty, folga, dispara):
    guilty.cd['proximidade'] = 0
    _perto(guilty, folga)
    _passo(guilty)
    assert (guilty.estado_habilidade == 'feixe_proximidade') == dispara


def test_proximidade_para_fica_vermelho_dura_meio_segundo_e_doi(guilty):
    guilty.cd['proximidade'] = 0
    _perto(guilty)
    j, inicio, pos = guilty.jogador, relogio.agora(), V(guilty.posicao)
    vida = j.vida_atual
    _passo(guilty)
    pos.update(guilty.posicao)
    assert guilty.animador.clip == 'vermelho' and guilty.feixe_ativo is guilty.feixe_proximidade
    assert guilty.game.camera.shake_intensidade == CFG.proximidade.shake >= 10
    while guilty.feixe_ativo is not None:
        _passo(guilty)
    duracao = relogio.agora() - inicio
    assert 500 <= duracao <= 550 and guilty.posicao.distance_to(pos) < 4
    assert 200 <= vida - j.vida_atual <= 280
    _passo(guilty)
    assert guilty.animador.clip == 'azul' and not guilty.pronto('proximidade')


def test_feixe_de_proximidade_quase_trava_no_jogador(guilty):
    """Correndo a 500 px/s ele não escapa da ponta (raio de 50)."""
    guilty.cd['proximidade'] = 0
    _perto(guilty)
    for i in range(25):
        guilty.jogador.posicao.y += 500 * DT
        _passo(guilty)
        if i > 6:
            assert guilty.feixe_proximidade.mira_atual.distance_to(guilty.jogador.posicao) < 20


def test_feixes_sao_vermelhos(guilty):
    for feixe in (guilty.feixe_proximidade, guilty.feixe_laser, guilty.feixe_fase3):
        r, g, b = feixe.color
        assert r == 255 and g < 50 and b < 50


# ── Fase 2: decisão e laser ──────────────────────────────────────────────────
def test_fase_2_anda_bem_mais_do_que_ataca(guilty):
    _ir_para_fase(guilty, 2)
    random.seed(3)
    guilty.invocar_luz = lambda: escolhas.append('luz')
    escolhas = []
    for _ in range(3000):
        _esperas(guilty, 0)
        antes = len(escolhas)
        if guilty.escolher_habilidade(0) == 'laser':
            escolhas.append('laser')
        elif len(escolhas) == antes:
            escolhas.append('passear')
    c = Counter(escolhas)
    assert c['passear'] > 2 * c['luz'] > 0 and c['passear'] > 2 * c['laser'] > 0


def test_laser_da_fase_2_carrega_parado_e_dispara_4_segundos(guilty):
    _ir_para_fase(guilty, 2)
    guilty.iniciar('laser')
    _passo(guilty)
    pos = V(guilty.posicao)
    assert guilty.feixe_ativo is None and guilty.animador.clip == 'vermelho'
    carga = _ate(guilty, lambda: guilty.feixe_ativo is not None)
    assert carga == pytest.approx(1.0, abs=0.06)
    tiro = _ate(guilty, lambda: guilty.feixe_ativo is None)
    assert tiro == pytest.approx(4.0, abs=0.06) and guilty.posicao == pos
    assert guilty.game.camera.shake_intensidade >= CFG.laser.shake


# ── Fase 2: super sentinelas ─────────────────────────────────────────────────
def test_super_sentinelas_em_triangulo_equilatero(guilty):
    _ir_para_fase(guilty, 2)
    avisos = guilty.chover_super_sentinelas()
    centro = guilty.jogador.posicao
    angulos = sorted((a.posicao - centro).as_polar()[1] % 360 for a in avisos)
    assert len(avisos) == 3
    assert all(a.posicao.distance_to(centro) == pytest.approx(CFG.super_dist) for a in avisos)
    assert [angulos[1] - angulos[0], angulos[2] - angulos[1]] == pytest.approx([120, 120])
    menor, maior = ARTILHARIA_PRESETS['guilty_sentinela'], ARTILHARIA_PRESETS['guilty_super_sentinela']
    assert maior.raio_explosao > menor.raio_explosao and maior.dano > menor.dano
    assert CFG.shake_super > CFG.shake_chuva


def test_super_sentinelas_saem_dos_3_avisos_invisiveis(guilty):
    _ir_para_fase(guilty, 2)
    avisos = guilty.chover_super_sentinelas()
    _ate(guilty, lambda: guilty.super_sentinelas)
    assert [type(s) for s in guilty.super_sentinelas] == [SentinelMajor] * 3
    assert all(s.alpha_atual == 0 for s in guilty.super_sentinelas)
    assert all(min(s.posicao.distance_to(a.posicao) for s in guilty.super_sentinelas) < 1 for a in avisos)


def test_super_sentinelas_tem_teto(guilty):
    _ir_para_fase(guilty, 2)
    for _ in range(CFG.super_max_vivas // 3):
        guilty.super_sentinelas += [SentinelMajor(V(0, 0), guilty.game) for _ in range(3)]
    assert guilty.chover_super_sentinelas() == []
    for s in guilty.super_sentinelas[:3]:
        s.kill()
    assert len(guilty.chover_super_sentinelas()) == 3


# ── Fase 2: infestação ───────────────────────────────────────────────────────
def test_infestacao_cinco_floods_na_tela_do_jogador(guilty):
    _ir_para_fase(guilty, 2)
    aviso = guilty.infestar()
    d = aviso.posicao - guilty.jogador.posicao
    assert abs(d.x) <= 640 and abs(d.y) <= 360
    _ate(guilty, lambda: guilty.floods)
    assert len(guilty.floods) == 5
    assert all(type(f) in (FloodMarine, FloodElite, FloodCarry) for f in guilty.floods)
    assert all(f.posicao.distance_to(aviso.posicao) <= aviso.cfg.raio_explosao for f in guilty.floods)
    assert len(entity_manager.particulas_grupo) >= 200
    assert guilty.game.camera.shake_intensidade == CFG.shake_flood


def test_infestacao_sorteia_as_tres_formas(guilty):
    _ir_para_fase(guilty, 2)
    for _ in range(8):
        guilty._brotar_flood(guilty._aviso(V(0, 0), 'guilty_flood', None))
    assert {type(f) for f in guilty.floods} == {FloodMarine, FloodElite, FloodCarry}


@pytest.mark.parametrize('dentro', [True, False])
def test_infestacao_deixa_lento_quem_esta_na_area(guilty, dentro):
    _ir_para_fase(guilty, 2)
    j = guilty.jogador
    aviso = guilty.infestar()
    raio = aviso.cfg.raio_explosao
    j.posicao.update(aviso.posicao + V(raio * (0.5 if dentro else 1.2), 0))
    guilty.posicao.update(aviso.posicao + V(0, 3000))      # a barreira não entra na conta
    vida = j.vida_atual
    _ate(guilty, lambda: aviso.explodiu)
    assert j.status.tem(Lentidao) == dentro
    assert j.status.mult_velocidade == (0.5 if dentro else 1.0)
    assert (vida - j.vida_atual) == (aviso.cfg.dano if dentro else 0)


def test_infestacao_tem_teto(guilty):
    _ir_para_fase(guilty, 2)
    guilty.floods = [FloodElite(V(0, 0), guilty.game) for _ in range(CFG.flood_max_vivos)]
    assert guilty.infestar() is None


# ── Fase 2: luz visível ──────────────────────────────────────────────────────
def _luz_longe_do_guilty(g):
    """Uma cadeia em cima do jogador, com o Guilty a 800 px (fora de todas)."""
    g.invocar_luz()
    return g.luz


def test_luz_sao_4_em_cadeia_no_mesmo_centro_cada_vez_maiores(guilty):
    _ir_para_fase(guilty, 2)
    guilty.posicao.update(CENTRO)
    luz = _luz_longe_do_guilty(guilty)
    centro = V(guilty.jogador.posicao)
    vistos, feixes = [], set()
    while luz.alive():
        if luz.aviso not in vistos:
            vistos.append(luz.aviso)
        _passo(guilty)
        feixes.update(_sprites(FeixeDoCeu))
    assert len(vistos) == len(feixes) == 4
    assert all(a.posicao == centro for a in vistos) and all(f.posicao == centro for f in feixes)
    raios, danos = [a.cfg.raio_explosao for a in vistos], [a.cfg.dano for a in vistos]
    assert raios == sorted(set(raios)) and danos == sorted(set(danos))
    assert sum(a.cfg.duracao for a in vistos) <= 3000      # dinâmica


def test_o_feixe_cai_junto_com_o_estouro(guilty):
    _ir_para_fase(guilty, 2)
    luz = _luz_longe_do_guilty(guilty)
    primeiro = luz.aviso
    _ate(guilty, lambda: _sprites(FeixeDoCeu))
    inicio = relogio.agora()
    assert not primeiro.explodiu
    _ate(guilty, lambda: primeiro.explodiu)
    assert relogio.agora() - inicio <= CFG.luz_raio_antes_ms + 1000 * DT
    assert luz.aviso is not primeiro                        # e já abriu a próxima


def test_luz_fere_o_jogador_4_vezes_se_ele_ficar(guilty):
    _ir_para_fase(guilty, 2)
    j = guilty.jogador
    vida = j.vida_atual
    luz = _luz_longe_do_guilty(guilty)
    _ate(guilty, lambda: not luz.alive())
    assert vida - j.vida_atual == sum(ARTILHARIA_PRESETS[p].dano for p in CFG.luz_presets)


def test_luz_nao_para_a_ronda_nem_muda_a_cor(guilty):
    _ir_para_fase(guilty, 2)
    luz = _luz_longe_do_guilty(guilty)
    pos = V(guilty.posicao)
    while luz.alive():
        _passo(guilty)
        assert guilty.animador.clip == 'azul' and guilty.rotina is None
    assert guilty.posicao.distance_to(pos) > 200


def _aviso_da_luz(g, preset, distancia):
    return ArtilhariaAviso(g.posicao + V(distancia, 0), (entity_manager.all_sprites,), g.game, dono='BOSS',
                           preset=preset, fonte=g)


def test_a_propria_luz_tira_5_por_cento_com_barreira_e_tudo(guilty):
    _ir_para_fase(guilty, 2)
    vida = guilty.vida
    assert guilty.atingido_pela_luz(_aviso_da_luz(guilty, 'guilty_luz_2', 100))
    assert vida - guilty.vida == pytest.approx(guilty.vida_maxima * 0.05) and guilty.barreira_ativa
    raio = ARTILHARIA_PRESETS['guilty_luz_2'].raio_explosao
    vida = guilty.vida
    assert not guilty.atingido_pela_luz(_aviso_da_luz(guilty, 'guilty_luz_2', raio + CFG.raio_corpo + 1))
    assert guilty.vida == vida


def test_uma_cadeia_inteira_em_cima_dele_tira_4_golpes(guilty):
    _ir_para_fase(guilty, 2)
    guilty.rondar = lambda agora, dt: None                  # parado no meio dela
    vida = guilty.vida
    luz = LuzVisivel(guilty, guilty.posicao)
    _ate(guilty, lambda: not luz.alive())
    assert vida - guilty.vida == pytest.approx(guilty.vida_maxima * 0.20)


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


def test_virar_a_fase_desfaz_a_luz(guilty):
    _ir_para_fase(guilty, 2)
    luz = _luz_longe_do_guilty(guilty)
    aviso = luz.aviso
    _ir_para_fase(guilty, 3)
    assert not luz.alive() and not aviso.alive() and guilty.luz is None


def test_uma_luz_por_vez(guilty):
    _ir_para_fase(guilty, 2)
    luz = _luz_longe_do_guilty(guilty)
    guilty.invocar_luz()
    assert guilty.luz is luz and len(_sprites(LuzVisivel)) == 1


# ── Fase 3 ───────────────────────────────────────────────────────────────────
def _fase3(g):
    _ir_para_fase(g, 2)
    g.wait = 0
    _ir_para_fase(g, 3)


def test_fase_3_e_so_teleporte_pausa_e_laser(guilty):
    _fase3(guilty)
    _esperas(guilty, 0)
    vistos = set()
    for _ in range(round(12 / DT)):
        _passo(guilty)
        vistos.add(guilty.estado_habilidade)
    assert vistos == {'idle', 'teleporte'}
    assert _avisos() == [] and guilty.armadilha is None and guilty.luz is None


def test_teleporte_em_volta_do_jogador_com_os_dois_clarões(guilty):
    _fase3(guilty)
    _ate(guilty, lambda: guilty.em_teleporte)
    assert guilty.invulneravel and not guilty.alvejavel
    vfx = set()
    while guilty.em_teleporte:
        vfx.update(_sprites(TeleporteVFX))
        _passo(guilty)
    assert len(vfx) == 2
    assert CFG.tp_raio[0] - 1 <= guilty.posicao.distance_to(guilty.jogador.posicao) <= CFG.tp_raio[1] + 1
    assert guilty.alpha_atual == 255 and guilty.alvejavel and not guilty.invulneravel


def test_depois_do_teleporte_para_500_ms_e_dispara(guilty):
    _fase3(guilty)
    _ate(guilty, lambda: guilty.em_teleporte)
    _ate(guilty, lambda: not guilty.em_teleporte)
    pos = V(guilty.posicao)
    pausa = _ate(guilty, lambda: guilty.feixe_ativo is not None)
    assert pausa == pytest.approx(0.5, abs=0.05) and guilty.feixe_ativo is guilty.feixe_fase3
    _ate(guilty, lambda: guilty.feixe_ativo is None)
    assert guilty.posicao == pos


def test_laser_da_fase_3_e_mais_curto_mais_forte_e_segue_melhor():
    assert CFG.laser_fase3.duracao_ms < CFG.laser.duracao_ms
    assert CFG.laser_fase3.dps > CFG.laser.dps
    assert CFG.laser_fase3.suavizacao > CFG.laser.suavizacao
    assert sum(CFG.laser_fase3.cor) < sum(CFG.laser.cor)


def test_sem_ponto_valido_o_teleporte_fica_onde_esta(guilty):
    _fase3(guilty)
    guilty.verificar_posicao_valida = lambda p: False
    assert guilty.ponto_de_teleporte() == guilty.posicao


def test_interromper_o_teleporte_devolve_ao_mundo(guilty):
    _fase3(guilty)
    _ate(guilty, lambda: guilty.em_teleporte)
    _passo(guilty)
    guilty.interromper_rotina()
    assert not guilty.em_teleporte and guilty.alpha_atual == 255


# ── Sprites ──────────────────────────────────────────────────────────────────
def _cor_do_olho(imagem):
    """Média dos pixels vivos (saturados e claros) do quadro."""
    soma, n = [0, 0, 0], 0
    for x in range(imagem.get_width()):
        for y in range(imagem.get_height()):
            r, g, b, a = imagem.get_at((x, y))
            if a > 200 and max(r, g, b) > 150 and max(r, g, b) - min(r, g, b) > 80:
                soma = [soma[0] + r, soma[1] + g, soma[2] + b]
                n += 1
    return [c / n for c in soma]


def test_sprites_azul_e_vermelho_das_duas_versoes(guilty):
    quadros = guilty.sprites['right']
    assert len(quadros) == 4
    for clip, vermelho in (('azul', False), ('vermelho', True), ('azul_destruido', False),
                           ('vermelho_destruido', True)):
        r, _, b = _cor_do_olho(quadros[guilty.CLIPS[clip].quadros[0]])
        if vermelho:
            assert r > b, clip
        else:
            assert b > r * 1.5, clip


def test_fase_3_usa_os_destruidos(guilty):
    _fase3(guilty)
    _ate(guilty, lambda: guilty.em_teleporte)
    assert guilty.animador.clip == 'azul_destruido'
    _ate(guilty, lambda: guilty.feixe_ativo is not None)
    _passo(guilty)
    assert guilty.animador.clip == 'vermelho_destruido'


def test_fases_1_e_2_so_ficam_vermelhas_com_feixe_ou_carga(guilty):
    guilty.proxima_invocacao['chuva'] = guilty.proxima_invocacao['armadilha'] = 0
    for _ in range(round(3 / DT)):
        _passo(guilty)
        assert guilty.animador.clip == 'azul'
    _ir_para_fase(guilty, 2)
    guilty.proxima_invocacao['chuva_super'] = guilty.proxima_invocacao['infestacao'] = 0
    for _ in range(round(3 / DT)):
        _passo(guilty)
        assert guilty.animador.clip == 'azul'


def test_olho_acompanha_o_lado(guilty):
    guilty.animador.virar(1)
    assert guilty.olho.x > 0
    guilty.animador.virar(-1)
    assert guilty.olho.x < 0


# ── VFX ──────────────────────────────────────────────────────────────────────
def test_contador_so_na_fase_1_com_barreira(guilty):
    preta = pygame.Surface((1280, 720))

    def desenhou():
        preta.fill((0, 0, 0))
        guilty.hud_draw(preta)
        return pygame.mask.from_threshold(preta, (0, 0, 0), (1, 1, 1)).count() != 1280 * 720

    assert desenhou()
    guilty.sentinelas_derrotadas = 12
    assert desenhou() and guilty._contador[0] == 12
    _sem_barreira_fase1(guilty)
    assert not desenhou()
    _ir_para_fase(guilty, 2)
    assert not desenhou()


def test_brilho_azul_em_volta_dele(guilty):
    tela = pygame.Surface((400, 400))
    _sem_barreira_fase1(guilty)
    deslocamento = guilty.posicao - V(200, 200)
    guilty.draw(tela, deslocamento)
    r, _, b, _ = tela.get_at((200, 200 + 62))    # fora do sprite (raio 50), dentro do halo
    assert b > 20 and b > r * 2


def test_desenho_da_luta_inteira_sem_erro_nem_alocacao(novo_jogo, guilty):
    """As 3 fases desenhadas: o vfx não cria Surface por frame."""
    ir_para_fase(novo_jogo, 2)
    tela, zero = pygame.Surface((1280, 720)), V(0, 0)
    del guilty.verificar_posicao_valida
    guilty.posicao.update(guilty.jogador.posicao + V(-300, 0))
    deslocamento = guilty.jogador.posicao - V(640, 360)

    def desenhar():
        guilty.draw(tela, deslocamento)
        guilty.draw_laser(tela, deslocamento)
        guilty.hud_draw(tela)
        for s in entity_manager.all_sprites:
            if isinstance(s, (TeleporteVFX, FeixeDoCeu, ArmadilhaForerunner)):
                s.draw(tela, deslocamento)

    desenhar()
    with contar_alocacoes() as c:
        guilty.armar_armadilha()
        FeixeDoCeu(guilty.jogador.posicao, 340)
        TeleporteVFX(guilty.posicao)
        guilty.feixe_ativo = guilty.feixe_laser
        for _ in range(round(2 / DT)):
            _passo(guilty)
            with c.pausado():
                guilty.feixe_ativo = guilty.feixe_laser
            desenhar()
    assert c.total == 0, c.por_tipo
    guilty.draw(tela, zero)      # fora da tela: não desenha nem quebra


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


# ── Configuração ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize('trocas, trecho', [
    ({'pesos_fase2': {'passear': 1, 'laser': 2, 'luz': 1}}, 'passear precisa pesar mais'),
    ({'pesos_fase2': {'passear': 5, 'laser': 2}}, 'pesos_fase2 inválidos'),
    ({'cooldown': {'luz': (1, 2)}}, 'mesmas habilidades'),
    ({'intervalo': {'luz': (1, 2)}}, 'mesmas invocações'),
    ({'intervalo': {**CFG.intervalo, 'luz': (9, 2)}}, 'intervalo de "luz"'),
    ({'shake_luz': (1, 2)}, 'mesmo tamanho'),
    ({'proximidade_dist': 50}, 'passar da barreira'),
    ({'luz_dano_no_guilty': 1.5}, 'luz_dano_no_guilty'),
    ({'sentinelas_para_cair': 0}, 'sentinelas_para_cair'),
])
def test_config_invalida(trocas, trecho):
    with pytest.raises(ValueError, match=trecho):
        dataclasses.replace(CFG, **trocas)


@pytest.mark.parametrize('campo, valor', [('dps', 0), ('duracao_ms', -1), ('suavizacao', 0), ('suavizacao', 1.1)])
def test_feixe_invalido(campo, valor):
    with pytest.raises(ValueError):
        dataclasses.replace(CFG.laser, **{campo: valor})


def test_config_padrao_e_presets_existem():
    assert isinstance(GuiltyConfig(), GuiltyConfig) and isinstance(CFG.laser, FeixeConfig)
    for preset in ('guilty_sentinela', 'guilty_super_sentinela', 'guilty_flood', *CFG.luz_presets):
        assert preset in ARTILHARIA_PRESETS and math.isfinite(ARTILHARIA_PRESETS[preset].dano)
