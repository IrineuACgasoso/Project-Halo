"""Skill de invisibilidade (`feats/skills/invisibilidade`): fases, tempos, alpha, encerrar e clarão;
e a regra do jogo: invisível nunca é mirado, mas pode ser atingido e distorce o cenário."""
import math
import pathlib

import pygame
import pytest

from helpers import DT, blindar_jogador, contar_alocacoes, simular
from source.enemies.standard.elite import Elite
from source.enemies.standard.grunt import GruntRed
from source.feats.grenades import FuelRodGrenade
from source.feats.projetil import M50, ProjetilNeedler
from source.feats.skills.invisibilidade import (FADE_IN, FADE_OUT, INVISIBILIDADE_PRESETS, OCULTO,
                                                Invisibilidade, InvisibilidadeConfig)
from source.feats.skills.invisibilidade.distorcao import desenhar_distorcao
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.systems.levelup import ARMAS_REGISTRO

V = pygame.math.Vector2
RAIZ = pathlib.Path(__file__).resolve().parents[2]


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


def test_alpha_desce_fica_em_zero_e_volta(grunt):
    inv = _com(grunt, fade_out_ms=500, duracao_ms=500, fade_in_ms=500)
    assert grunt.alpha_atual == 255 and inv.intensidade == 0
    _passar(grunt, 250)
    assert grunt.alpha_atual == pytest.approx(127, abs=3) and inv.intensidade == pytest.approx(0.5, abs=0.01)
    _passar(grunt, 300)
    assert inv.fase == OCULTO and grunt.alpha_atual == 0 and grunt.image.get_alpha() == 0
    assert inv.intensidade == 1
    _passar(grunt, 700)
    assert inv.fase == FADE_IN and 0 < grunt.alpha_atual < 255
    _passar(grunt, 400)
    assert grunt.invisibilidade is None and grunt.alpha_atual == 255 and grunt.image.get_alpha() == 255


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


def test_encerrar_no_meio_do_fade_out_volta_do_alpha_em_que_estava(grunt):
    inv = _com(grunt, fade_out_ms=1000, duracao_ms=1000, fade_in_ms=1000)
    _passar(grunt, 500)
    alpha = grunt.alpha_atual
    grunt.encerrar_invisibilidade()
    _passar(grunt, DT * 1000)
    assert inv.fase == FADE_IN and alpha <= grunt.alpha_atual <= alpha + 5   # sem piscar para 0
    assert grunt.alvejavel


def test_encerrar_de_novo_nao_reinicia_o_fade_in(grunt):
    _com(grunt, fade_out_ms=100, duracao_ms=100, fade_in_ms=500)
    _passar(grunt, 400)
    alpha = grunt.alpha_atual
    for _ in range(5):
        grunt.encerrar_invisibilidade()
        _passar(grunt, DT * 1000)
    assert grunt.alpha_atual > alpha


def test_visivel_nada_acontece(grunt):
    grunt.atualizar_invisibilidade(DT)
    grunt.encerrar_invisibilidade()
    grunt.trigger_flash()
    assert grunt.invisibilidade is None and grunt.fase_invisibilidade is None and grunt.alpha_atual == 255


def test_iniciar_de_novo_recomeca_sem_piscar(grunt):
    """Camuflar-se ainda reaparecendo parte do alpha em que está (não pula para 255)."""
    grunt.iniciar_invisibilidade('padrao')
    _passar(grunt, 1000)
    grunt.encerrar_invisibilidade()
    _passar(grunt, 250)
    alpha = grunt.alpha_atual
    assert 0 < alpha < 255
    grunt.iniciar_invisibilidade('padrao')
    assert grunt.fase_invisibilidade == FADE_OUT and grunt.alpha_atual == alpha and not grunt.alvejavel
    _passar(grunt, DT * 1000)
    assert 0 < grunt.alpha_atual <= alpha


# ── Clarão ───────────────────────────────────────────────────────────────────
def test_clarao_mostra_por_um_instante_sem_virar_alvo(grunt):
    inv = _com(grunt, fade_out_ms=100, duracao_ms=5000, fade_in_ms=100)
    _passar(grunt, 200)
    assert grunt.alpha_atual == 0
    grunt.trigger_flash(100, 60)
    _passar(grunt, DT * 1000)
    assert grunt.alpha_atual == 60 and not grunt.alvejavel
    assert inv.intensidade == 1            # a distorção não muda com o clarão
    _passar(grunt, 200)
    assert grunt.alpha_atual == 0


