"""Energy Sword: cada lâmina acerta cada inimigo uma vez por volta, com a forma que está na tela.

Regressão de 2026-11-24: a lâmina perfura infinito e não lembrava quem já tinha acertado, então
batia no mesmo alvo a cada frame (60× por segundo, por lâmina) e apagava qualquer boss."""
import pygame
import pytest

from helpers import DT
from source.enemies.standard.grunt import GruntRed
from source.feats.projetil import EnergySwordProj
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio

V = pygame.math.Vector2
VIDA = 10 ** 6


@pytest.fixture
def alvo(novo_jogo):
    """Grunt imóvel (ninguém chama o update dele), no meio da faixa varrida pela lâmina."""
    grunt = GruntRed(posicao=novo_jogo.player.posicao + V(90, 0), game=novo_jogo)
    grunt.vida, grunt.escudo_atual = VIDA, 0
    grunt.rect.center = grunt.posicao
    return grunt


def _lamina(game, angulo=0, velocidade=360, duracao=60_000, dano=5):
    return EnergySwordProj(posicao_inicial=game.player.posicao, grupos=(entity_manager.all_sprites,), game=game,
                           dano=dano, angulo_inicial=angulo, duracao=duracao,
                           velocidade_rotacao=velocidade, distancia_orbita=130)


def _girar(game, lamina, graus):
    for _ in range(round(graus / (lamina.velocidade_rotacao * DT))):
        relogio.avancar(DT)
        lamina.update(DT)
        game.collision_manager.update(DT)


@pytest.mark.parametrize('voltas', [1, 2, 3])
def test_um_acerto_por_volta(novo_jogo, alvo, voltas):
    lamina = _lamina(novo_jogo, angulo=-180)        # começa do lado oposto ao alvo
    _girar(novo_jogo, lamina, 360 * voltas)
    assert VIDA - alvo.vida == 5 * voltas


def test_lamina_parada_no_alvo_acerta_uma_vez_so(novo_jogo, alvo):
    lamina = _lamina(novo_jogo, velocidade=0)
    for _ in range(120):
        relogio.avancar(DT)
        lamina.update(DT)
        novo_jogo.collision_manager.update(DT)
    assert VIDA - alvo.vida == 5


def test_a_mesma_passada_acerta_varios_alvos(novo_jogo, alvo):
    outro = GruntRed(posicao=novo_jogo.player.posicao + V(0, 90), game=novo_jogo)
    outro.vida, outro.escudo_atual = VIDA, 0
    outro.rect.center = outro.posicao
    _girar(novo_jogo, _lamina(novo_jogo, angulo=-180), 360)
    assert VIDA - alvo.vida == VIDA - outro.vida == 5


def test_ativacao_inteira_tem_dano_limitado(novo_jogo, alvo):
    """A arma de verdade, nível 1: 120°/s por 5 s = no máximo 2 passadas (antes: centenas)."""
    novo_jogo.event_manager._aplicar_escolha_de_upgrade('energy_sword')
    arma = novo_jogo.player.armas['energy_sword']
    arma.disparar()
    laminas = [s for s in entity_manager.all_sprites if isinstance(s, EnergySwordProj)]
    for _ in range(round(arma.duracao / 1000 / DT) + 30):
        relogio.avancar(DT)
        for lamina in laminas:
            lamina.update(DT)
        novo_jogo.collision_manager.update(DT)
    passadas = int(arma.duracao / 1000 * arma.velocidade_rotacao // 360) + 1
    assert 0 < VIDA - alvo.vida <= arma.dano * arma.num_listas * passadas
    assert not any(lamina.alive() for lamina in laminas)
