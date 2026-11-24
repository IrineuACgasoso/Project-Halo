"""Scarab: patas por ângulo, queda e núcleo, passos sincronizados, cobertura, golpes do corpo, armas
autônomas, sobrecarga, colapso, desenho em camadas e config."""
import dataclasses
import math
import random

import pygame
import pytest

from helpers import DT, blindar_jogador, contar_alocacoes, ir_para_fase
from source.data.manifesto_assets import PARTES_SCARAB
from source.enemies.minibosses.scarab import corpo
from source.enemies.minibosses.scarab.armas import GUARNICAO
from source.enemies.minibosses.scarab.config import (CFG, CENTRO_CHAO, FASES, NUCLEO, PATAS_VULNERAVEIS, PES, VARIANTES,
                                                     FeixeConfig, ScarabConfig)
from source.enemies.minibosses.scarab.recortes import CANTOS
from source.feats.assets import ASSETS
from source.feats.skills.artilharia import ArtilhariaAviso
from source.feats.skills.artilharia.config import ARTILHARIA_PRESETS
from source.systems.collision import CollisionManager
from source.systems.dano import AREA, Dano, PROJETIL
from source.systems.empurrao import empurrao_ativo, limpar_empurroes
from source.systems.entitymanager import entity_manager
from source.systems.eventos import DANO_CAUSADO, eventos
from source.systems.gameclock import relogio

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


@pytest.mark.parametrize('nome', PATAS_VULNERAVEIS)
def test_borda_do_angulo(luta, nome):
    """1° dentro da abertura acerta a pata; 1° fora, não (para o lado em que não há outra)."""
    game, scarab = luta
    sentido = {'frente': 1, 'centro': 1, 'tras': -1}[nome]      # y para baixo: + gira da direita para baixo
    for folga, dentro in ((-1, True), (1, False)):
        eixo = scarab.patas[nome].posicao - scarab.centro_chao
        por(game, scarab.centro_chao + eixo.rotate(sentido * (CFG.angulo_pata[nome] + folga)))
        assert (scarab.pata_exposta is scarab.patas[nome]) is dentro


def test_angulos_das_patas_nao_se_cruzam(luta):
    game, scarab = luta
    for grau in range(0, 360, 2):
        por(game, scarab.centro_chao + V(500, 0).rotate(grau))
        expostas = [n for n in PATAS_VULNERAVEIS
                    if abs((scarab.patas[n].posicao - scarab.centro_chao).angle_to(
                        game.player.posicao - scarab.centro_chao) % 360) < CFG.angulo_pata[n]
                    or abs((scarab.patas[n].posicao - scarab.centro_chao).angle_to(
                        game.player.posicao - scarab.centro_chao) % 360 - 360) < CFG.angulo_pata[n]]
        assert len(expostas) <= 1, grau
        assert scarab.pata_exposta is (scarab.patas[expostas[0]] if expostas else None), grau


def test_pelo_norte_a_carapaca_barra_quase_tudo(luta):
    game, scarab = luta
    por(game, scarab.centro_chao - V(0, 500))
    vida, patas = scarab.vida, [p.vida for p in scarab.patas.values()]
    atirar(game, scarab, 100)
    assert vida - scarab.vida == pytest.approx(100 * CFG.carapaca_passa)
    assert patas == [p.vida for p in scarab.patas.values()]


def test_vida_das_patas_acompanha_a_dificuldade(novo_jogo):
    novo_jogo.player.contador_niveis = 10
    novo_jogo.spawner.spawnar('scarab')
    scarab = novo_jogo.sessao.boss_atual
    assert scarab.vida_maxima == CFG.vida * 2
    assert all(p.vida == p.vida_maxima == CFG.vida_pata * 2 for p in scarab.patas.values())


def test_pata_aparece_danificada_na_metade(luta):
    game, scarab = luta
    pata = scarab.patas['centro']
    assert not pata.danificada
    pata.ferir(pata.vida_maxima * CFG.pata_danificada)
    assert pata.danificada and not pata.quebrada


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


@pytest.mark.parametrize('lado', ['left', 'right'])
def test_nucleo_fica_no_angulo_dele(luta, lado):
    """O desenho do núcleo e o ângulo do dano massivo apontam para o mesmo lado."""
    game, scarab = luta
    olhar(scarab, lado)
    nucleo = scarab.no_mundo(NUCLEO)
    por(game, scarab.centro_chao + (nucleo - scarab.centro_chao).normalize() * 400)
    assert scarab.no_angulo_do_nucleo
    assert (nucleo.x > scarab.posicao.x) is (lado == 'left')


def test_caido_as_patas_nao_recebem_dano(luta):
    game, scarab = luta
    quebrar(game, scarab, 'frente')
    vida_centro = scarab.patas['centro'].vida
    ate(game, lambda: scarab.nucleo_exposto)
    por(game, no_angulo(scarab, 'centro'))
    atirar(game, scarab, 50)
    assert scarab.patas['centro'].vida == vida_centro


def test_caindo_e_se_erguendo_e_carapaca(luta):
    game, scarab = luta
    quebrar(game, scarab, 'frente')
    for quando in ('caindo', 'erguendo'):
        por(game, atras(scarab))
        vida = scarab.vida
        atirar(game, scarab, 100)
        assert vida - scarab.vida == pytest.approx(100 * CFG.carapaca_passa), quando
        if quando == 'caindo':
            ate(game, lambda: scarab.nucleo_exposto)
            ate(game, lambda: not scarab.nucleo_exposto)
            assert scarab.desabado


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


