"""Zealot reformulado: escudo × vida, combo de 3 dashes, invisibilidade ofensiva e defensiva, pesos e vfx."""
import random

import pygame
import pytest

from helpers import DT, blindar_jogador, ir_para_fase, simular
from source.enemies.minibosses.zealot import movement
from source.enemies.minibosses.zealot.config import CFG
from source.feats.skills.cone_strike import ConeStrikeAviso
from source.feats.skills.cone_strike.config import CONE_STRIKE_PRESETS
from source.feats.skills.dash import DASH_PRESETS
from source.feats.skills.invisibilidade import OCULTO
from source.feats.skills.rect_strike import RECT_STRIKE_PRESETS, RectStrikeAviso
from source.systems.dano import PROJETIL, Dano
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.systems.mapmanager.grade_paredes import GradeParedes

V = pygame.math.Vector2
CENTRO = V(1500, 1500)
LONGE, MEDIO, PERTO = V(CFG.dist_medio + 200, 0), V(400, 0), V(150, 0)
ALCANCE_DASH = DASH_PRESETS['zealot'].velocidade * DASH_PRESETS['zealot'].duracao_ms / 1000


@pytest.fixture
def zealot(novo_jogo):
    novo_jogo.spawner.spawnar('zealot')
    z = novo_jogo.sessao.boss_atual
    z.posicao.update(CENTRO)
    z.sync_rect()
    z.invencivel = False
    z.travamento = None               # sem anti-stuck: cada teste o chama quando quer
    z.verificar_posicao_valida = lambda p: True
    novo_jogo.mapa.caminho_livre = lambda a, b: True
    blindar_jogador(novo_jogo.player)
    _jogador_em(z, MEDIO)
    yield z
    del novo_jogo.mapa.caminho_livre


def _jogador_em(z, deslocamento):
    z.jogador.posicao.update(z.posicao + deslocamento)


def _passo(z, paredes=None):
    relogio.avancar(DT)
    z.update(DT, paredes)
    for s in list(entity_manager.all_sprites):
        if isinstance(s, (RectStrikeAviso, ConeStrikeAviso)):
            s.update(DT)


def _passos(z, segundos):
    for _ in range(round(segundos / DT)):
        _passo(z)


def _sem_ia(z):
    """Só o que o teste iniciar: nada é sorteado."""
    z.cd = {nome: float('inf') for nome in z.cd}


def _iniciar(z, nome):
    _sem_ia(z)
    z.iniciar(nome)


def _ate(z, condicao, limite_s=20):
    for i in range(round(limite_s / DT)):
        if condicao():
            return i * DT
        _passo(z)
    raise AssertionError('não aconteceu')


def _quebrar_escudo(z):
    z.receber_dano(Dano(z.escudo_atual, PROJETIL))
    assert z.escudo_atual == 0


def _avisos(classe):
    return [s for s in entity_manager.all_sprites if isinstance(s, classe)]


# ── Nascimento ───────────────────────────────────────────────────────────────
def test_nasce_com_escudo_cheio_e_maior_que_a_vida(zealot):
    assert zealot.escudo_atual == zealot.escudo_maximo > zealot.vida_maxima > 0
    assert zealot.escudo_maximo / zealot.vida_maxima == pytest.approx(CFG.escudo / CFG.vida)
    assert zealot.alvejavel and zealot.invisibilidade is None


# ── Combo de 3 dashes ────────────────────────────────────────────────────────
def _assistir_combo(z, ao_passar=None):
    """Roda o combo inteiro e devolve os dashes [(início, fim, direção)] e os golpes na ordem."""
    dashes, golpes, inicio = [], [], relogio.agora()
    original = movement.Dash

    class Espiao(original):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.registro = [relogio.agora() - inicio, None, V(self.direcao), kwargs['preset']]
            dashes.append(self.registro)

        def atualizar(self, dt, paredes=None):
            fim = super().atualizar(dt, paredes)
            if fim and self.registro[1] is None:
                self.registro[1] = relogio.agora() - inicio
            return fim

    movement.Dash = Espiao
    try:
        _iniciar(z, 'combo')
        vistos = set()
        for _ in range(round(10 / DT)):
            _passo(z)
            if ao_passar:
                ao_passar(len(dashes))
            for s in _avisos(RectStrikeAviso) + _avisos(ConeStrikeAviso):
                if s not in vistos:
                    vistos.add(s)
                    golpes.append((s, relogio.agora() - inicio, V(z.posicao)))
            if z.rotina is None:
                return dashes, golpes
    finally:
        movement.Dash = original
    raise AssertionError('o combo não acabou')


