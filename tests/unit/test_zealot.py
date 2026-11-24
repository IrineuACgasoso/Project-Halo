"""Zealot reformulado: escudo × vida, combo de 3 dashes, invisibilidade ofensiva e defensiva, pesos e vfx."""
import random
from collections import Counter

import pygame
import pytest

from helpers import DT, blindar_jogador, contar_alocacoes, ir_para_fase, simular
from source.enemies.minibosses.zealot import movement
from source.enemies.minibosses.zealot.config import CFG, ZealotConfig
from source.feats.skills.cone_strike import ConeStrikeAviso
from source.feats.skills.cone_strike.config import CONE_STRIKE_PRESETS
from source.feats.skills.dash import DASH_PRESETS
from source.feats.skills.invisibilidade import FADE_OUT, INVISIBILIDADE_PRESETS, OCULTO
from source.feats.skills.rect_strike import RECT_STRIKE_PRESETS, RectStrikeAviso
from source.systems.dano import PROJETIL, Dano
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.systems.mapmanager.grade_paredes import GradeParedes
from source.utils.superficies import silhueta_de

V = pygame.math.Vector2
CENTRO = V(1500, 1500)
LONGE, MEDIO, PERTO = V(CFG.dist_medio + 200, 0), V(400, 0), V(150, 0)


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


def test_escudo_escala_com_o_nivel_do_jogador_como_a_vida(novo_jogo):
    novo_jogo.player.contador_niveis = 10
    novo_jogo.spawner.spawnar('zealot')
    z = novo_jogo.sessao.boss_atual
    assert z.vida_maxima == pytest.approx(CFG.vida * 2) and z.escudo_maximo == pytest.approx(CFG.escudo * 2)


def test_o_escudo_protege_a_vida(zealot):
    vida = zealot.vida
    zealot.receber_dano(Dano(100, PROJETIL))
    assert zealot.vida == vida and zealot.escudo_atual == zealot.escudo_maximo - 100


def test_a_espada_aponta_para_o_jogador(zealot):
    """A arte original aponta para a esquerda (o sprite ficava espelhado ao contrário)."""
    _sem_ia(zealot)
    for dx, lado in ((300, 'right'), (-300, 'left')):
        _jogador_em(zealot, V(dx, 0))
        _passo(zealot)
        assert zealot.animador.lado == lado
        # a espada azul ocupa a metade do quadro do lado para onde ele olha
        quadro = zealot.quadro_original
        meio = quadro.get_width() // 2
        azuis = Counter()
        for x in range(quadro.get_width()):
            for y in range(80, 125):
                r, g, b, a = quadro.get_at((x, y))
                if a > 127 and b > 180 and r < 90:
                    azuis['right' if x >= meio else 'left'] += 1
        assert azuis[lado] > 2 * azuis['left' if lado == 'right' else 'right']


# ── IA: pesos ────────────────────────────────────────────────────────────────
def _sortear(z, n=2000):
    random.seed(7)
    z._agora = relogio.agora()
    z.contexto.atualizar(z, DT)
    z.cd = {nome: 0 for nome in z.cd}
    return Counter(z.escolher_habilidade(z._agora) for _ in range(n))


def test_longe_nunca_usa_o_combo_e_tende_a_ficar_invisivel(zealot):
    _jogador_em(zealot, LONGE)
    c = _sortear(zealot)
    assert c['combo'] == 0
    assert 0.6 < c['furtivo'] / c.total() < 1           # tende: às vezes só persegue
    assert c[None] > 0 and zealot.wait > 0


def test_media_distancia_usa_os_dois_com_mais_combo(zealot):
    _jogador_em(zealot, MEDIO)
    c = _sortear(zealot)
    assert c['combo'] > 2 * c['furtivo'] > 0 and set(c) == {'combo', 'furtivo'}


def test_curta_distancia_usa_o_combo(zealot):
    _jogador_em(zealot, PERTO)
    assert set(_sortear(zealot, 200)) == {'combo'}


@pytest.mark.parametrize('deslocamento, faixa', [
    (V(CFG.dist_perto, 0), 'perto'), (V(CFG.dist_perto + 1, 0), 'medio'),
    (V(CFG.dist_medio, 0), 'medio'), (V(CFG.dist_medio + 1, 0), 'longe')])
