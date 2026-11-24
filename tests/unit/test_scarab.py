"""Scarab: patas por ângulo, queda e núcleo, passos sincronizados, cobertura, golpes do corpo, armas
autônomas, sobrecarga, colapso, desenho em camadas e config."""

import pygame
import pytest

from helpers import DT, blindar_jogador, ir_para_fase
from source.enemies.minibosses.scarab.config import (CFG, CENTRO_CHAO, PATAS_VULNERAVEIS)
from source.feats.skills.artilharia.config import ARTILHARIA_PRESETS
from source.systems.dano import AREA, Dano, PROJETIL
from source.systems.empurrao import empurrao_ativo, limpar_empurroes
from source.systems.eventos import DANO_CAUSADO, eventos

V = pygame.math.Vector2


# ── Apoio ────────────────────────────────────────────────────────────────────
@pytest.fixture
def luta(novo_jogo):
    """Fase 3, jogador blindado e sem armas, Scarab no meio do mapa olhando para a esquerda."""
    limpar_empurroes()
    ir_para_fase(novo_jogo, 3)
    blindar_jogador(novo_jogo.player)
    novo_jogo.player.armas.clear()
    novo_jogo.spawner.update = lambda dt: None
    novo_jogo.spawner.spawnar('scarab')
    scarab = novo_jogo.sessao.boss_atual
    scarab.posicao.update(2300, 1400)
    scarab.sync_rect()
    olhar(scarab, 'left')
    calar(scarab)
    yield novo_jogo, scarab
    limpar_empurroes()


def olhar(scarab, lado):
    scarab.set_sprite_direction(-1 if lado == 'left' else 1)
    scarab.virar_em = None
    scarab.centro_chao = scarab.no_mundo(CENTRO_CHAO)
    scarab.animar()


def calar(scarab):
    """Armas e golpes só quando o teste mandar."""
    nunca = scarab._agora + 10 ** 9
    scarab.proximo_feixe = scarab.proxima_rajada = scarab.proximo_desembarque = nunca
    scarab.cd = dict.fromkeys(scarab.cd, nunca)


def por(game, ponto):
    p = game.player
    p.posicao.update(ponto)
    p.hitbox.center = p.rect.center = (round(p.posicao.x), round(p.posicao.y))


def no_angulo(scarab, nome, distancia=480):
    """Um ponto na direção do pé, a partir do centro do chão."""
    return scarab.centro_chao + (scarab.patas[nome].posicao - scarab.centro_chao).normalize() * distancia


def atras(scarab, distancia=480):
    return scarab.centro_chao + V(scarab.espelho * distancia, 0)


def atirar(game, scarab, valor=100):
    scarab.receber_dano(Dano(valor, PROJETIL, game.player))


def passos(game, n=1):
    for _ in range(n):
        game.update(DT)


def ate(game, condicao, segundos=10, cada=None):
    for _ in range(round(segundos / DT)):
        if cada:
            cada()
        game.update(DT)
        if condicao():
            return
    raise AssertionError('não aconteceu no tempo')


def quebrar(game, scarab, nome='frente'):
    por(game, no_angulo(scarab, nome))
    atirar(game, scarab, scarab.patas[nome].vida + 1)


def ouvir_dano_no_jogador(game):
    golpes = []
    eventos.assinar(DANO_CAUSADO, lambda alvo, dano, valor: golpes.append((dano, valor)) if alvo is game.player else None)
    return golpes


# ── Blindagem e patas ────────────────────────────────────────────────────────
@pytest.mark.parametrize('lado', ['left', 'right'])
@pytest.mark.parametrize('nome', PATAS_VULNERAVEIS)
def test_dano_vai_so_para_a_pata_do_angulo(luta, nome, lado):
    game, scarab = luta
    olhar(scarab, lado)
    por(game, no_angulo(scarab, nome))
    assert scarab.pata_exposta is scarab.patas[nome]
    vidas = {n: scarab.patas[n].vida for n in PATAS_VULNERAVEIS}
    vida = scarab.vida
    atirar(game, scarab, 40)
    assert scarab.vida == vida
    assert {n: vidas[n] - scarab.patas[n].vida for n in vidas} == {n: 40 if n == nome else 0 for n in vidas}


