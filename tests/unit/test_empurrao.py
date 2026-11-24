"""Knockback: `systems/empurrao.py` e o parâmetro da artilharia."""
import dataclasses
import math

import pygame
import pytest

from helpers import DT, blindar_jogador
from source.enemies.standard.grunt import GruntRed
from source.feats.skills.artilharia import ArtilhariaAviso, ArtilhariaConfig
from source.feats.skills.artilharia.config import ARTILHARIA_PRESETS
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


def test_tranco_vem_no_comeco_e_acaba(player):
    inicio = V(player.posicao)
    empurrar(player, inicio - V(50, 0), 200)
    _rodar(0.2)
    assert player.posicao.x - inicio.x > 150
    _rodar(2)
    assert empurrao_ativo(player) == V(0, 0)


def test_origem_em_cima_do_alvo_nao_quebra(player):
    inicio = V(player.posicao)
    empurrar(player, inicio, 100)
    _rodar(1)
    assert player.posicao.distance_to(inicio) == pytest.approx(100, abs=4)


def test_vale_o_empurrao_mais_forte(player):
    empurrar(player, player.posicao - V(10, 0), 300)
    forte = empurrao_ativo(player)
    empurrar(player, player.posicao + V(10, 0), 50)
    assert empurrao_ativo(player) == forte
    empurrar(player, player.posicao + V(10, 0), 500)
    assert empurrao_ativo(player).x < 0


@pytest.mark.parametrize('forca', [0, -5, True, False, None, float('inf'), float('nan'), '9'])
def test_forca_invalida(player, forca):
    with pytest.raises(ValueError):
        empurrar(player, (0, 0), forca)


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


def test_inimigo_comum_se_move(novo_jogo):
    grunt = GruntRed(posicao=novo_jogo.player.posicao + V(200, 0), game=novo_jogo)
    inicio = V(grunt.posicao)
    empurrar(grunt, inicio - V(10, 0), 150)
    _rodar(1)
    assert grunt.posicao.x - inicio.x == pytest.approx(150, abs=4)
    assert grunt.rect.center == (round(grunt.posicao.x), round(grunt.posicao.y))


def test_quem_sai_do_mundo_sai_da_lista(novo_jogo):
    grunt = GruntRed(posicao=novo_jogo.player.posicao + V(200, 0), game=novo_jogo)
    empurrar(grunt, grunt.posicao - V(10, 0), 150)
    grunt.kill()
    _rodar(DT)
    assert empurrao._ativos == {}
    empurrar(grunt, grunt.posicao - V(10, 0), 150)      # morto: ignora
    assert empurrao._ativos == {}


def test_partida_nova_limpa(novo_jogo):
    empurrar(novo_jogo.player, novo_jogo.player.posicao - V(10, 0), 300)
    novo_jogo._resetar_estado_jogo()
    assert empurrao._ativos == {}


def test_jogo_aplica_a_cada_passo(novo_jogo):
    novo_jogo.spawner.update = lambda dt: None
    inicio = V(novo_jogo.player.posicao)
    empurrar(novo_jogo.player, inicio - V(0, 50), 120)
    for _ in range(60):
        novo_jogo.update(DT)
    assert novo_jogo.player.posicao.y > inicio.y + 60


# ── Artilharia ───────────────────────────────────────────────────────────────
def test_padrao_nao_empurra():
    assert ArtilhariaConfig().knockback is False
    sem = [nome for nome, cfg in ARTILHARIA_PRESETS.items() if cfg.knockback]
    assert sem == [nome for nome in ARTILHARIA_PRESETS if nome.startswith('scarab_')]


@pytest.mark.parametrize('valor', [0, -1, True, None, float('nan'), 'forte'])
def test_knockback_invalido(valor):
    with pytest.raises(ValueError):
        ArtilhariaConfig(knockback=valor)


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


def test_sem_knockback_nao_empurra(novo_jogo):
    _explodir(novo_jogo, novo_jogo.player.posicao + V(60, 60))
    assert empurrao_ativo(novo_jogo.player) == V(0, 0)


def test_fora_do_raio_nao_empurra(novo_jogo):
    _explodir(novo_jogo, novo_jogo.player.posicao + V(201, 0), knockback=90)
    assert empurrao_ativo(novo_jogo.player) == V(0, 0)


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


def test_artilharia_do_jogador_empurra_inimigo(novo_jogo):
    grunt = GruntRed(posicao=novo_jogo.player.posicao + V(300, 0), game=novo_jogo)
    aviso = ArtilhariaAviso(grunt.posicao - V(20, 0), (entity_manager.all_sprites,), novo_jogo, dono='PLAYER',
                            custom_config=ArtilhariaConfig(dano=0, raio_explosao=100, duracao=100, knockback=80))
    relogio.avancar(0.11)
    aviso.update(DT)
    assert empurrao_ativo(grunt).x > 0


def test_presets_do_scarab_do_menor_para_o_maior():
    passo, sismica = ARTILHARIA_PRESETS['scarab_passo'], ARTILHARIA_PRESETS['scarab_sismica']
    for campo in ('dano', 'raio_explosao', 'knockback'):
        assert getattr(sismica, campo) > getattr(passo, campo), campo
    assert math.isfinite(dataclasses.replace(passo, duracao=10).knockback)