def test_tempo_do_nucleo_exposto(luta):
    game, scarab = luta
    quebrar(game, scarab)
    ate(game, lambda: scarab.nucleo_exposto)
    inicio = relogio.agora()
    ate(game, lambda: not scarab.nucleo_exposto)
    assert relogio.agora() - inicio == pytest.approx(CFG.exposto_ms, abs=20)


def test_varios_golpes_no_mesmo_frame_derrubam_uma_vez(luta):
    game, scarab = luta
    quebrar(game, scarab, 'centro')
    rotina = scarab.rotina
    atirar(game, scarab, 5000)
    assert scarab.rotina is rotina


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


def test_desabado_nao_anda_nem_atira_nem_vira(luta):
    game, scarab = luta
    scarab.proximo_feixe = scarab.proxima_rajada = scarab.proximo_desembarque = 0
    quebrar(game, scarab)
    onde = V(scarab.posicao)
    por(game, scarab.centro_chao + V(700, 200))
    for _ in range(round(5 / DT)):
        game.update(DT)
        assert scarab.feixe_estado == 'espera' and not scarab.no_passo
    assert scarab.posicao == onde and scarab.animador.lado == 'left'
    assert len(entity_manager.projeteis_inimigos_grupo) == 0 and scarab.guarnicao == []


def test_rearma_com_folga_ao_se_erguer(luta):
    game, scarab = luta
    scarab.proximo_feixe = scarab.proxima_rajada = scarab.proximo_desembarque = 0
    quebrar(game, scarab)
    ate(game, lambda: not scarab.desabado, segundos=12)
    assert min(scarab.proximo_feixe, scarab.proxima_rajada,
               scarab.proximo_desembarque) >= relogio.agora() + CFG.rearme_ms - 1


# ── Passos ───────────────────────────────────────────────────────────────────
def test_passo_avisa_onde_cada_pata_vai_pisar(luta):
    game, scarab = luta
    por(game, scarab.centro_chao + V(-900, 0))
    ate(game, lambda: scarab.no_passo)
    erguidas = {n for n, p in scarab.patas.items() if p.erguida}
    assert erguidas in ({'frente', 'tras'}, {'centro', 'oculta'})
    assert len(scarab.avisos) == 2
    for aviso in scarab.avisos:
        assert min(aviso.posicao.distance_to(scarab.patas[n].posicao) for n in erguidas) < 3
        assert aviso.cfg.duracao == CFG.passo_ms[0] and aviso.fonte is scarab


def test_pata_pousa_no_frame_em_que_a_artilharia_estoura(luta):
    game, scarab = luta
    por(game, scarab.centro_chao + V(-900, 0))
    vistos = 0
    for _ in range(round(8 / DT)):
        estourados = [a for a in scarab.avisos if a.explodiu]
        no_ar = scarab.no_passo
        game.update(DT)
        agora = [a for a in scarab.avisos if a.explodiu and a not in estourados]
        pousou = no_ar and not scarab.no_passo
        assert bool(agora) == pousou
        vistos += pousou
    assert vistos >= 4


def test_alterna_os_pares(luta):
    game, scarab = luta
    por(game, scarab.centro_chao + V(-1000, 0))
    pares = []
    for _ in range(round(7 / DT)):
        antes = scarab.no_passo
        game.update(DT)
        if scarab.no_passo and not antes:
            pares.append(frozenset(n for n, p in scarab.patas.items() if p.erguida))
    assert len(pares) >= 4 and all(a != b for a, b in zip(pares, pares[1:]))


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


def test_anda_ate_o_jogador_e_repousa_com_ele_por_baixo(luta):
    game, scarab = luta
    por(game, scarab.centro_chao + V(-800, 0))
    antes = scarab.centro_chao.distance_to(game.player.posicao)
    passos(game, 180)
    assert scarab.centro_chao.distance_to(game.player.posicao) < antes - 60
    ate(game, lambda: not scarab.no_passo, cada=lambda: por(game, scarab.centro_chao))
    onde = V(scarab.posicao)
    for _ in range(240):
        por(game, scarab.centro_chao)
        game.update(DT)
        assert scarab.posicao == onde and not scarab.no_passo
    por(game, scarab.centro_chao + V(-800, 0))           # saiu: volta a andar
    ate(game, lambda: scarab.no_passo)


def test_passa_por_cima_das_paredes_mas_nao_sai_do_mapa(luta):
    game, scarab = luta
    scarab.posicao.update(-500, 99999)
    scarab.update(DT, game.mapa.grade_paredes)
    assert scarab.posicao.x >= CFG.margem_mapa - 1
    assert scarab.posicao.y <= game.mapa.altura_mapa_pixels - CFG.margem_mapa + 1


# ── Virar ────────────────────────────────────────────────────────────────────
def test_vira_com_atraso_e_spam_nao_reinicia(luta):
    game, scarab = luta
    scarab.proximo_passo_em = relogio.agora() + 10 ** 9
    inicio = relogio.agora()
    lado = 1
    while scarab.animador.lado == 'left':
        por(game, scarab.centro_chao + V(700 * lado, 0))
        game.update(DT)
        lado = -lado if relogio.agora() - inicio < 1000 else 1
        assert relogio.agora() - inicio < 3000
    assert relogio.agora() - inicio == pytest.approx(CFG.atraso_virar_ms, abs=60)