def test_faixas_de_distancia(zealot, deslocamento, faixa):
    _jogador_em(zealot, deslocamento)
    zealot.contexto.atualizar(zealot, DT)
    assert zealot.faixa_de_distancia() == faixa


def test_habilidade_em_cooldown_nao_e_escolhida(zealot):
    _jogador_em(zealot, MEDIO)
    zealot.contexto.atualizar(zealot, DT)
    zealot._agora = relogio.agora()
    zealot.cd = {'combo': zealot._agora + 1, 'furtivo': 0}
    assert {zealot.escolher_habilidade(zealot._agora) for _ in range(50)} == {'furtivo'}
    zealot.cd['furtivo'] = zealot._agora + 1
    assert zealot.escolher_habilidade(zealot._agora) is None and zealot.wait == 0


def test_longe_sem_habilidade_corre_ate_o_jogador(zealot):
    _sem_ia(zealot)
    _jogador_em(zealot, LONGE)
    _passos(zealot, 0.5)
    assert zealot.posicao.x - CENTRO.x == pytest.approx(CFG.velocidade * CFG.mult_sprint * 0.5, rel=0.1)


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


def test_pausa_entre_dashes_fica_entre_meio_e_um_segundo(zealot):
    pausas = []
    for seed in range(6):
        random.seed(seed)
        _jogador_em(zealot, MEDIO)
        dashes, _ = _assistir_combo(zealot)
        pausas += [dashes[1][0] - dashes[0][1], dashes[2][0] - dashes[1][1]]
    margem = DT * 2000
    assert all(500 - margem <= p <= 1000 + margem for p in pausas), pausas
    assert max(pausas) - min(pausas) > 100              # não é robotizado


def test_dash_vai_ate_onde_o_jogador_estava(zealot):
    _jogador_em(zealot, MEDIO)
    alvo = V(zealot.jogador.posicao)
    _iniciar(zealot, 'combo')
    _ate(zealot, lambda: zealot.posicao != CENTRO)
    _jogador_em(zealot, V(0, 900))                      # fugiu durante o dash: ele não faz curva
    _ate(zealot, lambda: zealot.velocidade == 0 and zealot.is_inofensivo)
    assert zealot.posicao.distance_to(alvo) < 1


def test_golpes_saem_no_vetor_do_dash_e_nao_no_jogador(zealot):
    """Quem desvia para o lado durante o dash não leva o golpe virado para ele."""
    _jogador_em(zealot, MEDIO)

    def desviar(numero_de_dashes):
        zealot.jogador.posicao.update(zealot.posicao + (V(350, 0) if numero_de_dashes % 2 else V(0, -350)))

    dashes, golpes = _assistir_combo(zealot, desviar)
    for (aviso, _, posicao), dash in zip(golpes, dashes[1:]):
        assert aviso.direcao == dash[2]
        assert aviso.posicao == posicao                 # parte de onde ele parou


def test_esquiva_lateral_escapa_da_estocada_e_correr_para_tras_nao(zealot):
    p = zealot.jogador
    for fuga, acerta in ((V(300, 0), True), (V(0, 120), False)):
        recebidos = []
        p.receber_dano = recebidos.append
        zealot.posicao.update(CENTRO)
        p.posicao.update(CENTRO)
        duracao = zealot._estocada(V(1, 0))
        p.posicao.update(CENTRO + fuga)
        aviso = _avisos(RectStrikeAviso)[-1]
        for _ in range(round(duracao / 1000 / DT) + 2):
            relogio.avancar(DT)
            aviso.update(DT)
        assert bool(recebidos) is acerta, fuga
        if acerta:
            assert recebidos[0].valor == aviso.cfg.dano and recebidos[0].fonte is zealot


def test_parado_entre_os_dashes_nao_da_dano_de_contato(zealot):
    _jogador_em(zealot, MEDIO)
    em_dash, parado = set(), set()

    def anotar(n):
        if n and zealot.rotina is not None:
            (em_dash if zealot.animador.clip == 'dash' else parado).add(zealot.inofensivo)

    _assistir_combo(zealot, anotar)
    assert em_dash == {False} and parado == {True}
    assert not zealot.inofensivo


