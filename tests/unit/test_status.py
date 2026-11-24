"""Sistema de status (buffs e debuffs): efeitos validados, acúmulo por tipo, duração, imunidade
dos bosses e o efeito de cada um no jogo (movimento, ataque, dano, cura, escudo, cadência, cegueira)."""
import importlib
import pathlib

import pygame
import pytest

from helpers import DT, voltar_ao_menu
from source.enemies.base.enemy_base import BaseEnemy
from source.enemies.standard.grunt import GruntRed
from source.systems.dano import DIRETO, PROJETIL, STATUS, Dano
from source.systems.entitymanager import entity_manager
from source.systems.entrada import ComandoJogador, Roteiro
from source.systems.estados import PAUSA
from source.systems.eventos import DANO_CAUSADO, eventos
from source.systems.gameclock import relogio
from source.systems.status import (IMUNIDADES_CHEFE, TICK_QUEIMADURA, Atordoamento, BuffCadencia,
                                   BuffDano, BuffVelocidade, Cegueira, Cura, Defesa, Escudo, Fraqueza,
                                   Lentidao, Queimadura, aplicar, atualizar_status, remover)
from source.systems.status import status as modulo_status

V = pygame.math.Vector2
RAIZ = pathlib.Path(__file__).resolve().parents[2]


def _grunt(game, deslocamento=V(300, 0), vida=1000):
    g = GruntRed(posicao=game.player.posicao + deslocamento, game=game)
    g.vida, g.escudo_atual, g.invencivel = vida, 0, False
    return g


def _passar(segundos):
    """Só o tempo e os status (sem spawner, entidades nem colisão)."""
    for _ in range(round(segundos / DT)):
        relogio.avancar(DT)
        atualizar_status(DT)


def _passar_jogo(game, segundos):
    """Tempo, status e entidades (sem spawner e sem colisão)."""
    for _ in range(round(segundos / DT)):
        relogio.avancar(DT)
        game._atualizar_status(DT)
        game._atualizar_entidades(DT)


def _ouvir_dano():
    recebidos = []
    eventos.assinar(DANO_CAUSADO, lambda **d: recebidos.append(d))
    return recebidos


# ── Efeitos: validação ──────────────────────────────────────────────────────
@pytest.mark.parametrize('criar', [
    lambda: Lentidao(0, 1000), lambda: Lentidao(1.01, 1000), lambda: Lentidao(0.5, 0),
    lambda: Lentidao(0.5, None), lambda: Lentidao(float('nan'), 1000),
    lambda: Atordoamento(0), lambda: Atordoamento(-5), lambda: Atordoamento(float('inf')),
    lambda: Queimadura(0, 1000), lambda: Queimadura(10, 1000, reducao_cura=1.5),
    lambda: Queimadura(10, 1000, reducao_cura=-0.1), lambda: Queimadura(10, None),
    lambda: Fraqueza(0, 1000), lambda: Fraqueza(30, 1000), lambda: Fraqueza(0.5, None),
    lambda: Cegueira(0, 1000), lambda: Cegueira(100, None),
    lambda: BuffDano(-0.1), lambda: BuffDano(30), lambda: BuffDano(0.5, 0),
    lambda: BuffVelocidade(0), lambda: BuffVelocidade(0.2, -1),
    lambda: BuffCadencia(1.0), lambda: BuffCadencia(0), lambda: BuffCadencia(0.5, 0),
    lambda: Defesa(1.0), lambda: Defesa(0), lambda: Defesa(-0.5), lambda: Defesa(90),
    lambda: Defesa(float('nan')), lambda: Defesa(0.5, 0), lambda: Defesa(0.5, float('inf')),
    lambda: Escudo(0), lambda: Escudo(float('inf')), lambda: Cura(-1), lambda: Cura(float('nan')),
])
def test_efeito_invalido_e_recusado(criar):
    with pytest.raises(ValueError):
        criar()


@pytest.mark.parametrize('fonte', ['arma', object(), 3])
def test_fonte_precisa_ser_entidade(player, fonte):
    with pytest.raises(ValueError, match='use chave='):
        aplicar(player, Lentidao(0.5, 1000), fonte=fonte)