def test_nao_vira_com_pata_no_ar_nem_com_o_jogador_por_baixo(luta):
    game, scarab = luta
    por(game, scarab.centro_chao + V(900, 0))
    trocas = 0
    for _ in range(round(6 / DT)):
        lado, no_ar = scarab.animador.lado, scarab.no_passo
        game.update(DT)
        if scarab.animador.lado != lado:
            trocas += 1
            assert not no_ar
    assert trocas == 1
    olhar(scarab, 'left')
    ate(game, lambda: not scarab.no_passo, cada=lambda: por(game, scarab.centro_chao + V(60, 0)))
    for _ in range(round(4 / DT)):
        por(game, scarab.centro_chao + V(60, 0))
        game.update(DT)
    assert scarab.animador.lado == 'left'


# ── Feixe ────────────────────────────────────────────────────────────────────
def _ligar_feixe(game, scarab, onde):
    por(game, onde)
    scarab.proximo_feixe = 0
    ate(game, lambda: scarab.feixe_estado == 'disparo', cada=lambda: por(game, onde))


def test_feixe_carrega_dispara_e_volta_a_esperar(luta):
    game, scarab = luta
    onde = scarab.centro_chao + V(-700, 100)
    por(game, onde)
    scarab.proximo_feixe = 0
    passos(game)
    assert scarab.feixe_estado == 'carga'
    inicio = relogio.agora()
    ate(game, lambda: scarab.feixe_estado == 'disparo', cada=lambda: por(game, onde))
    assert relogio.agora() - inicio == pytest.approx(CFG.feixe.carga_ms, abs=20)
    inicio = relogio.agora()
    ate(game, lambda: scarab.feixe_estado == 'espera', cada=lambda: por(game, onde))
    assert relogio.agora() - inicio == pytest.approx(CFG.feixe.duracao_ms, abs=20)
    minimo, maximo = CFG.feixe.cooldown_ms
    assert minimo <= scarab.proximo_feixe - relogio.agora() <= maximo


def test_feixe_persegue_e_fere_quem_fica_parado(luta):
    game, scarab = luta
    onde = scarab.centro_chao + V(-700, 100)
    _ligar_feixe(game, scarab, onde)
    golpes = ouvir_dano_no_jogador(game)
    for _ in range(120):
        por(game, onde)
        game.update(DT)
    total = sum(v for d, v in golpes if d.fonte is scarab and d.tipo == AREA and d.valor < 20)
    assert total > CFG.feixe.dps * 1.2
    assert scarab.feixe.mira_atual.distance_to(onde) < 5


def test_feixe_nao_alcanca_quem_nao_para_de_correr(luta):
    """Correndo em volta (500 px/s), a ponta fica para trás em todas as fases."""
    game, scarab = luta
    for fase in (1, 3):
        scarab.fase = fase
        scarab.fase_cfg = FASES[fase - 1]
        centro, angulo, raio = V(scarab.centro_chao), 180.0, 700
        _ligar_feixe(game, scarab, centro + V(raio, 0).rotate(angulo))
        passos(game, 1)
        golpes = ouvir_dano_no_jogador(game)
        feixe = scarab.feixe
        feixe.mira_atual = centro + V(raio, 0).rotate(angulo - 20)
        for _ in range(180):
            angulo += math.degrees(500 * DT / raio)
            por(game, centro + V(raio, 0).rotate(angulo))
            feixe.update(DT, game.player.posicao)
        assert golpes == [], f'fase {fase}'
        scarab.desligar_armas()
        calar(scarab)


def test_feixe_para_na_barreira_e_volta_a_perseguir(luta):
    game, scarab = luta
    _ligar_feixe(game, scarab, scarab.centro_chao + V(-700, 100))
    golpes = ouvir_dano_no_jogador(game)
    for _ in range(90):
        por(game, scarab.centro_chao + V(-80, 40))        # coberto
        game.update(DT)
        # a barreira é medida antes de ele andar neste frame: folga de 1 passo
        assert scarab.feixe.mira_atual.distance_to(scarab.centro_chao) >= CFG.raio_sob - 4
    assert scarab.feixe_estado == 'disparo'
    assert [d for d, _ in golpes if d.fonte is scarab and d.valor < 20] == []
    fora = scarab.centro_chao + V(-640, 60)
    for _ in range(60):
        por(game, fora)
        game.update(DT)
    assert scarab.feixe.mira_atual.distance_to(fora) < 10


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


def test_jogador_exatamente_no_centro_nao_quebra_o_feixe(luta):
    game, scarab = luta
    por(game, scarab.centro_chao)
    scarab.feixe.comecar()
    scarab.feixe.mira_atual = V(scarab.centro_chao)
    scarab.feixe.update(DT, game.player.posicao)
    assert scarab.feixe.mira_atual.distance_to(scarab.centro_chao) == pytest.approx(CFG.raio_sob)


@pytest.mark.parametrize('lado', ['left', 'right'])
@pytest.mark.parametrize('mira', ['left', 'right'])
def test_feixe_sai_da_ponta_do_canhao_desenhado(luta, lado, mira):
    game, scarab = luta
    olhar(scarab, lado)
    scarab.mira_torreta = mira
    imagem, x, y = corpo.recorte_torreta('default', 'em_pe_torreta', lado, mira)
    caixa = imagem.get_bounding_rect().move(x + scarab.rect.x, y + scarab.rect.y)
    ponta = scarab.ponta_canhao
    extremo = caixa.right if mira == 'right' else caixa.left
    assert abs(ponta.x - extremo) < 8 and caixa.top <= ponta.y <= caixa.bottom