def test_sem_dano_de_contato_nem_com_o_jogador_dentro(luta):
    game, scarab = luta
    golpes = ouvir_dano_no_jogador(game)
    for ponto in (scarab.posicao, scarab.centro_chao, scarab.patas['centro'].posicao):
        por(game, ponto)
        game.collision_manager.update(DT)
    assert golpes == []


# ── Queda e núcleo ───────────────────────────────────────────────────────────
def test_pata_zerada_derruba_e_expoe_o_nucleo(luta):
    game, scarab = luta
    quebrar(game, scarab, 'tras')
    assert scarab.desabado and scarab.pose == 'caido' and scarab.estado_habilidade == 'queda'
    assert not scarab.nucleo_exposto      # ainda desabando
    passos(game, round(CFG.queda_ms / 1000 / DT) + 3)
    assert scarab.nucleo_exposto
    assert scarab.patas['tras'].quebrada


def test_nucleo_so_de_costas_recebe_dano_massivo(luta):
    game, scarab = luta
    quebrar(game, scarab)
    ate(game, lambda: scarab.nucleo_exposto)
    por(game, atras(scarab))
    vida = scarab.vida
    atirar(game, scarab, 10)
    assert vida - scarab.vida == 10 * CFG.nucleo_mult
    por(game, scarab.centro_chao - V(scarab.espelho * 480, 0))
    vida = scarab.vida
    atirar(game, scarab, 10)
    assert vida - scarab.vida == 10 * CFG.nucleo_fora_mult


def test_caido_as_patas_nao_recebem_dano(luta):
    game, scarab = luta
    quebrar(game, scarab, 'frente')
    vida_centro = scarab.patas['centro'].vida
    ate(game, lambda: scarab.nucleo_exposto)
    por(game, no_angulo(scarab, 'centro'))
    atirar(game, scarab, 50)
    assert scarab.patas['centro'].vida == vida_centro


def test_se_ergue_regenera_so_a_pata_quebrada_e_recomeca(luta):
    game, scarab = luta
    scarab.patas['centro'].ferir(100)
    ferida = scarab.patas['centro'].vida
    quebrar(game, scarab, 'frente')
    ate(game, lambda: scarab.nucleo_exposto)
    ate(game, lambda: not scarab.desabado, segundos=12)
    assert scarab.pose == 'em_pe' and scarab.rotina is None and not scarab.nucleo_exposto
    assert scarab.patas['frente'].vida == scarab.patas['frente'].vida_maxima
    assert scarab.patas['centro'].vida == ferida
    calar(scarab)
    quebrar(game, scarab, 'frente')      # o ciclo recomeça
    assert scarab.desabado


def test_queda_cancela_passo_e_golpe_em_andamento(luta):
    game, scarab = luta
    por(game, no_angulo(scarab, 'centro', 600))
    ate(game, lambda: scarab.no_passo)
    avisos = list(scarab.avisos)
    assert len(avisos) == 2
    quebrar(game, scarab, 'centro')
    assert not any(a.alive() for a in avisos) and not scarab.no_passo
    golpes = ouvir_dano_no_jogador(game)
    passos(game, 90)
    assert [d for d, _ in golpes if d.tipo == AREA] == []


# ── Passos ───────────────────────────────────────────────────────────────────


def test_pisada_fere_empurra_do_centro_e_treme(luta):
    game, scarab = luta
    por(game, scarab.centro_chao + V(-900, 0))
    ate(game, lambda: scarab.no_passo)
    pata = next(p for p in scarab.patas.values() if p.erguida)
    golpes = ouvir_dano_no_jogador(game)

    def ficar():
        por(game, pata.posicao + V(40, 0))

    ate(game, lambda: not scarab.no_passo, cada=ficar)
    area = [d for d, _ in golpes if d.tipo == AREA]
    assert [d.valor for d in area] == [ARTILHARIA_PRESETS['scarab_passo'].dano]
    vel = empurrao_ativo(game.player)
    assert vel.x > 0 and abs(vel.y) < vel.x * 0.4
    assert game.camera.shake_intensidade == CFG.shake_passo[0]


def test_passa_por_cima_das_paredes_mas_nao_sai_do_mapa(luta):
    game, scarab = luta
    scarab.posicao.update(-500, 99999)
    scarab.update(DT, game.mapa.grade_paredes)
    assert scarab.posicao.x >= CFG.margem_mapa - 1
    assert scarab.posicao.y <= game.mapa.altura_mapa_pixels - CFG.margem_mapa + 1