def test_chave_separa_o_lugar_e_a_fonte_leva_o_credito(novo_jogo):
    grunt = _grunt(novo_jogo)
    player = novo_jogo.player
    recebidos = _ouvir_dano()
    aplicar(grunt, Queimadura(40, 1000), fonte=player, chave='arma A')
    aplicar(grunt, Queimadura(40, 1000), fonte=player, chave='arma B')
    assert len(grunt.status.ativos()) == 2
    _passar(1.5)
    assert grunt.vida == pytest.approx(1000 - 80)
    assert {r['dano'].fonte for r in recebidos} == {player}


# ── Modificadores e acúmulo ─────────────────────────────────────────────────
def test_sem_efeitos_os_multiplicadores_sao_exatamente_1(player):
    s = player.status
    assert (s.mult_velocidade, s.mult_dano_causado, s.mult_dano_recebido, s.mult_cooldown) == (1.0,) * 4
    assert not s.atordoado and s.reducao_cura == 0 and s.raio_cegueira is None


def test_lentidao_entre_fontes_vale_a_mais_forte(player):
    a, b = object(), object()
    aplicar(player, Lentidao(0.3, 1000), chave=a)
    aplicar(player, Lentidao(0.5, 1000), chave=b)
    assert player.status.mult_velocidade == pytest.approx(0.5)


def test_mesma_fonte_substitui_valores_e_renova_a_duracao(player):
    fonte = object()
    aplicar(player, Lentidao(0.5, 1000), chave=fonte)
    _passar(0.9)
    aplicar(player, Lentidao(0.2, 1000), chave=fonte)
    assert player.status.mult_velocidade == pytest.approx(0.8)
    assert len(player.status.ativos()) == 1
    _passar(0.9)
    assert player.status.tem(Lentidao)   # renovada: 1 s a partir da reaplicação


def test_buffs_de_velocidade_somam_e_combinam_com_lentidao(player):
    aplicar(player, BuffVelocidade(0.2), chave='a')
    aplicar(player, BuffVelocidade(0.3), chave='b')
    aplicar(player, Lentidao(0.5, 1000))
    assert player.status.mult_velocidade == pytest.approx(1.5 * 0.5)


# ── Duração ─────────────────────────────────────────────────────────────────
def test_efeito_acaba_na_duracao_e_tudo_volta_a_1(player):
    aplicar(player, Lentidao(0.5, 500))
    _passar(0.45)
    assert player.status.tem(Lentidao)
    _passar(0.1)
    assert not player.status.tem(Lentidao) and player.status.mult_velocidade == 1.0
    assert player.status not in modulo_status._com_efeito


def test_buff_sem_fim_so_sai_com_remover(player):
    chave = object()
    aplicar(player, BuffVelocidade(0.2), chave=chave)
    _passar(30)
    assert player.status.mult_velocidade == pytest.approx(1.2)
    assert not remover(player, BuffVelocidade, chave=object())
    assert remover(player, BuffVelocidade, chave=chave)
    assert player.status.mult_velocidade == 1.0


def test_status_nao_corre_fora_do_jogo(novo_jogo):
    """O tempo dos efeitos é o do update: pausa e level-up o congelam."""
    aplicar(novo_jogo.player, Lentidao(0.5, 100))
    novo_jogo.mudar_estado(PAUSA)
    for _ in range(60):
        novo_jogo.update(DT)
    assert novo_jogo.player.status.tem(Lentidao)


def test_nova_partida_esquece_os_efeitos(novo_jogo):
    grunt = _grunt(novo_jogo)
    aplicar(grunt, Lentidao(0.5, 10 ** 6))
    voltar_ao_menu(novo_jogo)
    novo_jogo.iniciar_novo_jogo()
    assert modulo_status._com_efeito == {}
    assert not novo_jogo.player.status.tem(Lentidao)


def test_morto_nao_recebe_nem_atualiza(novo_jogo):
    grunt = _grunt(novo_jogo)
    aplicar(grunt, Queimadura(100, 1000))
    grunt.kill()
    assert aplicar(grunt, Lentidao(0.5, 1000)) is False
    _passar(0.5)
    assert grunt.vida == 1000 and grunt.status not in modulo_status._com_efeito