def test_canhao_gira_sozinho_para_o_lado_do_alvo(luta):
    game, scarab = luta
    por(game, scarab.centro_chao + V(700, 0))
    passos(game)
    assert scarab.mira_torreta == 'right' and scarab.animador.lado == 'left'


def test_feixe_treme_muito_e_o_tremor_maior_ganha(luta):
    game, scarab = luta
    _ligar_feixe(game, scarab, scarab.centro_chao + V(-700, 100))
    passos(game, 2)
    assert game.camera.shake_intensidade == CFG.feixe.shake
    scarab.tremer(*CFG.shake_stomp)
    scarab.tremer(CFG.feixe.shake, 100)
    assert game.camera.shake_intensidade == CFG.shake_stomp[0]
    relogio.avancar(CFG.shake_stomp[1] / 1000 + 0.01)
    scarab.tremer(CFG.feixe.shake, 100)
    assert game.camera.shake_intensidade == CFG.feixe.shake


def test_fase_critica_varre_mais_rapido(luta):
    game, scarab = luta
    scarab.fase = 3
    _ligar_feixe(game, scarab, scarab.centro_chao + V(-700, 100))
    assert scarab.feixe.suavizacao == CFG.feixe.suavizacao_critica > CFG.feixe.suavizacao


def test_longe_demais_o_feixe_espera(luta):
    game, scarab = luta
    por(game, scarab.posicao - V(CFG.feixe.alcance + 50, 0))
    scarab.proximo_feixe = 0
    scarab.contexto.atualizar(scarab, DT)
    scarab.atualizar_feixe(relogio.agora(), DT)
    assert scarab.feixe_estado == 'espera'


# ── Torreta e desembarque ────────────────────────────────────────────────────
def _rajada(game, scarab):
    criados, vistos = [], set()
    por(game, scarab.centro_chao + V(-700, 0))
    scarab.proxima_rajada = 0
    for _ in range(round(4 / DT)):
        por(game, scarab.centro_chao + V(-700, 0))
        game.update(DT)
        for p in entity_manager.projeteis_inimigos_grupo:
            if p.fonte is scarab and p not in vistos:
                vistos.add(p)
                criados.append(relogio.agora())
        if scarab.tiros_restantes == 0 and criados:
            break
    return criados


def test_torreta_como_antes(luta):
    """6 disparos de 2 canhões, um a cada 250 ms."""
    game, scarab = luta
    quando = _rajada(game, scarab)
    assert len(quando) == CFG.torreta_tiros * len(CFG.torreta_canhoes) == 12
    momentos = sorted(set(quando))
    assert len(momentos) == 6
    assert all(b - a == pytest.approx(CFG.torreta_intervalo_ms, abs=18) for a, b in zip(momentos, momentos[1:]))
    minimo, maximo = CFG.torreta_cooldown_ms
    assert minimo <= scarab.proxima_rajada - relogio.agora() <= maximo


def test_torreta_dobra_a_cadencia_na_fase_critica(luta):
    game, scarab = luta
    scarab.fase = 3
    momentos = sorted(set(_rajada(game, scarab)))
    assert all(b - a == pytest.approx(CFG.torreta_intervalo_ms / 2, abs=18) for a, b in zip(momentos, momentos[1:]))
    assert scarab.proxima_rajada - relogio.agora() <= CFG.torreta_cooldown_ms[1] / 2


def test_desembarque_avisa_e_solta_a_guarnicao(luta):
    game, scarab = luta
    por(game, scarab.centro_chao + V(-700, 200))
    scarab.proximo_desembarque = 0
    passos(game)
    assert scarab.desembarque_em_curso is not None and scarab.guarnicao == []
    ate(game, lambda: scarab.guarnicao, segundos=3)
    minimo, maximo = CFG.desembarque_qtd
    assert minimo <= len(scarab.guarnicao) <= maximo
    for inimigo in scarab.guarnicao:
        assert isinstance(inimigo, tuple(GUARNICAO.values())) and inimigo.alive()
        assert inimigo.tabela_drop['life_orb'] == (1, CFG.desembarque_life_orb, 100)
        assert inimigo.tabela_drop['exp_shard']
        assert game.mapa.posicao_e_valida(inimigo.posicao)
        assert not inimigo.invisivel


def test_drop_da_guarnicao_nao_muda_o_dos_comuns(luta):
    from source.data.enemy_data import INIMIGOS
    game, scarab = luta
    antes = {nome: dict(perfil.drops) for nome, perfil in INIMIGOS.items()}
    scarab.desembarcar()
    assert {nome: dict(perfil.drops) for nome, perfil in INIMIGOS.items()} == antes


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


def test_desembarque_fora_da_arena_cai_perto_do_jogador(luta, monkeypatch):
    game, scarab = luta
    por(game, V(2300, 1400))
    monkeypatch.setattr(scarab, 'verificar_posicao_valida', lambda p: p.distance_to(game.player.posicao) <= 420)
    scarab.posicao.update(400, 400)
    assert scarab._ponto_de_desembarque(0).distance_to(game.player.posicao) <= 421


def test_armas_funcionam_durante_os_golpes(luta):
    """Autônomas: o feixe carrega no meio do body stomp."""
    game, scarab = luta
    por(game, scarab.centro_chao)
    scarab.iniciar('stomp')
    scarab.proximo_feixe = 0
    passos(game, 3)
    assert scarab.estado_habilidade == 'body_stomp' and scarab.feixe_estado == 'carga'