def test_combo_sao_tres_dashes_dash_estocada_e_cone(zealot):
    _jogador_em(zealot, MEDIO)
    dashes, golpes = _assistir_combo(zealot)
    assert len(dashes) == 3 and {d[3] for d in dashes} == {'zealot'}
    assert [type(g[0]) for g in golpes] == [RectStrikeAviso, ConeStrikeAviso]
    (estocada, t_est, _), (cone, t_cone, _) = golpes
    assert estocada.cfg is RECT_STRIKE_PRESETS['zealot_estocada']
    assert cone.cfg is CONE_STRIKE_PRESETS['zealot_varredura']
    assert dashes[1][1] <= t_est <= dashes[2][0]        # a estocada sai no fim do 2º dash
    assert t_cone >= dashes[2][1]                       # o cone, no fim do 3º
    assert zealot.cd['combo'] > relogio.agora()


def test_golpes_saem_no_vetor_do_dash_e_nao_no_jogador(zealot):
    """Quem desvia para o lado durante o dash não leva o golpe virado para ele."""
    _jogador_em(zealot, MEDIO)

    def desviar(numero_de_dashes):
        zealot.jogador.posicao.update(zealot.posicao + (V(350, 0) if numero_de_dashes % 2 else V(0, -350)))

    dashes, golpes = _assistir_combo(zealot, desviar)
    for (aviso, _, posicao), dash in zip(golpes, dashes[1:]):
        assert aviso.direcao == dash[2]
        assert aviso.posicao == posicao                 # parte de onde ele parou


def test_dash_nao_atravessa_parede(zealot):
    paredes = GradeParedes([{'tipo': 'linha', 'pontos': [CENTRO + V(200, -600), CENTRO + V(200, 600)]}])
    _jogador_em(zealot, MEDIO)
    _iniciar(zealot, 'combo')
    for _ in range(round(1.5 / DT)):
        _passo(zealot, paredes)
        assert zealot.posicao.x < CENTRO.x + 200


# ── Invisibilidade ofensiva ──────────────────────────────────────────────────


def test_furtivo_contorna_a_parede_em_vez_de_ficar_preso(zealot):
    paredes = GradeParedes([{'tipo': 'linha', 'pontos': [CENTRO + V(150, -120), CENTRO + V(150, 120)]}])
    random.seed(2)
    _jogador_em(zealot, LONGE)
    _iniciar(zealot, 'furtivo')
    for _ in range(round(4 / DT)):
        _passo(zealot, paredes)
    assert zealot.posicao.x > CENTRO.x + 150            # deu a volta


# ── Invisibilidade defensiva ─────────────────────────────────────────────────
def test_sem_escudo_foge_invisivel_antes_de_qualquer_outra_coisa(zealot):
    zealot.cd = {nome: 0 for nome in zealot.cd}         # tudo pronto
    zealot.wait = 5000                                  # e em pausa: não importa
    _quebrar_escudo(zealot)
    _passo(zealot)
    assert zealot.ultima_habilidade == 'defensiva' and not zealot.alvejavel


def test_perder_o_escudo_nao_interrompe_o_golpe_mas_fugir_vem_logo_depois(zealot):
    _jogador_em(zealot, MEDIO)
    _iniciar(zealot, 'combo')
    _passos(zealot, 0.5)
    _quebrar_escudo(zealot)
    vida, exposto = zealot.vida, 0.0
    while zealot.ultima_habilidade == 'combo':
        assert zealot.alvejavel                         # o jogador tem essa janela para acertar a vida
        _passo(zealot)
        exposto += DT
    assert zealot.ultima_habilidade == 'defensiva' and not zealot.alvejavel
    assert exposto > 1 and zealot.vida == vida
    zealot.receber_dano(Dano(10, PROJETIL))
    assert zealot.vida <= vida                          # sem escudo, é na vida que dói


def test_fuga_fica_dentro_do_mapa_mesmo_encurralado(zealot):
    """No canto, com o jogador fechando a saída: passa por ele em vez de correr contra a parede."""
    mapa = zealot.game.mapa
    zealot.posicao.update(150, 150)
    _jogador_em(zealot, V(200, 200))
    for seed in range(40):
        random.seed(seed)
        ponto = zealot._sortear_ponto_de_fuga()
        assert CFG.fuga_margem_mapa <= ponto.x <= mapa.largura_mapa_pixels
        assert CFG.fuga_margem_mapa <= ponto.y <= mapa.altura_mapa_pixels