# ── Imunidade dos bosses ────────────────────────────────────────────────────
def _classes_de_chefe():
    for pasta in ('bosses', 'minibosses'):
        for arquivo in (RAIZ / 'source' / 'enemies' / pasta).rglob('*.py'):
            modulo = '.'.join(arquivo.relative_to(RAIZ).with_suffix('').parts)
            importlib.import_module(modulo.removesuffix('.__init__'))
    pendentes, achadas = [BaseEnemy], set()
    while pendentes:
        for sub in pendentes.pop().__subclasses__():
            pendentes.append(sub)
            if sub.__module__.startswith(('source.enemies.bosses.', 'source.enemies.minibosses.')):
                achadas.add(sub)
    return achadas


def test_todo_boss_e_miniboss_e_imune_a_controle():
    classes = _classes_de_chefe()
    assert len(classes) >= 19
    sem = sorted(c.__name__ for c in classes if not IMUNIDADES_CHEFE <= c.imunidades_status)
    assert sem == []


# ── Atordoamento ────────────────────────────────────────────────────────────
def test_inimigo_atordoado_nao_anda_nem_atira_e_volta_depois(novo_jogo):
    grunt = _grunt(novo_jogo, V(400, 0))
    aplicar(grunt, Atordoamento(3000))
    pos = V(grunt.posicao)
    antes = set(entity_manager.projeteis_inimigos_grupo)
    _passar_jogo(novo_jogo, 2.9)
    assert grunt.posicao == pos
    assert not any(p.fonte is grunt for p in set(entity_manager.projeteis_inimigos_grupo) - antes)
    _passar_jogo(novo_jogo, 0.5)
    assert grunt.posicao != pos


def test_inimigo_atordoado_nao_causa_dano_de_contato(novo_jogo):
    player = novo_jogo.player
    grunt = _grunt(novo_jogo, V(0, 0))
    aplicar(grunt, Atordoamento(1000))
    assert grunt.inofensivo
    novo_jogo.collision_manager.update(DT)
    assert player.vida_atual == player.vida_maxima


def test_jogador_atordoado_nao_anda_nem_atira(novo_jogo, monkeypatch):
    player = novo_jogo.player
    monkeypatch.setattr(novo_jogo, 'entrada', Roteiro([(10 ** 6, ComandoJogador(direcao=(1, 0)))]))
    _grunt(novo_jogo, V(300, 0))
    aplicar(player, Atordoamento(1000))
    pos = V(player.posicao)
    antes = set(entity_manager.projeteis_jogador_grupo)
    _passar_jogo(novo_jogo, 0.9)
    assert player.posicao == pos
    assert set(entity_manager.projeteis_jogador_grupo) == antes
    _passar_jogo(novo_jogo, 0.5)
    assert player.posicao.x > pos.x
    assert set(entity_manager.projeteis_jogador_grupo) - antes


# ── Dano: buff de quem causa × fraqueza de quem recebe ──────────────────────
def test_buff_de_dano_do_jogador_vale_nos_tiros_dele(novo_jogo):
    grunt = _grunt(novo_jogo)
    aplicar(novo_jogo.player, BuffDano(0.5))
    grunt.receber_dano(Dano(100, PROJETIL, novo_jogo.player))
    assert grunt.vida == 1000 - 150


def test_fraqueza_soma_entre_fontes_e_multiplica_com_o_buff(novo_jogo):
    grunt = _grunt(novo_jogo)
    aplicar(grunt, Fraqueza(0.5, 1000), chave='a')
    aplicar(grunt, Fraqueza(0.5, 1000), chave='b')
    aplicar(novo_jogo.player, BuffDano(0.5))
    grunt.receber_dano(Dano(100, PROJETIL, novo_jogo.player))
    assert grunt.vida == pytest.approx(1000 - 100 * 1.5 * 2.0)


def test_defesa_reduz_o_dano_do_inimigo_e_do_jogador(novo_jogo):
    grunt = _grunt(novo_jogo)
    aplicar(grunt, Defesa(0.9))
    grunt.receber_dano(Dano(100, PROJETIL, novo_jogo.player))
    assert grunt.vida == pytest.approx(1000 - 10)
    player = novo_jogo.player
    aplicar(player, Defesa(0.25, 1000))
    player.receber_dano(Dano(100, DIRETO))
    assert player.vida_atual == pytest.approx(player.vida_maxima - 75)