# ── Body stomp ───────────────────────────────────────────────────────────────
def test_stomp_senta_no_frame_da_explosao(luta):
    game, scarab = luta
    por(game, scarab.centro_chao)
    golpes = ouvir_dano_no_jogador(game)
    scarab.iniciar('stomp')
    passos(game)
    aviso = scarab.avisos[-1]
    cfg = ARTILHARIA_PRESETS['scarab_stomp']
    assert aviso.cfg is cfg and aviso.posicao.distance_to(scarab.centro_chao) < 1
    while not aviso.explodiu:
        assert scarab.pose == 'em_pe'
        game.update(DT)
    assert scarab.pose == 'sentado'
    assert [d.valor for d, _ in golpes if d.fonte is scarab] == [cfg.dano]
    assert game.camera.shake_intensidade == CFG.shake_stomp[0]
    inicio = relogio.agora()
    ate(game, lambda: scarab.pose == 'em_pe')
    assert relogio.agora() - inicio == pytest.approx(CFG.sentado_ms, abs=20)
    assert scarab.cd['stomp'] >= relogio.agora() + CFG.cooldown['stomp'][0] - 1


def test_stomp_cobre_a_area_inteira_e_da_para_fugir():
    cfg = ARTILHARIA_PRESETS['scarab_stomp']
    assert cfg.raio_explosao > CFG.raio_sob             # não há canto seguro por baixo
    assert cfg.raio_explosao / 500 * 1000 < cfg.duracao   # do centro para fora, a 500 px/s


def test_stomp_pesa_muito_com_o_jogador_por_baixo(luta):
    game, scarab = luta
    por(game, scarab.centro_chao)
    scarab.cd['stomp'] = 0
    random.seed(3)
    escolhas = [scarab.escolher_habilidade(0) for _ in range(300)]
    assert escolhas.count('stomp') > 200 and set(escolhas) <= {'stomp', None}
    por(game, scarab.centro_chao + V(-900, 0))
    assert {scarab.escolher_habilidade(0) for _ in range(50)} == {None}


def test_stomp_acontece_sozinho(luta):
    game, scarab = luta
    scarab.cd['stomp'] = 0
    ate(game, lambda: scarab.pose == 'sentado', segundos=8, cada=lambda: por(game, scarab.centro_chao))


def test_queda_no_meio_do_stomp_nao_deixa_resto(luta):
    game, scarab = luta
    por(game, scarab.centro_chao)
    scarab.iniciar('stomp')
    passos(game, 20)
    assert scarab.impulso_y > 0
    quebrar(game, scarab, 'centro')
    assert scarab.impulso_y == 0 and scarab.pose == 'caido' and scarab.avisos == []


# ── Pisada sísmica ───────────────────────────────────────────────────────────
def _acampar(game, scarab, nome, segundos):
    for _ in range(round(segundos / DT)):
        por(game, scarab.patas[nome].posicao)
        scarab.medir_acampamento(DT)


def test_acampar_conta_so_colado_e_sem_sair(luta):
    game, scarab = luta
    _acampar(game, scarab, 'tras', CFG.acampar_ms / 1000 - 0.1)
    assert scarab.pata_acampada is None
    por(game, scarab.patas['tras'].posicao + V(CFG.acampar_raio + 5, 0))
    scarab.medir_acampamento(DT)
    assert scarab.patas['tras'].acampado_ms == 0
    _acampar(game, scarab, 'tras', CFG.acampar_ms / 1000 + 0.05)
    assert scarab.pata_acampada is scarab.patas['tras']


@pytest.mark.parametrize('nome', PATAS_VULNERAVEIS)
def test_sismica_ergue_so_aquela_pata_e_persegue(luta, nome):
    game, scarab = luta
    _acampar(game, scarab, nome, CFG.acampar_ms / 1000 + 0.05)
    scarab.iniciar('sismica')
    passos(game)
    assert {n for n, p in scarab.patas.items() if p.erguida} == {nome}
    aviso = scarab.avisos[-1]
    cfg = ARTILHARIA_PRESETS['scarab_sismica']
    destino = scarab.patas[nome].posicao + V(0, 220)
    antes = aviso.posicao.distance_to(destino)
    for _ in range(20):
        por(game, destino)
        game.update(DT)
    assert aviso.posicao.distance_to(destino) < antes - 80
    golpes = ouvir_dano_no_jogador(game)
    while not aviso.explodiu:
        assert scarab.patas[nome].erguida
        por(game, aviso.posicao + V(60, 0))
        game.update(DT)
    assert not scarab.patas[nome].erguida
    assert [d.valor for d, _ in golpes if d.fonte is scarab] == [cfg.dano]
    assert empurrao_ativo(game.player).length() > ARTILHARIA_PRESETS['scarab_passo'].knockback * 9
    assert game.camera.shake_intensidade == CFG.shake_sismica[0] > CFG.shake_passo[0]


def test_sismica_trava_no_fim_e_respeita_o_alcance(luta):
    game, scarab = luta
    _acampar(game, scarab, 'frente', CFG.acampar_ms / 1000 + 0.05)
    scarab.iniciar('sismica')
    passos(game)
    aviso, pata = scarab.avisos[-1], scarab.patas['frente']
    ultima = None
    while not aviso.explodiu:
        por(game, pata.posicao + V(-2000, 0))
        restante = aviso.cfg.duracao - (relogio.agora() - aviso.tempo_criacao)
        if restante <= CFG.sismica_trava_ms - 20:
            ultima = ultima or V(aviso.posicao)
            assert aviso.posicao == ultima
        game.update(DT)
        assert aviso.posicao.distance_to(pata.posicao) <= CFG.sismica_alcance + 1
    assert ultima is not None


