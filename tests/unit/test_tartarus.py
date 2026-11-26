"""Tartarus reformulado: barreira (-90%), sobrecarga e barra de esquivas, Rampage e ofegante, vórtice
(lentidão + puxão), escolha por alcance, Fúria e a Ativação do Halo."""
import pygame
import pytest

from helpers import DT, blindar_jogador
from source.enemies.bosses.tartarus.config import CFG
from source.enemies.bosses.tartarus.halo import BRANCO_TOTAL_MS, FADE_MS
from source.systems.dano import AREA, PROJETIL, Dano
from source.systems.empurrao import atualizar_empurroes, empurrao_ativo
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.systems.status import BuffVelocidade, Lentidao, atualizar_status

V = pygame.math.Vector2
CENTRO = V(1500, 1500)


@pytest.fixture
def tartarus(novo_jogo):
    novo_jogo.spawner.spawnar('tartarus')
    b = novo_jogo.sessao.boss_atual
    b.posicao.update(CENTRO)
    b.sync_rect()
    b.invencivel = False
    b.travamento = None               # sem anti-stuck: cada teste o chama quando quer
    b.verificar_posicao_valida = lambda p: True
    blindar_jogador(novo_jogo.player)
    _jogador_em(b, V(600, 0))
    b.cd = {nome: float('inf') for nome in b.cd}     # só o que o teste iniciar
    return b


def _jogador_em(b, deslocamento):
    b.jogador.posicao.update(b.posicao + deslocamento)
    b.jogador.sincronizar_rects()


def _passo(b):
    """Um passo sem paredes: status, empurrões, o Tartarus e o que ele criou (avisos, auras, purge, Halo)."""
    relogio.avancar(DT)
    atualizar_status(DT)
    atualizar_empurroes(DT, None)
    b.update(DT, None)
    for sprite in list(entity_manager.all_sprites):
        if sprite is not b.game.player and sprite not in entity_manager.inimigos_grupo:
            sprite.update(DT)


def _ate(b, condicao, limite_s=15):
    for _ in range(round(limite_s / DT)):
        if condicao():
            return
        _passo(b)
    raise AssertionError('não aconteceu')


def _ferir(b, valor):
    antes = b.vida
    b.receber_dano(Dano(valor, PROJETIL))
    return antes - b.vida


def test_barreira_corta_90_e_ofegante_toma_mais(tartarus):
    assert _ferir(tartarus, 100) == pytest.approx(100 * (1 - CFG.barreira_reducao))
    tartarus._sem_barreira_ate = tartarus._agora + 5000
    assert _ferir(tartarus, 100) == pytest.approx(100)
    tartarus._ofegante_ate = tartarus._agora + 5000
    assert _ferir(tartarus, 100) == pytest.approx(100 * CFG.ofegante_mult)


def test_golpe_que_erra_sobrecarrega_e_barra_cheia_derruba_e_chama_o_rampage(tartarus):
    tartarus._acertou = True
    tartarus._resolver_golpe()                       # acertou: nada
    assert tartarus.esquivas == 0 and tartarus.barreira_ativa

    tartarus._resolver_golpe()                       # errou: sobrecarga de 3 s
    assert tartarus.esquivas == 1 and not tartarus.barreira_ativa and not tartarus.quebra_longa
    _ate(tartarus, lambda: tartarus.barreira_ativa, limite_s=CFG.sobrecarga_ms / 1000 + 0.5)

    for _ in range(CFG.meta_esquivas - 1):
        tartarus._resolver_golpe()
    assert tartarus.quebra_longa and tartarus.esquivas == 0 and not tartarus.barreira_ativa
    tartarus._resolver_golpe()                       # durante a queda longa não conta
    assert tartarus.esquivas == 0
    _ate(tartarus, lambda: tartarus.estado_habilidade == 'chieftain_rampage', limite_s=1)


def test_rampage_esquivado_deixa_ofegante_e_atingido_nao(tartarus):
    _jogador_em(tartarus, V(3000, 0))                # longe: nenhuma explosão o pega
    tartarus.iniciar('rampage')
    _ate(tartarus, lambda: tartarus.ofegante, limite_s=8)
    assert tartarus.is_inofensivo
    _ate(tartarus, lambda: tartarus.rotina is None, limite_s=8)
    assert not tartarus.ofegante and not tartarus.is_inofensivo


@pytest.mark.parametrize('nome', ['vortice', 'onda', 'salto', 'rampage', 'punho', 'corrida', 'antistuck',
                                  'transicao'])