def test_presets_seguem_o_pedido():
    estocada, varredura = RECT_STRIKE_PRESETS['zealot_estocada'], CONE_STRIKE_PRESETS['zealot_varredura']
    contra = CONE_STRIKE_PRESETS['zealot_contra_ataque']
    assert estocada.largura < estocada.altura / 5 and estocada.duracao <= 400   # fino e curtíssimo
    assert estocada.dano > varredura.dano                                       # altíssimo dano
    assert contra.angulo_spray < varredura.angulo_spray and contra.raio > varredura.raio
    assert DASH_PRESETS['zealot'].ate_o_alvo and not DASH_PRESETS['zealot_bote'].ate_o_alvo
    assert DASH_PRESETS['zealot_bote'].velocidade > DASH_PRESETS['zealot'].velocidade


def test_dash_nao_atravessa_parede(zealot):
    paredes = GradeParedes([{'tipo': 'linha', 'pontos': [CENTRO + V(200, -600), CENTRO + V(200, 600)]}])
    _jogador_em(zealot, MEDIO)
    _iniciar(zealot, 'combo')
    for _ in range(round(1.5 / DT)):
        _passo(zealot, paredes)
        assert zealot.posicao.x < CENTRO.x + 200


# ── Invisibilidade ofensiva ──────────────────────────────────────────────────
def test_furtivo_persegue_invisivel_e_mais_rapido(zealot):
    _jogador_em(zealot, LONGE)
    base = zealot.velocidade_base
    _iniciar(zealot, 'furtivo')
    _passos(zealot, 1.0)
    assert not zealot.alvejavel and not zealot.invulneravel
    assert zealot.posicao.x - CENTRO.x == pytest.approx(base * (1 + CFG.furtivo_buff), rel=0.05)
    assert zealot.velocidade_base == base               # é buff, não muda a base


def test_furtivo_perto_da_um_bote_que_passa_reto(zealot):
    _jogador_em(zealot, MEDIO)
    _iniciar(zealot, 'furtivo')
    _ate(zealot, lambda: zealot.animador.clip == 'dash')
    assert zealot.status.mult_velocidade == 1.0         # o buff é só enquanto invisível
    assert zealot.alvejavel
    partida, jogador = V(zealot.posicao), V(zealot.jogador.posicao)
    assert partida.distance_to(jogador) <= CFG.furtivo_dist_bote + 1
    _ate(zealot, lambda: zealot.animador.clip != 'dash')
    cfg = DASH_PRESETS['zealot_bote']
    assert zealot.posicao.x > jogador.x + 300           # passou reto
    assert zealot.posicao.x - partida.x == pytest.approx(cfg.velocidade * cfg.duracao_ms / 1000, rel=0.1)
    _ate(zealot, lambda: zealot.rotina is None)
    assert zealot.cd['furtivo'] > relogio.agora() and zealot.invisibilidade is None


def test_furtivo_nao_da_bote_ainda_sumindo(zealot):
    _jogador_em(zealot, PERTO)
    _iniciar(zealot, 'furtivo')
    while zealot.fase_invisibilidade in (None, FADE_OUT):
        assert zealot.animador.clip != 'dash'
        _passo(zealot)


def test_furtivo_com_o_jogador_mantendo_distancia_acaba_sem_bote(zealot):
    _iniciar(zealot, 'furtivo')
    clips = set()
    for _ in range(round(10 / DT)):
        _jogador_em(zealot, LONGE)
        _passo(zealot)
        clips.add(zealot.animador.clip)
        if zealot.rotina is None:
            break
    assert zealot.rotina is None and 'dash' not in clips
    assert zealot.invisibilidade is None and zealot.alpha_atual == 255
    assert zealot.status.mult_velocidade == 1.0


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


def test_fuga_afasta_do_jogador_parado(zealot):
    _jogador_em(zealot, PERTO)
    _quebrar_escudo(zealot)
    _passos(zealot, 1.5)
    assert zealot.dist_jogador() > 400


def test_fuga_muda_de_rumo_ao_acaso(zealot):
    random.seed(1)
    _jogador_em(zealot, PERTO)
    _quebrar_escudo(zealot)
    rumos = []
    for _ in range(round(6 / DT)):
        _passo(zealot)
        if zealot.ultima_habilidade == 'defensiva' and zealot._ponto_fuga not in rumos:
            rumos.append(V(zealot._ponto_fuga))
    assert len(rumos) >= 4