def test_sismica_da_para_fugir_correndo():
    cfg = ARTILHARIA_PRESETS['scarab_sismica']
    assert CFG.sismica_velocidade < 500
    assert (500 - CFG.sismica_velocidade) * cfg.duracao / 1000 > cfg.raio_explosao


def test_acampar_dispara_a_sismica_no_jogo(luta):
    game, scarab = luta
    scarab.cd['sismica'] = 0
    ate(game, lambda: scarab.estado_habilidade == 'pisada_sismica', segundos=12,
        cada=lambda: por(game, scarab.patas['frente'].posicao + V(-60, 0)))


# ── Fases e sobrecarga ───────────────────────────────────────────────────────
@pytest.mark.parametrize('razao, variante', [(1, 'default'), (0.6, 'damaged'), (0.31, 'damaged'), (0.29, 'broken')])
def test_arte_de_cada_fase(luta, razao, variante):
    game, scarab = luta
    por(game, scarab.centro_chao + V(-900, 0))
    scarab.vida = scarab.vida_maxima * razao
    passos(game, 2)
    assert scarab.variante_arte == variante
    assert scarab.critico is (variante == 'broken')


def test_sobrecarga_solta_fumaca(luta):
    game, scarab = luta
    por(game, scarab.centro_chao + V(-900, 0))
    scarab.fase = 3
    for p in list(entity_manager.particulas_grupo):
        p.kill()
    scarab.atualizar_vfx(relogio.agora())
    assert len(entity_manager.particulas_grupo) == 1
    assert entity_manager.particulas_grupo.sprites()[0].y_desenho > scarab.y_desenho   # por cima dele


def test_fase_nova_no_meio_da_queda_nao_corta_a_queda(luta):
    game, scarab = luta
    quebrar(game, scarab)
    ate(game, lambda: scarab.nucleo_exposto)
    por(game, atras(scarab))
    scarab.vida = scarab.vida_maxima * 0.25
    passos(game, 5)
    assert scarab.fase == 3 and scarab.nucleo_exposto and scarab.estado_habilidade == 'queda'


def test_fase_mais_avancada_pisa_mais_rapido(luta):
    game, scarab = luta
    assert list(CFG.passo_ms) == sorted(CFG.passo_ms, reverse=True)
    scarab.fase = 3
    por(game, scarab.centro_chao + V(-900, 0))
    ate(game, lambda: scarab.no_passo)
    assert scarab.avisos[-1].cfg.duracao == CFG.passo_ms[2]


# ── Morte ────────────────────────────────────────────────────────────────────
def _matar(game, scarab):
    scarab.vida = 0
    game.collision_manager.update(DT)


def test_colapso_antes_de_sumir(luta):
    game, scarab = luta
    por(game, scarab.centro_chao + V(-1200, 0))
    _matar(game, scarab)
    assert scarab.alive() and scarab.morrendo and scarab.pose == 'caido' and not scarab.alvejavel
    inicio = relogio.agora()
    itens = len(entity_manager.items_grupo)
    ate(game, lambda: not scarab.alive(), segundos=4)
    assert relogio.agora() - inicio == pytest.approx(ARTILHARIA_PRESETS['scarab_detonacao'].duracao, abs=40)
    assert len(entity_manager.items_grupo) > itens
    passos(game, 1)
    assert game.sessao.boss_atual is None and game.sessao.spawnar_portal_em_breve


@pytest.mark.parametrize('distancia, atinge', [(100, True), (900, False)])
def test_detonacao_fere_quem_ficou_perto(luta, distancia, atinge):
    game, scarab = luta
    onde = scarab.centro_chao + V(-distancia, 0)
    por(game, onde)
    _matar(game, scarab)
    golpes = ouvir_dano_no_jogador(game)
    ate(game, lambda: not scarab.alive(), segundos=4, cada=lambda: por(game, onde))
    passos(game, 2)
    area = [d.valor for d, _ in golpes if d.tipo == AREA]
    assert area == ([ARTILHARIA_PRESETS['scarab_detonacao'].dano] if atinge else [])


def test_da_para_correr_da_detonacao():
    cfg = ARTILHARIA_PRESETS['scarab_detonacao']
    assert cfg.raio_explosao / 500 * 1000 < cfg.duracao


def test_explosoes_em_cadeia_durante_o_colapso(luta):
    from source.enemies.minibosses.scarab.vfx import ExplosaoVFX
    game, scarab = luta
    por(game, scarab.centro_chao + V(-1200, 0))
    _matar(game, scarab)
    vistas = set()
    for _ in range(140):
        game.update(DT)
        vistas |= {s for s in entity_manager.all_sprites if isinstance(s, ExplosaoVFX)}
        if not scarab.alive():
            break
        assert len(vistas) <= 40
    assert len(vistas) >= 15


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


def test_morrendo_desliga_tudo(luta):
    game, scarab = luta
    _ligar_feixe(game, scarab, scarab.centro_chao + V(-700, 100))
    por(game, scarab.centro_chao + V(-1200, 0))
    _matar(game, scarab)
    assert scarab.feixe_estado == 'espera' and not scarab.no_passo
    passos(game, 60)
    assert scarab.feixe_estado == 'espera' and not scarab.no_passo