def test_regenera_do_zero_ao_cheio_no_tempo_do_config_e_volta_a_atacar(zealot):
    _jogador_em(zealot, PERTO)
    _quebrar_escudo(zealot)
    _sem_ia(zealot)
    _passo(zealot)
    levou = _ate(zealot, lambda: zealot.escudo_atual >= zealot.escudo_maximo)
    assert levou == pytest.approx(CFG.regen_ms / 1000, abs=0.1)
    _ate(zealot, lambda: zealot.rotina is None, 1)
    assert zealot.alvejavel and zealot.invisibilidade is None and zealot.alpha_atual == 255
    assert zealot.status.mult_velocidade == 1.0
    assert _avisos(ConeStrikeAviso) == []               # ninguém o caçou: sem contra-ataque


def test_cacado_interrompe_a_regeneracao_com_dash_e_cone_fino(zealot):
    _jogador_em(zealot, PERTO)
    _quebrar_escudo(zealot)
    _sem_ia(zealot)
    _passos(zealot, CFG.fuga_min_ms / 1000 + 0.5)
    assert zealot.fase_invisibilidade == OCULTO
    distancia = CFG.fuga_dist_limite - 20
    _jogador_em(zealot, V(0, distancia))
    chegada, escudo = zealot.posicao + V(0, min(distancia, ALCANCE_DASH)), zealot.escudo_atual
    assert 0 < escudo < zealot.escudo_maximo
    _passos(zealot, 2 * DT)
    assert zealot.alvejavel and zealot.status.mult_velocidade == 1.0 and zealot.animador.clip == 'dash'
    _ate(zealot, lambda: _avisos(ConeStrikeAviso))
    cone, = _avisos(ConeStrikeAviso)
    assert cone.cfg is CONE_STRIKE_PRESETS['zealot_contra_ataque'] and cone.direcao == V(0, 1)
    assert zealot.posicao.distance_to(chegada) < 1 and zealot.inofensivo
    assert zealot.dist_jogador() < cone.cfg.raio        # o dash pode não chegar; o golpe alcança quem ficou parado
    _ate(zealot, lambda: zealot.rotina is None)
    assert zealot.escudo_atual == escudo                # parou de regenerar
    assert not zealot.inofensivo
    _passo(zealot)
    assert zealot.ultima_habilidade == 'defensiva' and zealot.rotina is None   # voltou ao ofensivo


@pytest.mark.parametrize('nome', ['combo', 'furtivo', 'defensiva', 'antistuck'])
def test_interromper_qualquer_habilidade_nao_deixa_efeito_preso(zealot, nome):
    for segundos in (0.1, 0.6, 1.2, 1.7):
        _jogador_em(zealot, PERTO)
        _iniciar(zealot, nome)
        _passos(zealot, segundos)
        zealot.interromper_rotina()
        assert zealot.status.mult_velocidade == 1.0 and not zealot.is_inofensivo
        zealot.escudo_atual = zealot.escudo_maximo
        _passos(zealot, 1)
        assert zealot.invisibilidade is None and zealot.alvejavel


# ── Anti-stuck ───────────────────────────────────────────────────────────────
def test_antistuck_some_e_reaparece_perto_do_jogador(zealot):
    _jogador_em(zealot, V(1500, 0))
    _iniciar(zealot, 'antistuck')
    _ate(zealot, lambda: zealot.rotina is None)
    minimo, maximo = CFG.antistuck_raio
    assert minimo - 1 <= zealot.dist_jogador() <= maximo + 1
    assert zealot.invisibilidade is None


# ── Luta real ────────────────────────────────────────────────────────────────
@pytest.mark.integration
def test_luta_real_passa_por_todos_os_modos(novo_jogo):
    """Loop real na fase 1 (paredes, colisão, desenho): ataca, perde o escudo, foge, regenera e volta."""
    random.seed(11)
    ir_para_fase(novo_jogo, 1)
    blindar_jogador(novo_jogo.player)
    novo_jogo.spawner.spawnar('zealot')
    z = novo_jogo.sessao.boss_atual
    z.vida = z.vida_maxima = 10 ** 6
    novo_jogo.renderer._erros_logados.clear()
    usadas = set()
    for segundo in range(60):
        if segundo == 30:
            z.receber_dano(Dano(z.escudo_atual, PROJETIL))
        simular(novo_jogo, 1, desenhar_a_cada=10)
        usadas.add(z.ultima_habilidade)
    assert z.alive() and {'combo', 'defensiva'} <= usadas, usadas
    assert z.escudo_atual > 0                           # regenerou
    assert novo_jogo.renderer._erros_logados == set()