def test_toda_rotina_termina_e_devolve_as_flags(tartarus, nome):
    _jogador_em(tartarus, V(300, 0))
    tartarus.iniciar(nome)
    _ate(tartarus, lambda: tartarus.rotina is None, limite_s=15)
    assert not tartarus.no_ar and not tartarus.is_inofensivo and not tartarus.invulneravel
    assert tartarus.altura_z == 0


def test_vortice_deixa_lento_e_puxa_sem_engolir(tartarus):
    _jogador_em(tartarus, V(300, 0))
    tartarus.iniciar('vortice')
    _ate(tartarus, lambda: tartarus.jogador.status.tem(Lentidao), limite_s=1)
    dist_antes = tartarus.dist_jogador()
    for _ in range(30):
        _passo(tartarus)
    assert CFG.vortice_puxao_min <= tartarus.dist_jogador() < dist_antes


def test_aura_aplica_efeito_so_em_quem_esta_dentro(tartarus):
    from source.feats.auras import EnergyAura
    jogador = tartarus.jogador
    aura = EnergyAura(owner=tartarus, raio=200, dano_contato=0, game=tartarus.game, impenetravel=False,
                      efeitos=(Lentidao(0.5, 300),), duracao_ms=500)
    _jogador_em(tartarus, V(400, 0))
    aura.update(DT)
    assert not jogador.status.tem(Lentidao)
    _jogador_em(tartarus, V(150, 0))
    relogio.avancar(0.11)
    aura.update(DT)
    assert jogador.status.tem(Lentidao) and jogador.vida_atual == jogador.vida_maxima
    relogio.avancar(0.6)
    aura.update(DT)
    assert not aura.alive()


def test_onda_arremessa_e_deixa_lento(tartarus):
    from source.feats.skills.rect_strike import RectStrikeAviso
    jogador = tartarus.jogador
    jogador.invencivel = False
    jogador.receber_dano = lambda dano: None          # só o efeito do golpe importa aqui
    _jogador_em(tartarus, V(300, 0))
    aviso = RectStrikeAviso(V(tartarus.posicao), V(1, 0), (), tartarus.game, preset='tartarus_onda', fonte=tartarus)
    relogio.avancar(aviso.cfg.duracao / 1000 + 0.01)
    aviso.update(DT)
    assert empurrao_ativo(jogador).x > 0 and jogador.status.tem(Lentidao)


@pytest.mark.parametrize('dist,fase,esperado,proibido', [
    (1200, 1, 'salto', {'vortice', 'punho', 'corrida'}),
    (200, 1, 'vortice', {'salto', 'punho', 'corrida'}),
    (500, 1, 'onda', {'vortice', 'salto', 'punho', 'corrida'}),
    (600, 2, 'corrida', {'vortice'}),
])
def test_so_escolhe_o_que_alcanca(tartarus, dist, fase, esperado, proibido):
    tartarus.cd = {nome: 0 for nome in tartarus.cd}
    tartarus.fase, tartarus.fase_cfg = fase, tartarus.FASES[fase - 1]
    _jogador_em(tartarus, V(dist, 0))
    tartarus.contexto.atualizar(tartarus, DT)
    notas = tartarus.decisor.notas(tartarus)
    assert esperado in notas and not proibido & set(notas)


def test_furia_acelera_e_invoca_brutes_com_teto(tartarus):
    tartarus._sem_barreira_ate = tartarus._agora + 60000
    tartarus.receber_dano(Dano(tartarus.vida_maxima * 0.7, AREA))
    _ate(tartarus, lambda: tartarus.estado_habilidade == 'phase_shift', limite_s=1)
    _ate(tartarus, lambda: tartarus.rotina is None, limite_s=3)
    assert tartarus._furia and tartarus.status.tem(BuffVelocidade)
    tartarus.cd_brutes = 0
    _passo(tartarus)
    assert len(tartarus.brutes_invocados) == CFG.brutes_por_invocacao
    tartarus.cd_brutes = 0
    _passo(tartarus)
    tartarus.cd_brutes = 0
    _passo(tartarus)
    assert len([b for b in tartarus.brutes_invocados if b.alive()]) == CFG.max_brutes


def test_halo_zerado_termina_a_partida_em_branco(novo_jogo, tartarus):
    halo = tartarus.halo
    relogio.avancar(CFG.halo_ms / 1000)
    halo.update(DT)
    assert halo.disparou_em is not None and novo_jogo.estado_do_jogo == 'jogando'
    relogio.avancar((FADE_MS + BRANCO_TOTAL_MS) / 1000)
    halo.update(DT)
    assert novo_jogo.estado_do_jogo == 'game_over' and not halo.alive()