def test_defesa_entre_fontes_multiplica_e_nunca_chega_a_100(player):
    aplicar(player, Defesa(0.5), chave='a')
    aplicar(player, Defesa(0.5), chave='b')
    assert player.status.mult_dano_recebido == pytest.approx(0.25)
    for chave in 'cdefgh':
        aplicar(player, Defesa(0.99), chave=chave)
    assert player.status.mult_dano_recebido > 0


# ── Queimadura ──────────────────────────────────────────────────────────────
def test_queimadura_da_o_dps_total_em_ticks_com_a_fonte(novo_jogo):
    grunt = _grunt(novo_jogo)
    fonte = novo_jogo.player
    recebidos = _ouvir_dano()
    aplicar(grunt, Queimadura(40, 1000), fonte=fonte)
    _passar(1.5)
    assert len(recebidos) == round(1.0 / TICK_QUEIMADURA)
    assert all(r['dano'].tipo == STATUS and r['dano'].fonte is fonte for r in recebidos)
    assert grunt.vida == pytest.approx(1000 - 40)


def test_queimadura_de_fontes_diferentes_soma(novo_jogo):
    grunt = _grunt(novo_jogo)
    aplicar(grunt, Queimadura(40, 1000), chave='a')
    aplicar(grunt, Queimadura(20, 1000), chave='b')
    _passar(1.5)
    assert grunt.vida == pytest.approx(1000 - 60)


def test_queimadura_no_jogador_ignora_iframes_sem_liga_los(player):
    player.invencivel = True
    aplicar(player, Queimadura(40, 500))
    _passar(0.3)
    assert player.vida_atual < player.vida_maxima
    player.invencivel = False
    _passar(0.3)
    assert not player.invencivel
    assert player.vida_atual == pytest.approx(player.vida_maxima - 20)


def test_queimadura_corta_a_cura_pelo_maior_corte(player):
    player.vida_atual = 100
    aplicar(player, Queimadura(1, 10 ** 6, reducao_cura=0.25), chave='a')
    aplicar(player, Queimadura(1, 10 ** 6, reducao_cura=0.5), chave='b')
    aplicar(player, Cura(100))
    assert player.vida_atual == 150


# ── Cura e escudo ───────────────────────────────────────────────────────────
def test_cura_vai_ate_o_maximo(novo_jogo):
    grunt = _grunt(novo_jogo, vida=10)
    grunt.vida_maxima = 50
    aplicar(grunt, Cura(1000))
    assert grunt.vida == 50


def test_escudo_vai_ate_o_maximo_e_sem_maximo_nao_faz_nada(novo_jogo):
    player = novo_jogo.player
    aplicar(player, Escudo(50))
    assert player.escudo_atual == 0                  # sem escudo máximo
    player.adicionar_escudo(100)
    player.escudo_atual = 70
    aplicar(player, Escudo(50))
    assert player.escudo_atual == 100
    grunt = _grunt(novo_jogo)
    grunt.escudo_maximo, grunt.escudo_atual = 40, 0
    aplicar(grunt, Escudo(15))
    assert grunt.escudo_atual == 15


# ── Cadência ────────────────────────────────────────────────────────────────
def test_cadencia_encolhe_o_cooldown_das_armas(novo_jogo):
    arma = novo_jogo.player.armas['assault_rifle']
    _grunt(novo_jogo, V(300, 0))
    arma.ultimo_tiro = relogio.agora()
    relogio.avancar(arma.cooldown * 0.6 / 1000)
    antes = len(entity_manager.projeteis_jogador_grupo)
    arma.update(DT)
    assert len(entity_manager.projeteis_jogador_grupo) == antes      # 60% do cooldown: ainda não
    aplicar(novo_jogo.player, BuffCadencia(0.5, 1000))
    arma._proxima_busca = 0
    arma.update(DT)
    assert len(entity_manager.projeteis_jogador_grupo) > antes       # com -50%, já pode
