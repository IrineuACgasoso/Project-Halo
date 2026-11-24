"""Knockback: `systems/empurrao.py` e o parâmetro da artilharia."""

import pygame
import pytest

from helpers import DT, blindar_jogador
from source.enemies.standard.grunt import GruntRed
from source.feats.skills.artilharia import ArtilhariaAviso, ArtilhariaConfig
from source.systems import empurrao
from source.systems.empurrao import atualizar_empurroes, empurrao_ativo, empurrar, limpar_empurroes
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.systems.mapmanager.grade_paredes import GradeParedes

V = pygame.math.Vector2


@pytest.fixture(autouse=True)
def _sem_sobras():
    limpar_empurroes()
    yield
    limpar_empurroes()


def _rodar(segundos, grade=None, dt=DT):
    for _ in range(round(segundos / dt)):
        atualizar_empurroes(dt, grade)


# ── empurrar ─────────────────────────────────────────────────────────────────
@pytest.mark.parametrize('dt', [1 / 60, 1 / 30, 1 / 120])
def test_anda_a_forca_para_longe_da_origem(player, dt):
    inicio = V(player.posicao)
    empurrar(player, inicio - V(50, 0), 200)
    _rodar(2, dt=dt)
    assert player.posicao.x - inicio.x == pytest.approx(200, abs=4)
    assert player.posicao.y == pytest.approx(inicio.y)
    assert player.hitbox.center == player.rect.center == (round(player.posicao.x), round(player.posicao.y))


def test_origem_em_cima_do_alvo_nao_quebra(player):
    inicio = V(player.posicao)
    empurrar(player, inicio, 100)
    _rodar(1)
    assert player.posicao.distance_to(inicio) == pytest.approx(100, abs=4)


def test_nao_atravessa_parede(player):
    inicio = V(player.posicao)
    x = inicio.x + 120
    grade = GradeParedes([{'pontos': [(x, inicio.y - 400), (x, inicio.y + 400)]}])
    empurrar(player, inicio - V(50, 0), 900)
    _rodar(1, grade)
    assert player.posicao.x < x


def test_boss_nao_se_move(novo_jogo):
    novo_jogo.spawner.spawnar('hunter')
    hunter = novo_jogo.sessao.boss_atual
    inicio = V(hunter.posicao)
    empurrar(hunter, inicio - V(10, 0), 300)
    _rodar(0.5)
    assert hunter.posicao == inicio


def test_quem_sai_do_mundo_sai_da_lista(novo_jogo):
    grunt = GruntRed(posicao=novo_jogo.player.posicao + V(200, 0), game=novo_jogo)
    empurrar(grunt, grunt.posicao - V(10, 0), 150)
    grunt.kill()
    _rodar(DT)
    assert empurrao._ativos == {}
    empurrar(grunt, grunt.posicao - V(10, 0), 150)      # morto: ignora
    assert empurrao._ativos == {}


# ── Artilharia ───────────────────────────────────────────────────────────────


def _explodir(game, centro, **cfg):
    blindar_jogador(game.player)
    aviso = ArtilhariaAviso(centro, (entity_manager.all_sprites,), game, dono='BOSS',
                            custom_config=ArtilhariaConfig(dano=10, raio_explosao=200, duracao=100, **cfg))
    relogio.avancar(0.11)
    aviso.update(DT)
    return aviso


def test_explosao_empurra_para_longe_do_centro(novo_jogo):
    jogador = novo_jogo.player
    _explodir(novo_jogo, jogador.posicao + V(60, 60), knockback=90)
    vel = empurrao_ativo(jogador)
    assert vel.x < 0 and vel.y < 0 and vel.x == pytest.approx(vel.y)
    assert vel.length() == pytest.approx(90 * empurrao.DECAIMENTO)


def test_tick_de_dot_nao_empurra(novo_jogo):
    aviso = _explodir(novo_jogo, novo_jogo.player.posicao + V(60, 0), knockback=90, dot=True,
                      dano_por_segundo=5, impacto_com_dot=True)
    assert empurrao_ativo(novo_jogo.player).length() > 0
    limpar_empurroes()
    vida = novo_jogo.player.vida_atual
    relogio.avancar(1.1)
    aviso.update(DT)
    assert novo_jogo.player.vida_atual < vida
    assert empurrao_ativo(novo_jogo.player) == V(0, 0)