def test_drop_dentro_da_arena(luta, monkeypatch):
    game, scarab = luta
    por(game, V(2300, 1400))
    monkeypatch.setattr(scarab, 'verificar_posicao_valida', lambda p: False)
    scarab.grupos_do_drop = (entity_manager.all_sprites, entity_manager.items_grupo)
    scarab.posicao.update(400, 400)
    scarab.detonar(100)
    assert all(V(i.rect.center).distance_to(game.player.posicao) < 200 for i in entity_manager.items_grupo)


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


def test_boss_cabe_na_tela_afastada():
    """O corpo inteiro aparece com o jogador na pata da frente dele (a central)."""
    alto = PES['centro'][1] - 90              # do topo do canhão ao pé
    assert 720 / CFG.zoom / 2 > alto - 160


def test_jogador_some_por_baixo_dele(luta):
    """Onde o casco cobre o jogador, o pixel da tela é o do casco."""
    game, scarab = luta
    game.camera.restaurar_zoom()
    meio = V(400, 440)                                    # no meio do casco
    ponto = scarab.no_mundo(meio)
    por(game, ponto)
    game.camera.update(ponto)
    game.renderer._draw_mundo()
    com = game.tela.get_at((round(ponto.x - game.camera.offset.x), round(ponto.y - game.camera.offset.y)))
    game.player.image = pygame.Surface((144, 144))
    game.player.image.fill((255, 0, 255))
    game.renderer._draw_mundo()
    assert game.tela.get_at((round(ponto.x - game.camera.offset.x), round(ponto.y - game.camera.offset.y))) == com


# ── Corpo em camadas ─────────────────────────────────────────────────────────
def test_todo_recorte_tem_imagem_e_canto():
    assert set(CANTOS) == set(PARTES_SCARAB)
    assert set(ASSETS['enemies']['scarab_partes']) == set(VARIANTES)
    for variante, partes in ASSETS['enemies']['scarab_partes'].items():
        for nome, imagem in partes.items():
            x, y = CANTOS[nome]
            assert 0 <= x and x + imagem.get_width() <= 1024 and 0 <= y and y + imagem.get_height() <= 1024, nome


def test_tamanho_do_recorte_e_o_mesmo_nas_variantes():
    """Um canto só por recorte: as três variantes precisam ter a mesma caixa."""
    partes = ASSETS['enemies']['scarab_partes']
    for nome in PARTES_SCARAB:
        assert len({partes[v][nome].get_size() for v in VARIANTES}) == 1, nome


@pytest.mark.parametrize('variante, arquivo', [('default', 'scarab1'), ('damaged', 'damaged/damaged1'),
                                               ('broken', 'broken/broken1')])
def test_camadas_remontam_a_arte_original(variante, arquivo):
    """De pé, com tudo inteiro, as camadas dão pixel a pixel o sprite de antes."""
    original = pygame.image.load(f'assets/img/enemies/covenant/scarab/{arquivo}.png').convert_alpha()
    fundo = pygame.Surface((1024, 1024))
    fundo.fill((90, 80, 70))
    esperado = fundo.copy()
    esperado.blit(original, (0, 0))
    for nome in ('oculta', 'frente', 'tras', 'corpo', 'centro'):
        imagem, x, y = corpo.recorte(variante, f'em_pe_{nome}', 'left')
        fundo.blit(imagem, (x, y))
    imagem, x, y = corpo.recorte_torreta(variante, 'em_pe_torreta', 'left', 'right')
    fundo.blit(imagem, (x, y))
    assert pygame.image.tobytes(fundo, 'RGB') == pygame.image.tobytes(esperado, 'RGB')


@pytest.mark.parametrize('pose', corpo.POSES)
@pytest.mark.parametrize('variante', VARIANTES)
def test_pata_danificada_muda_o_desenho(pose, variante):
    for nome in PATAS_VULNERAVEIS:
        inteira = corpo.recorte(variante, corpo.nome_da_pata(pose, nome, False, False), 'left')
        ferida = corpo.recorte(variante, corpo.nome_da_pata(pose, nome, False, True), 'left')
        assert pygame.image.tobytes(inteira[0], 'RGBA') != pygame.image.tobytes(ferida[0], 'RGBA')


def test_rle_nao_muda_os_pixels():
    imagem, _, _ = corpo.recorte('default', 'em_pe_centro', 'left')
    do_disco = pygame.image.load('assets/img/enemies/covenant/scarab/partes/default/em_pe_centro.png').convert_alpha()
    pygame.display.get_surface().blit(imagem, (0, 0))
    assert pygame.image.tobytes(imagem, 'RGBA') == pygame.image.tobytes(do_disco, 'RGBA')


@pytest.mark.parametrize('lado', ['left', 'right'])
@pytest.mark.parametrize('pose', corpo.POSES)
def test_mascara_da_pose_e_do_lado(luta, pose, lado):
    game, scarab = luta
    olhar(scarab, lado)
    scarab.pose = pose
    scarab.animar()
    assert scarab.mask is corpo.mascara(pose, lado) and scarab.mask.get_size() == (1024, 1024)
    assert scarab.rect.size == (1024, 1024)