# ── Presets e config ─────────────────────────────────────────────────────────
@pytest.mark.parametrize('campos', [
    dict(fade_out_ms=0, duracao_ms=100, fade_in_ms=100), dict(fade_out_ms=100, duracao_ms=100, fade_in_ms=0),
    dict(fade_out_ms=100, duracao_ms=-1, fade_in_ms=100), dict(fade_out_ms=math.nan, duracao_ms=1, fade_in_ms=1),
    dict(fade_out_ms=1, duracao_ms=math.inf, fade_in_ms=1),
])
def test_config_invalida(campos):
    with pytest.raises(ValueError):
        InvisibilidadeConfig(**campos)


def test_preset_desconhecido(grunt):
    with pytest.raises(KeyError):
        grunt.iniciar_invisibilidade('nao_existe')


def test_presets_imutaveis():
    with pytest.raises(AttributeError):
        INVISIBILIDADE_PRESETS['padrao'].duracao_ms = 1


def test_elite_ferido_usa_a_skill(novo_jogo):
    elite = Elite(posicao=novo_jogo.player.posicao + V(500, 0), game=novo_jogo)
    elite.vida = elite.vida_base / 2
    elite.update(DT)
    assert elite.invisibilidade.cfg is INVISIBILIDADE_PRESETS['elite']


def test_a_maquina_antiga_saiu_do_codigo():
    """Um lugar só para a camuflagem: ninguém mexe em `invis_*` por fora da skill."""
    usos = [c.relative_to(RAIZ).as_posix() for c in (RAIZ / 'source').rglob('*.py')
            if 'invis_phase' in c.read_text(encoding='utf-8')]
    assert usos == []


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


def test_companheiro_ainda_coleta_itens(novo_jogo):
    """O item não tem `alvejavel`: continua alvo válido."""
    from source.feats.items import Items
    _criar_arma(novo_jogo, 'marine')
    marine = novo_jogo.player.armas['marine'].sprite_companion
    Items.spawn_drop(V(marine.posicao + V(60, 0)), (entity_manager.all_sprites, entity_manager.items_grupo),
                     exp_shard=(1, 100, 100))
    marine.logica_de_decisao()
    assert marine.estado_logico == 'COLETANDO'
    item = marine.alvo
    marine.logica_de_decisao()
    assert marine.alvo is item


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


def test_fuel_rod_nao_quica_no_invisivel(novo_jogo, grunt):
    p = novo_jogo.player
    granada = FuelRodGrenade(posicao_inicial=p.posicao, posicao_alvo=p.posicao + V(200, 0),
                             grupos=(entity_manager.all_sprites,), game=novo_jogo, dono='PLAYER',
                             inimigos_grupo=entity_manager.inimigos_grupo, quiques=2)
    grunt.posicao.update(granada.target_pos + V(60, 0))
    assert granada._alvo_do_quique() is grunt
    _ocultar(grunt)
    assert granada._alvo_do_quique() is None


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


def test_arbiter_camuflado_pode_ser_atingido(novo_jogo):
    novo_jogo.spawner.spawnar('arbiter')
    boss = novo_jogo.sessao.boss_atual
    boss.invencivel = False
    _ocultar(boss)
    assert not boss.invulneravel and not boss.alvejavel
    boss.trigger_flash(400, 120)                       # revelado ao golpear: continua sem ser mirado
    boss.atualizar_invisibilidade(DT)
    assert boss.alpha_atual > 0 and not boss.alvejavel


@pytest.mark.parametrize('estado', ['orbitando', 'ilusao'])
def test_jega_invisivel_pode_ser_atingido_e_nao_da_dano_de_contato(novo_jogo, estado):
    novo_jogo.spawner.spawnar('jega')
    jega = novo_jogo.sessao.boss_atual
    jega.invencivel = False
    assert not jega.inofensivo
    jega.estado = estado
    _ocultar(jega)
    assert not jega.invulneravel and not jega.alvejavel and jega.inofensivo
    assert jega.collision_rect is jega.hitbox