def test_fuga_nao_passa_por_cima_do_jogador(zealot):
    _jogador_em(zealot, V(200, 0))
    zealot._agora = relogio.agora()
    for seed in range(40):
        random.seed(seed)
        ponto = zealot._sortear_ponto_de_fuga() - zealot.posicao
        assert abs(ponto.angle_to(V(1, 0))) % 360 >= CFG.fuga_angulo_graus - 1e-6


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


def test_fuga_so_vai_a_pontos_validos_e_alcancaveis(zealot):
    zealot.verificar_posicao_valida = lambda p: p.y < CENTRO.y
    zealot.game.mapa.caminho_livre = lambda a, b: b.x < CENTRO.x
    for seed in range(20):
        random.seed(seed)
        ponto = zealot._sortear_ponto_de_fuga()
        assert ponto.y < CENTRO.y and ponto.x < CENTRO.x
    zealot.verificar_posicao_valida = lambda p: False   # nenhum ponto: direto para longe do jogador
    _jogador_em(zealot, V(100, 0))
    assert zealot._sortear_ponto_de_fuga().x < zealot.posicao.x


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
    _jogador_em(zealot, V(0, CFG.fuga_dist_limite - 20))
    alvo, escudo = V(zealot.jogador.posicao), zealot.escudo_atual
    assert 0 < escudo < zealot.escudo_maximo
    _passos(zealot, 2 * DT)
    assert zealot.alvejavel and zealot.status.mult_velocidade == 1.0 and zealot.animador.clip == 'dash'
    _ate(zealot, lambda: _avisos(ConeStrikeAviso))
    cone, = _avisos(ConeStrikeAviso)
    assert cone.cfg is CONE_STRIKE_PRESETS['zealot_contra_ataque'] and cone.direcao == V(0, 1)
    assert zealot.posicao.distance_to(alvo) < 1 and zealot.inofensivo
    _ate(zealot, lambda: zealot.rotina is None)
    assert zealot.escudo_atual == escudo                # parou de regenerar
    assert not zealot.inofensivo
    _passo(zealot)
    assert zealot.ultima_habilidade == 'defensiva' and zealot.rotina is None   # voltou ao ofensivo


def test_encostar_logo_no_comeco_nao_o_traz_de_volta(zealot):
    _quebrar_escudo(zealot)
    _passo(zealot)
    for _ in range(round((CFG.fuga_min_ms - 100) / 1000 / DT)):
        _jogador_em(zealot, V(60, 0))
        _passo(zealot)
        assert not zealot.alvejavel
    _jogador_em(zealot, V(60, 0))
    _ate(zealot, lambda: zealot.alvejavel, 0.3)         # passou o mínimo: contra-ataca


def test_terminar_o_contra_ataque_sem_escudo_o_faz_fugir_de_novo(zealot):
    _quebrar_escudo(zealot)
    _sem_ia(zealot)
    _passos(zealot, CFG.fuga_min_ms / 1000 + 0.2)
    _jogador_em(zealot, V(100, 0))
    _ate(zealot, lambda: zealot.animador.clip == 'dash')
    _quebrar_escudo(zealot)
    _ate(zealot, lambda: zealot.rotina is None)
    _passo(zealot)
    assert zealot.rotina is not None and not zealot.alvejavel


def test_tiro_perdido_acerta_a_vida_dele_fugindo(zealot):
    _quebrar_escudo(zealot)
    _passos(zealot, 1)
    antes = zealot.vida + zealot.escudo_atual
    zealot.receber_dano(Dano(30, PROJETIL))
    assert zealot.vida + zealot.escudo_atual == pytest.approx(antes - 30)


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


def test_antistuck_sem_ponto_valido_fica_onde_esta(zealot):
    zealot.verificar_posicao_valida = lambda p: False
    _jogador_em(zealot, V(1500, 0))
    _iniciar(zealot, 'antistuck')
    _ate(zealot, lambda: zealot.rotina is None)
    assert zealot.posicao.distance_to(CENTRO) < 5      # não teleportou


