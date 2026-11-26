"""Efeitos visuais: quebra de escudo (todo escudo), fogo da queimadura e o soco Spartan."""
import random

import pygame
import pytest

from helpers import contar_alocacoes, simular
from source.enemies.bosses.harbinger import Harbinger
from source.enemies.minibosses.hunter import Hunter
from source.enemies.minibosses.scarab import Scarab
from source.enemies.standard.grunt import GruntRed
from source.enemies.standard.jackal import Jackal
from source.feats.skills.onda_emp import OndaEMP
from source.systems.dano import AREA, Dano
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.systems.status import Queimadura, aplicar, remover

V = pygame.math.Vector2


def _particulas():
    return len(entity_manager.particulas_grupo)


# ── Quebra de escudo ─────────────────────────────────────────────────────────
@pytest.mark.parametrize('dano', [50, 80])   # exato e com sobra
@pytest.mark.parametrize('quem', ['jogador', 'inimigo'])
def test_quebrar_o_escudo_solta_fagulhas(novo_jogo, quem, dano):
    alvo = novo_jogo.player if quem == 'jogador' else GruntRed(posicao=V(600, 600), game=novo_jogo)
    alvo.adicionar_escudo(50)
    alvo.receber_dano(Dano(49, AREA, None, ignora_iframes=True))
    assert _particulas() == 0
    alvo.receber_dano(Dano(dano - 49, AREA, None, ignora_iframes=True))
    assert alvo.escudo_atual == 0 and _particulas() > 20


def test_fagulhas_caem_e_quebras_seguidas_nao_viram_chuva(novo_jogo):
    alvo = GruntRed(posicao=V(600, 600), game=novo_jogo)
    alvo.ao_quebrar_escudo()
    antes = _particulas()
    alvo.ao_quebrar_escudo()
    assert _particulas() == antes
    particula = next(iter(entity_manager.particulas_grupo))
    vy = particula.velocidade.y
    particula.update(0.1)
    assert particula.velocidade.y > vy


def test_emp_e_escudo_do_jackal_usam_o_mesmo_efeito(novo_jogo):
    p = novo_jogo.player
    p.adicionar_escudo(500)
    OndaEMP(V(p.posicao), (entity_manager.all_sprites,), novo_jogo, atacante=p).update(0.05)
    assert p.escudo_atual == 0 and _particulas() > 20
    jackal = Jackal(V(600, 600), novo_jogo)
    jackal.tipo, jackal.vida = 'blue', 0.1 * jackal.vida_base
    antes = _particulas()
    jackal.checar_quebra_escudo()
    assert jackal.escudo_quebrado and _particulas() > antes


# ── Fogo ─────────────────────────────────────────────────────────────────────
def _tela_com(game):
    game.camera.update(game.player.posicao)
    game.draw()
    return pygame.image.tobytes(game.tela, 'RGB')


@pytest.mark.parametrize('quem', ['jogador', 'grunt', Hunter, Scarab, Harbinger])
def test_queimando_desenha_fogo_sem_mexer_na_simulacao(novo_jogo, quem):
    p = novo_jogo.player
    if quem == 'jogador':
        alvo = p
    elif quem == 'grunt':
        alvo = GruntRed(posicao=p.posicao + V(150, 0), game=novo_jogo)
    else:
        alvo = quem(p.posicao + V(150, 0), novo_jogo)
    relogio.avancar(0.1)
    sem = _tela_com(novo_jogo)
    aplicar(alvo, Queimadura(1, 5000))
    estado = random.getstate()
    com = _tela_com(novo_jogo)
    assert com != sem and random.getstate() == estado
    with contar_alocacoes() as c:
        novo_jogo.renderer._draw_fogo(novo_jogo.tela, novo_jogo.camera.offset)
    assert c.total == 0, dict(c.por_tipo)
    remover(alvo, Queimadura)
    assert _tela_com(novo_jogo) == sem and not novo_jogo.renderer._erros_logados


def test_camuflado_nao_mostra_o_fogo(novo_jogo):
    alvo = GruntRed(posicao=novo_jogo.player.posicao + V(150, 0), game=novo_jogo)
    alvo._aplicar_alpha(0)
    sem = _tela_com(novo_jogo)
    aplicar(alvo, Queimadura(1, 5000))
    assert _tela_com(novo_jogo) == sem


def test_renovar_a_queimadura_antes_do_tick_nao_apaga_o_dano(novo_jogo):
    alvo = GruntRed(posicao=novo_jogo.player.posicao + V(3000, 0), game=novo_jogo)
    alvo.vida = alvo.vida_maxima = 1000
    for _ in range(60):
        aplicar(alvo, Queimadura(60, 1000), chave='x')
        alvo.status.atualizar(1 / 60)
    assert alvo.vida == pytest.approx(940, abs=1)


# ── Soco ─────────────────────────────────────────────────────────────────────
def test_soco_solta_faiscas_e_desenha_sem_erro(novo_jogo):
    p = novo_jogo.player
    inimigo = GruntRed(posicao=p.posicao + V(40, 0), game=novo_jogo)
    inimigo.vida = inimigo.vida_maxima = 10 ** 6
    p.configurar_espinhos(dano=10, cooldown=1000)
    p.espinho_disponivel = True
    p.contra_atacar_com_espinhos(inimigo)
    assert _particulas() > 50
    simular(novo_jogo, 0.5, desenhar_a_cada=1)
    assert not novo_jogo.renderer._erros_logados


# ── Lentidão ─────────────────────────────────────────────────────────────────
def test_lento_desenha_sem_mexer_na_simulacao_nem_alocar(novo_jogo):
    from source.feats.particulas.lentidao import preparar_lentidao
    from source.systems.status import Lentidao
    p = novo_jogo.player
    preparar_lentidao(q for lado in p.sprites.values() for q in lado)
    relogio.avancar(0.1)
    sem = _tela_com(novo_jogo)
    aplicar(p, Lentidao(0.5, 5000))
    estado = random.getstate()
    assert _tela_com(novo_jogo) != sem and random.getstate() == estado
    with contar_alocacoes() as c:
        novo_jogo.renderer._draw_lentidao(novo_jogo.tela, novo_jogo.camera.offset)
    assert c.total == 0, dict(c.por_tipo)
    remover(p, Lentidao)
    assert _tela_com(novo_jogo) == sem and not novo_jogo.renderer._erros_logados