# ── Distorção ────────────────────────────────────────────────────────────────
def _tela_com_fundo(tamanho=(800, 600)):
    """Fundo com detalhe (listras): em fundo liso, deslocar não muda nada."""
    tela = pygame.Surface(tamanho)
    for x in range(0, tamanho[0], 4):
        pygame.draw.line(tela, (x % 256, 90, 160), (x, 0), (x, tamanho[1]), 2)
    return tela


def _na_tela(grunt, centro=(400, 300)):
    grunt.posicao.update(centro)
    grunt.sync_rect()
    return V(0, 0)


def test_invisivel_distorce_so_a_silhueta_dele(novo_jogo, grunt):
    desloc = _na_tela(grunt)
    _ocultar(grunt)
    tela = _tela_com_fundo()
    antes = tela.copy()
    desenhar_distorcao(tela, grunt, desloc)
    diferentes = [(x, y) for x in range(800) for y in range(600) if tela.get_at((x, y)) != antes.get_at((x, y))]
    assert len(diferentes) > 50
    quadro, mascara = grunt.rect, pygame.mask.from_surface(grunt.quadro_original)
    for x, y in diferentes:
        assert quadro.collidepoint(x, y)
        assert mascara.get_at((x - quadro.x, y - quadro.y))


def test_distorcao_aparece_ate_em_fundo_liso(novo_jogo, grunt):
    """O véu: sem ele, o inimigo sumiria por completo num chão de uma cor só."""
    desloc = _na_tela(grunt)
    _ocultar(grunt)
    tela = pygame.Surface((800, 600))
    tela.fill((40, 60, 40))
    desenhar_distorcao(tela, grunt, desloc)
    assert any(tela.get_at((x, y))[:3] != (40, 60, 40)
               for x in range(grunt.rect.left, grunt.rect.right) for y in range(grunt.rect.top, grunt.rect.bottom))


def test_visivel_e_fora_da_tela_nao_distorcem(novo_jogo, grunt):
    grunt.iniciar_invisibilidade('padrao')             # ainda visível: força 0
    desloc = _na_tela(grunt)
    tela = _tela_com_fundo()
    antes = pygame.image.tobytes(tela, 'RGB')
    desenhar_distorcao(tela, grunt, desloc)
    _ocultar(grunt)
    desenhar_distorcao(tela, grunt, desloc + V(5000, 0))
    assert pygame.image.tobytes(tela, 'RGB') == antes


@pytest.mark.parametrize('centro', [(0, 0), (800, 600), (3, 590)])
def test_distorcao_na_borda_da_tela_nao_quebra(novo_jogo, grunt, centro):
    desloc = _na_tela(grunt, centro)
    _ocultar(grunt)
    desenhar_distorcao(_tela_com_fundo(), grunt, desloc)


def test_distorcao_nao_aloca_por_frame(novo_jogo, grunt):
    desloc = _na_tela(grunt)
    _ocultar(grunt)
    tela = _tela_com_fundo()
    for _ in range(round(6 / DT)):                     # uma pulsação inteira: silhuetas, véus e rascunho no cache
        relogio.avancar(DT)
        desenhar_distorcao(tela, grunt, desloc)
    with contar_alocacoes() as c:
        for _ in range(round(6 / DT)):
            relogio.avancar(DT)
            desenhar_distorcao(tela, grunt, desloc)
    assert c.total == 0


@pytest.mark.parametrize('nome', ['elite', 'arbiter', 'jega', 'zealot'])
def test_renderer_distorce_todo_invisivel(novo_jogo, monkeypatch, nome):
    """O jogo desenha a distorção de qualquer inimigo camuflado, sem erro no Renderer."""
    from source.systems import renderer
    if nome == 'elite':
        inimigo = Elite(posicao=novo_jogo.player.posicao + V(100, 0), game=novo_jogo)
    else:
        novo_jogo.spawner.spawnar(nome)
        inimigo = novo_jogo.sessao.boss_atual
        inimigo.posicao.update(novo_jogo.player.posicao + V(100, 0))
        inimigo.sync_rect()
    vistos = []
    monkeypatch.setattr(renderer, 'desenhar_distorcao',
                        lambda tela, i, d: (vistos.append(i), desenhar_distorcao(tela, i, d)))
    novo_jogo.renderer._erros_logados.clear()
    novo_jogo.draw()
    assert vistos == []
    _ocultar(inimigo)
    novo_jogo.draw()
    assert vistos == [inimigo] and novo_jogo.renderer._erros_logados == set()