# ── VFX ──────────────────────────────────────────────────────────────────────
def test_rastro_so_no_dash_some_sozinho_e_nao_aloca(novo_jogo, zealot):
    tela, zero = pygame.Surface((3000, 3000)), V(0, 0)
    _jogador_em(zealot, MEDIO)
    zealot.draw_extras(tela, zero)
    assert len(zealot.rastro) == 0
    _iniciar(zealot, 'combo')
    _ate(zealot, lambda: len(zealot.rastro) >= 5)
    with contar_alocacoes() as c:
        zealot.draw_extras(tela, zero)
    assert c.total == 0
    x, y = zealot.rastro[0][1:3]
    caixa = tela.subsurface((x, y, *zealot.quadro_original.get_size()))
    assert pygame.transform.average_color(caixa)[2] > 5
    relogio.avancar(1)
    zealot.draw_extras(tela, zero)
    assert len(zealot.rastro) == 0


def test_silhuetas_do_rastro_prontas_no_spawn(zealot):
    from source.utils import superficies
    for frames in zealot.sprites.values():
        for frame in frames:
            assert CFG.cor_energia in superficies._SILHUETAS[frame]
            assert silhueta_de(frame, CFG.cor_energia).get_size() == frame.get_size()


def test_quebra_do_escudo_solta_faiscas_e_treme_uma_vez(zealot):
    camera = zealot.game.camera
    zealot.receber_dano(Dano(10, PROJETIL))
    assert len(entity_manager.particulas_grupo) == 0
    _quebrar_escudo(zealot)
    assert len(entity_manager.particulas_grupo) == CFG.faiscas_escudo
    assert relogio.agora() < camera.shake_timer and camera.shake_intensidade == CFG.shake_escudo
    zealot.receber_dano(Dano(1, PROJETIL))              # já sem escudo: nada de novo
    assert len(entity_manager.particulas_grupo) == CFG.faiscas_escudo


@pytest.mark.parametrize('classe', [RectStrikeAviso, ConeStrikeAviso])
def test_golpes_soltam_faiscas_mesmo_com_o_zealot_morto(zealot, classe):
    if classe is RectStrikeAviso:
        zealot._estocada(V(1, 0))
    else:
        zealot._cone(V(1, 0), CFG.combo_cone_preset)
    zealot.kill()
    aviso, = _avisos(classe)
    for _ in range(round(1 / DT)):
        relogio.avancar(DT)
        if aviso.alive():
            aviso.update(DT)
    assert len(entity_manager.particulas_grupo) >= CFG.faiscas_golpe
    assert zealot.game.camera.shake_intensidade == CFG.shake_golpe


def test_fugindo_nao_deixa_rastro_azul(zealot):
    """Só a distorção o denuncia."""
    _quebrar_escudo(zealot)
    _passos(zealot, 1.4)
    assert len(zealot.rastro) == 0


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
    assert z.alive() and {'combo', 'furtivo', 'defensiva'} <= usadas, usadas
    assert z.escudo_atual > 0                           # regenerou
    assert novo_jogo.renderer._erros_logados == set()


# ── Config ───────────────────────────────────────────────────────────────────
@pytest.mark.parametrize('kwargs', [
    {'pesos': {'perto': {'combo': 1}, 'medio': {'combo': 1}}},
    {'pesos': {'perto': {'combo': 1}, 'medio': {'combo': 1}, 'longe': {'combo': 1}}},
    {'pesos': {'perto': {'inexistente': 1}, 'medio': {'combo': 1}, 'longe': {'furtivo': 1}}},
    {'pesos': {'perto': {'combo': 0}, 'medio': {'combo': 1}, 'longe': {'furtivo': 1}}},
    {'pesos': {'perto': {}, 'medio': {'combo': 1}, 'longe': {'furtivo': 1}}},
    {'cooldown_inicial': {'combo': 1}},
    {'dist_perto': 700}, {'dist_perto': 0}, {'fuga_dist_limite': 900},
])
def test_config_invalida(kwargs):
    with pytest.raises(ValueError):
        ZealotConfig(**kwargs)


def test_presets_de_invisibilidade_do_zealot():
    assert INVISIBILIDADE_PRESETS[CFG.fuga_preset].duracao_ms is None   # a rotina decide quando acaba
    assert INVISIBILIDADE_PRESETS[CFG.furtivo_preset].duracao_ms > 0