def test_tiro_acerta_a_pata_desenhada_e_passa_no_vao(luta):
    game, scarab = luta

    class Tiro(pygame.sprite.Sprite):
        def __init__(self, ponto):
            super().__init__()
            self.image = pygame.Surface((8, 8))
            self.mask = pygame.mask.Mask((8, 8), fill=True)
            self.rect = self.image.get_rect(center=(round(ponto.x), round(ponto.y)))

    assert CollisionManager.custom_collision(Tiro(scarab.no_mundo((600, 500))), scarab)       # pata central
    assert CollisionManager.custom_collision(Tiro(scarab.no_mundo((90, 470))), scarab)        # pata da frente
    assert not CollisionManager.custom_collision(Tiro(scarab.no_mundo((760, 520))), scarab)   # entre as patas


@pytest.mark.parametrize('pose', corpo.POSES)
@pytest.mark.parametrize('fase', [1, 2, 3])
def test_desenha_tudo_sem_alocar(luta, fase, pose):
    game, scarab = luta
    por(game, scarab.centro_chao + V(-500, 100))
    game.camera.update(game.player.posicao)
    scarab.fase, scarab.pose = fase, pose
    scarab.nucleo_exposto = pose == 'caido'
    scarab.desabado = pose == 'caido'
    scarab.feixe_estado, scarab.feixe_fim = 'disparo', relogio.agora() + 1000
    scarab.patas['frente'].ferir(10 ** 6)
    scarab.patas['centro'].erguida = True
    for _ in range(3):
        game.draw()
    with contar_alocacoes() as contador:
        for estado in ('disparo', 'carga'):
            scarab.feixe_estado = estado
            for lado in ('left', 'right'):
                olhar(scarab, lado)
                game.draw()
    assert contador.total == 0, contador.por_tipo
    assert game.renderer._erros_logados == set()


def test_desenhar_nao_usa_random(luta):
    game, scarab = luta
    por(game, scarab.centro_chao + V(-500, 100))
    scarab.fase = 3
    scarab.feixe_estado, scarab.feixe_fim = 'carga', relogio.agora() + 1000
    estado = random.getstate()
    for morrendo in (False, True):
        scarab.morrendo = morrendo
        game.renderer._draw_mundo()
    assert random.getstate() == estado


# ── Config ───────────────────────────────────────────────────────────────────
@pytest.mark.parametrize('troca', [
    {'cooldown': {'stomp': (1, 2)}},
    {'angulo_pata': {'frente': 30}},
    {'angulo_pata': {'frente': 95, 'centro': 20, 'tras': 20}},
    {'carapaca_passa': 1},
    {'passo_ms': (700, 0, 480)},
    {'passo_ms': (700, 600)},
    {'nucleo_mult': 1},
    {'zoom': 0},
    {'zoom': 1.5},
    {'vida_pata': 0},
    {'pata_danificada': 1},
])
def test_config_invalida(troca):
    with pytest.raises(ValueError):
        dataclasses.replace(CFG, **troca)


@pytest.mark.parametrize('troca', [{'dps': 0}, {'duracao_ms': 0}, {'suavizacao': 0.2}, {'suavizacao_critica': 2}])
def test_config_do_feixe_invalida(troca):
    with pytest.raises(ValueError):
        dataclasses.replace(FeixeConfig(), **troca)


def test_config_e_imutavel():
    with pytest.raises(dataclasses.FrozenInstanceError):
        ScarabConfig().vida = 1


def test_presets_do_scarab_empurram_e_sao_cinza():
    for nome in ('scarab_passo', 'scarab_sismica', 'scarab_stomp'):
        cfg = ARTILHARIA_PRESETS[nome]
        assert cfg.knockback
        r, g, b, _ = cfg.cor_borda
        assert max(r, g, b) - min(r, g, b) < 25                                  # borda cinza
        assert cfg.cor_preenchimento[0] > 180 > 60 > cfg.cor_preenchimento[1]    # preenchimento vermelho
        assert min(cfg.cor_explosao[:3]) > 200                                   # estouro claro


# ── Luta real ────────────────────────────────────────────────────────────────
@pytest.mark.integration
def test_luta_real_na_fase_3(novo_jogo):
    """90 s com o jogador circulando e tudo ligado: passos, feixe, torreta, desembarque, queda e morte."""
    ir_para_fase(novo_jogo, 3)
    blindar_jogador(novo_jogo.player)
    novo_jogo.spawner.update = lambda dt: None
    novo_jogo.spawner.spawnar('scarab')
    scarab = novo_jogo.sessao.boss_atual
    scarab.posicao.update(2300, 1400)
    vistos = set()
    for i in range(round(90 / DT)):
        angulo = i * 0.35
        raio = 620 if (i // 300) % 2 else 200
        por(novo_jogo, scarab.centro_chao + V(raio, 0).rotate(angulo))
        novo_jogo.update(DT)
        novo_jogo.player.vida_atual = novo_jogo.player.vida_maxima
        if i % 10 == 0:
            novo_jogo.draw()
        vistos |= {scarab.estado_habilidade, scarab.feixe_estado, scarab.pose}
        vistos.add('passo' if scarab.no_passo else '')
        vistos.add('guarnicao' if scarab.guarnicao else '')
        if i == 2400:
            quebrar(novo_jogo, scarab, 'tras')
        if i == 4200 and scarab.alive():
            scarab.vida = 0
        if not scarab.alive():
            vistos.add('morreu')
            break
    assert {'body_stomp', 'queda', 'colapso', 'disparo', 'carga', 'sentado', 'caido', 'passo', 'guarnicao',
            'morreu'} <= vistos
    assert novo_jogo.renderer._erros_logados == set()
    assert not any(isinstance(s, ArtilhariaAviso) and s.fonte is scarab and s.grude for s in entity_manager.all_sprites)