# ── Feixe ────────────────────────────────────────────────────────────────────
def _ligar_feixe(game, scarab, onde):
    por(game, onde)
    scarab.proximo_feixe = 0
    ate(game, lambda: scarab.feixe_estado == 'disparo', cada=lambda: por(game, onde))


def test_feixe_na_borda_da_cobertura_nao_fere_quem_esta_por_baixo(luta):
    game, scarab = luta
    _ligar_feixe(game, scarab, scarab.centro_chao + V(-700, 0))
    borda = scarab.centro_chao + V(-(CFG.raio_sob - 5), 0)
    golpes = ouvir_dano_no_jogador(game)
    por(game, borda)
    for _ in range(60):
        scarab.feixe.update(DT, game.player.posicao)
    assert scarab.feixe.mira_atual.distance_to(borda) < CFG.feixe.raio_impacto
    assert golpes == []


# ── Torreta e desembarque ────────────────────────────────────────────────────


def test_desembarque_tem_teto(luta):
    game, scarab = luta
    for _ in range(20):
        scarab.desembarcar()
    assert len(scarab.guarnicao) <= CFG.desembarque_max_vivos
    scarab.proximo_desembarque = 0
    passos(game)
    assert scarab.desembarque_em_curso is None
    for inimigo in scarab.guarnicao:
        inimigo.kill()
    scarab.proximo_desembarque = 0
    passos(game)
    assert scarab.desembarque_em_curso is not None


# ── Body stomp ───────────────────────────────────────────────────────────────


def test_stomp_cobre_a_area_inteira_e_da_para_fugir():
    cfg = ARTILHARIA_PRESETS['scarab_stomp']
    assert cfg.raio_explosao > CFG.raio_sob             # não há canto seguro por baixo
    assert cfg.raio_explosao / 500 * 1000 < cfg.duracao   # do centro para fora, a 500 px/s


# ── Fases e sobrecarga ───────────────────────────────────────────────────────


def test_fase_nova_no_meio_da_queda_nao_corta_a_queda(luta):
    game, scarab = luta
    quebrar(game, scarab)
    ate(game, lambda: scarab.nucleo_exposto)
    por(game, atras(scarab))
    scarab.vida = scarab.vida_maxima * 0.25
    passos(game, 5)
    assert scarab.fase == 3 and scarab.nucleo_exposto and scarab.estado_habilidade == 'queda'


# ── Morte ────────────────────────────────────────────────────────────────────
def _matar(game, scarab):
    scarab.vida = 0
    game.collision_manager.update(DT)


def test_morrendo_ignora_dano_e_nao_recomeca(luta):
    game, scarab = luta
    por(game, scarab.centro_chao + V(-1200, 0))
    _matar(game, scarab)
    rotina = scarab.rotina
    passos(game, 10)
    _matar(game, scarab)
    atirar(game, scarab, 999)
    assert scarab.rotina is rotina and scarab.vida == 0


def test_morre_caido_de_nucleo_exposto(luta):
    game, scarab = luta
    quebrar(game, scarab)
    ate(game, lambda: scarab.nucleo_exposto)
    por(game, atras(scarab))
    atirar(game, scarab, scarab.vida)
    passos(game, 2)
    assert scarab.morrendo and not scarab.nucleo_exposto and scarab.estado_habilidade == 'colapso'
    por(game, scarab.centro_chao + V(-1200, 0))
    ate(game, lambda: not scarab.alive(), segundos=4)


# ── Câmera e ordem de desenho ────────────────────────────────────────────────
def test_camera_afasta_na_chegada_e_volta_na_morte(luta):
    game, scarab = luta
    por(game, scarab.centro_chao + V(-1200, 0))
    assert game.camera.zoom_alvo == CFG.zoom
    passos(game, round(CFG.zoom_entrada_ms / 1000 / DT) + 2)
    assert game.camera.zoom == CFG.zoom
    _matar(game, scarab)
    ate(game, lambda: not scarab.alive(), segundos=4)
    assert game.camera.zoom_alvo == 1
    ate(game, lambda: game.camera.zoom == 1, segundos=4)
