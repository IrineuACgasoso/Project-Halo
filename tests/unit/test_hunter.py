"""Hunter reformulado: armadura (Defesa) × costas, virar com atraso, IA por distância, dash, slam e vfx."""
import random
from collections import Counter

import pygame
import pytest

from helpers import DT, blindar_jogador, contar_alocacoes
from source.enemies.minibosses.hunter.config import CFG, HunterConfig
from source.enemies.minibosses.hunter import vfx
from source.feats.projetil import PlasmaGun
from source.feats.skills.artilharia import ArtilhariaAviso
from source.feats.skills.cone_strike import ConeStrikeAviso
from source.feats.skills.mortar import CanhaoParabolico
from source.systems.dano import PROJETIL, Dano
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.systems.status import Defesa, Fraqueza, aplicar

V = pygame.math.Vector2
CENTRO = V(1500, 1500)


@pytest.fixture
def hunter(novo_jogo):
    novo_jogo.spawner.spawnar('hunter')
    h = novo_jogo.sessao.boss_atual
    h.posicao.update(CENTRO)
    h.sync_rect()
    h.escudo_atual, h.vida = 0, 10 ** 6
    h.invencivel = False
    blindar_jogador(novo_jogo.player)
    _jogador_em(h, V(300, 0))
    return h


def _jogador_em(h, deslocamento):
    h.jogador.posicao.update(h.posicao + deslocamento)


def _parar_ia(h):
    """Sem pensar nem andar: só orientação, vulnerabilidade e animação."""
    h.livre_em = float('inf')
    h.movimento_livre = False


def _passos(h, segundos):
    for _ in range(round(segundos / DT)):
        relogio.avancar(DT)
        h.update(DT)


def _olhando_para(h, lado):
    h.virar_para(lado)
    h.virar_em = None
    h.atualizar_vulnerabilidade()


def _vida_tirada(h, valor=100):
    antes = h.vida
    h.receber_dano(Dano(valor, PROJETIL))
    return antes - h.vida


# ── Armadura e costas ────────────────────────────────────────────────────────
COSTAS = V(-300, 0)
@pytest.mark.parametrize('lado, deslocamento, vulneravel', [
    (1, V(300, 0), False),                                # olhando para a direita, jogador na frente
    (1, COSTAS, True),                                    # costas, no eixo
    (1, COSTAS.rotate(CFG.costas_graus - 1), True),       # costas, 1° dentro da borda do cone
    (1, COSTAS.rotate(-(CFG.costas_graus - 1)), True),
    (1, COSTAS.rotate(CFG.costas_graus + 1), False),      # costas, 1° fora do cone
    (1, COSTAS.rotate(-(CFG.costas_graus + 1)), False),
    (1, V(0, 300), False),                                # de lado
    (-1, V(300, 0), True),                                # olhando para a esquerda: costas = +x
    (-1, V(-300, 0), False),
])
def test_vulneravel_so_nas_costas_dentro_do_cone(hunter, lado, deslocamento, vulneravel):
    _parar_ia(hunter)
    _jogador_em(hunter, deslocamento)
    _olhando_para(hunter, lado)
    assert hunter.vulneravel is vulneravel
    assert hunter.status.tem(Defesa) is (not vulneravel)
    assert _vida_tirada(hunter) == pytest.approx(100 if vulneravel else 100 * (1 - CFG.defesa))


def test_sair_das_costas_devolve_a_defesa(hunter):
    _parar_ia(hunter)
    _olhando_para(hunter, 1)
    _jogador_em(hunter, V(-200, 0))
    hunter.atualizar_vulnerabilidade()
    assert hunter.vulneravel and hunter.status.mult_dano_recebido == 1.0
    _jogador_em(hunter, V(-200, 200))
    hunter.atualizar_vulnerabilidade()
    assert not hunter.vulneravel and hunter.status.mult_dano_recebido == pytest.approx(0.1)
    assert len([e for e, _, _ in hunter.status.ativos() if type(e) is Defesa]) == 1


def test_fraqueza_vale_de_frente_e_pelas_costas(hunter):
    _parar_ia(hunter)
    aplicar(hunter, Fraqueza(0.5, 1000))
    _olhando_para(hunter, 1)
    _jogador_em(hunter, V(300, 0))
    hunter.atualizar_vulnerabilidade()
    assert _vida_tirada(hunter) == pytest.approx(100 * 1.5 * 0.1)
    _jogador_em(hunter, V(-300, 0))
    hunter.atualizar_vulnerabilidade()
    assert _vida_tirada(hunter) == pytest.approx(150)


def test_nasce_protegido(hunter):
    assert hunter.status.tem(Defesa)


# ── Virar com atraso ─────────────────────────────────────────────────────────
def test_vira_so_depois_do_atraso(hunter):
    _parar_ia(hunter)
    _olhando_para(hunter, 1)
    _jogador_em(hunter, V(-300, 0))
    _passos(hunter, CFG.atraso_virar_ms / 1000 - 0.1)
    assert hunter.lado == 1 and hunter.estado_animacao == 'right'
    assert hunter.vulneravel                          # enquanto não vira, o jogador está nas costas
    _passos(hunter, 0.2)
    assert hunter.lado == -1 and hunter.estado_animacao == 'left'
    assert not hunter.vulneravel


def test_spam_de_lado_nao_reinicia_o_timer_e_vale_o_lado_no_vencimento(hunter):
    _parar_ia(hunter)
    _olhando_para(hunter, 1)
    lados = [V(-300, 0), V(300, 0)]
    for i in range(7):                                # 7 × 0,2 s = 1,4 s trocando de lado
        _jogador_em(hunter, lados[i % 2])
        _passos(hunter, 0.2)
    _jogador_em(hunter, V(-300, 0))
    _passos(hunter, 0.2)                              # vence aos 1,5 s com o jogador à esquerda
    assert hunter.lado == -1


def test_no_vencimento_com_o_jogador_na_frente_nao_vira(hunter):
    _parar_ia(hunter)
    _olhando_para(hunter, 1)
    _jogador_em(hunter, V(-300, 0))
    _passos(hunter, 0.5)
    _jogador_em(hunter, V(300, 0))
    _passos(hunter, 1.2)
    assert hunter.lado == 1 and hunter.virar_em is None


# ── Dash ─────────────────────────────────────────────────────────────────────
def _iniciar(h, nome):
    h.ultima_habilidade = nome
    h.rotina = getattr(h, f'rotina_{nome}')()
    h.livre_em = float('inf')


def test_dash_corre_olhando_para_o_lado_da_corrida_e_depois_fica_parado(hunter):
    _olhando_para(hunter, 1)
    _jogador_em(hunter, V(-300, 0))
    _iniciar(hunter, 'dash')
    _passos(hunter, DT)
    assert hunter.lado == -1 and not hunter.is_inofensivo
    _passos(hunter, 2.0)
    assert hunter.posicao.x == pytest.approx(CENTRO.x - 500 * 2.0, abs=1)   # passou do jogador
    assert hunter.is_inofensivo and hunter.animacao_congelada and hunter.estado_habilidade == 'stun'
    parado = V(hunter.posicao)
    frame = hunter.frame_atual
    _passos(hunter, CFG.atraso_virar_pos_dash_ms / 1000 - 0.1)
    assert hunter.posicao == parado and hunter.frame_atual == frame
    assert hunter.lado == -1                          # o jogador ficou nas costas: ainda não virou
    assert hunter.vulneravel
    _passos(hunter, 0.2)
    assert hunter.lado == 1 and not hunter.is_inofensivo and hunter.rotina is None
    assert hunter.cd['dash'] > relogio.agora()


def test_dash_com_o_jogador_na_frente_depois_tambem_fica_parado(hunter):
    _olhando_para(hunter, 1)
    _jogador_em(hunter, V(1500, 0))                   # longe: o dash para antes dele
    _iniciar(hunter, 'dash')
    _passos(hunter, 2.05)
    parado = V(hunter.posicao)
    assert not hunter.vulneravel
    _passos(hunter, 2.0)
    assert hunter.posicao == parado and hunter.is_inofensivo


def test_dash_solta_poeira_para_os_lados(hunter):
    _olhando_para(hunter, 1)
    _jogador_em(hunter, V(300, 0))
    _iniciar(hunter, 'dash')
    antes = len(entity_manager.particulas_grupo)
    _passos(hunter, 1.0)
    emitidas = len(entity_manager.particulas_grupo) - antes
    assert 10 <= emitidas <= 40                       # ~11 rajadas de 2 grãos: pouca poeira


# ── Shield slam ──────────────────────────────────────────────────────────────
def test_slam_so_com_o_jogador_colado_e_na_frente(hunter):
    _olhando_para(hunter, 1)
    for deslocamento, pode in [(V(150, 0), True), (V(150, 140), True), (V(150, 160), False),
                               (V(-150, 0), False), (V(400, 0), False)]:
        _jogador_em(hunter, deslocamento)
        assert hunter.pode_slam() is pode, deslocamento


def test_slam_e_um_cone_de_90_graus_no_eixo_de_frente_e_solta_poeira(hunter):
    _olhando_para(hunter, -1)
    _jogador_em(hunter, V(-150, 60))
    hunter.movimento_livre = False
    _iniciar(hunter, 'slam')
    _passos(hunter, DT)
    cones = [s for s in entity_manager.all_sprites if isinstance(s, ConeStrikeAviso)]
    assert len(cones) == 1
    cone = cones[0]
    assert cone.cfg.angulo_spray == 90 and cone.direcao == V(-1, 0) and cone.fonte is hunter
    assert cone.cfg.duracao > 750                     # carga mais lenta que o cleave do Knight
    antes = len(entity_manager.particulas_grupo)
    for _ in range(round(cone.cfg.duracao / 1000 / DT) + 5):
        relogio.avancar(DT)
        cone.update(DT)
        hunter.update(DT)
    assert len(entity_manager.particulas_grupo) - antes >= CFG.poeira_slam
    assert hunter.rotina is None and hunter.cd['slam'] > relogio.agora()


# ── Longe: canhão e burst andando ────────────────────────────────────────────
def test_canhao_dispara_com_poeira_na_explosao_e_segue_andando(hunter):
    _jogador_em(hunter, V(800, 0))
    _iniciar(hunter, 'canhao')
    _passos(hunter, DT)
    canhoes = [s for s in entity_manager.all_sprites if isinstance(s, CanhaoParabolico)]
    assert len(canhoes) == 1 and canhoes[0].ao_explodir is vfx.impacto_do_canhao
    assert canhoes[0].fonte is hunter and hunter.movimento_livre


def test_burst_dispara_todos_os_tiros_andando(hunter):
    _jogador_em(hunter, V(800, 0))
    hunter.modo_movimento, hunter.troca_movimento_em = 'avancar', float('inf')
    _iniciar(hunter, 'burst')
    inicio = V(hunter.posicao)
    _passos(hunter, CFG.burst_tiros * CFG.burst_intervalo_ms / 1000 + 0.1)
    tiros = [s for s in entity_manager.all_sprites if isinstance(s, PlasmaGun) and s.fonte is hunter]
    assert len(tiros) == CFG.burst_tiros
    assert hunter.posicao.x > inicio.x                # andou em direção ao jogador enquanto atirava


# ── Camera shake ─────────────────────────────────────────────────────────────
def _tremendo(camera):
    return relogio.agora() < camera.shake_timer


def test_burst_treme_fraco_durante_toda_a_rajada_e_para_no_fim(hunter):
    camera = hunter.game.camera
    _jogador_em(hunter, V(800, 0))
    _iniciar(hunter, 'burst')
    _passos(hunter, DT)
    for _ in range(CFG.burst_tiros * CFG.burst_intervalo_ms // round(DT * 1000) - 2):
        assert _tremendo(camera) and camera.shake_intensidade == CFG.shake_burst
        _passos(hunter, DT)
    _passos(hunter, 0.1)
    assert hunter.rotina is None and not _tremendo(camera)


def test_slam_treme_na_hora_do_golpe(hunter):
    camera = hunter.game.camera
    _olhando_para(hunter, 1)
    _jogador_em(hunter, V(150, 0))
    hunter.movimento_livre = False
    _iniciar(hunter, 'slam')
    _passos(hunter, DT)
    cone = next(s for s in entity_manager.all_sprites if isinstance(s, ConeStrikeAviso))
    while not cone.explodiu:
        assert not _tremendo(camera)                  # na carga, nada
        relogio.avancar(DT)
        cone.update(DT)
    assert _tremendo(camera) and camera.shake_intensidade == CFG.shake_slam


def test_canhao_treme_forte_na_explosao_mesmo_com_o_hunter_morto(hunter):
    camera = hunter.game.camera
    _jogador_em(hunter, V(200, 0))
    _iniciar(hunter, 'canhao')
    _passos(hunter, DT)
    hunter.kill()
    canhao = next(s for s in entity_manager.all_sprites if isinstance(s, CanhaoParabolico))
    for _ in range(round(2 / DT)):                    # voo + carga da artilharia
        relogio.avancar(DT)
        for s in [canhao, *(s for s in entity_manager.all_sprites if isinstance(s, ArtilhariaAviso))]:
            if s.alive():
                s.update(DT)
        if _tremendo(camera):
            break
    assert _tremendo(camera) and camera.shake_intensidade == CFG.shake_canhao


def test_movimento_lateral_e_perpendicular(hunter):
    _jogador_em(hunter, V(800, 0))
    hunter.livre_em = float('inf')
    hunter.modo_movimento, hunter.sentido_lateral, hunter.troca_movimento_em = 'lateral', 1, float('inf')
    _passos(hunter, 1)
    # perpendicular a cada passo = orbita o jogador: a distância quase não muda (800 -> ~801)
    assert hunter.posicao.distance_to(hunter.jogador.posicao) == pytest.approx(800, abs=2)
    assert abs(hunter.posicao.y - CENTRO.y) == pytest.approx(CFG.velocidade, rel=0.05)


# ── IA ───────────────────────────────────────────────────────────────────────
def _sortear(h, n=2000):
    random.seed(7)
    agora = relogio.agora()
    for nome in h.cd:
        h.cd[nome] = agora
    contagem = Counter()
    for _ in range(n):
        h.ultima_habilidade = None
        contagem[h.escolher_habilidade(agora)] += 1
    return contagem


def test_longe_prefere_os_canhoes_e_nunca_da_slam(hunter):
    _olhando_para(hunter, 1)
    _jogador_em(hunter, V(900, 0))
    c = _sortear(hunter)
    assert c['slam'] == 0 and c['dash'] > 0                       # não determinista
    assert (c['canhao'] + c['burst']) / sum(c.values()) > 0.8


def test_perto_prefere_os_golpes_fisicos(hunter):
    _olhando_para(hunter, 1)
    _jogador_em(hunter, V(150, 0))                                 # colado e na frente
    c = _sortear(hunter)
    assert c['canhao'] > 0 and c['burst'] > 0                      # não determinista
    assert (c['dash'] + c['slam']) / sum(c.values()) > 0.8


def test_perto_mas_nas_costas_nao_da_slam(hunter):
    _olhando_para(hunter, 1)
    _jogador_em(hunter, V(-150, 0))
    assert _sortear(hunter, 500)['slam'] == 0


def test_habilidade_em_cooldown_nao_e_escolhida(hunter):
    _jogador_em(hunter, V(900, 0))
    agora = relogio.agora()
    hunter.cd = {nome: agora + 10_000 for nome in hunter.cd}
    hunter.cd['burst'] = agora
    assert {hunter.escolher_habilidade(agora) for _ in range(50)} == {'burst'}
    hunter.cd['burst'] = agora + 1
    assert hunter.escolher_habilidade(agora) is None


def test_luta_de_20_segundos_usa_as_habilidades_sem_quebrar(novo_jogo, hunter):
    """Loop real (com paredes e colisão): o jogador parado perto dele."""
    from helpers import simular
    random.seed(3)
    _jogador_em(hunter, V(350, 0))
    usadas = set()
    for _ in range(20):
        simular(novo_jogo, 1)
        usadas.add(hunter.ultima_habilidade)
    assert hunter.alive() and {'dash'} <= usadas


# ── VFX ──────────────────────────────────────────────────────────────────────
def test_brilho_so_quando_vulneravel_e_sem_alocar(novo_jogo, hunter):
    _parar_ia(hunter)
    _olhando_para(hunter, 1)
    tela = pygame.Surface((3000, 3000))
    zero = V(0, 0)
    tela.fill((0, 0, 0))
    hunter.draw_extras(tela, zero)
    assert tela.get_at(hunter.rect.center)[:3] == (0, 0, 0)
    _jogador_em(hunter, V(-300, 0))
    hunter.atualizar_vulnerabilidade()
    with contar_alocacoes() as c:
        for _ in range(30):
            relogio.avancar(DT)
            hunter.draw_extras(tela, zero)
    assert c.total == 0
    r, g, b = tela.get_at(hunter.rect.center)[:3]
    assert r > 100 and g <= CFG.brilho_cor[1] and b <= CFG.brilho_cor[2]   # vermelho por cima do preto


def test_alpha_do_brilho_pulsa_entre_os_limites():
    valores = {vfx.alpha_do_brilho(t) for t in range(0, CFG.brilho_periodo_ms, 10)}
    assert min(valores) >= CFG.brilho_alpha[0] and max(valores) <= CFG.brilho_alpha[1]
    assert max(valores) - min(valores) > 50


def test_silhuetas_prontas_no_spawn(hunter):
    for frames in hunter.sprites.values():
        for frame in frames:
            assert frame in vfx._SILHUETAS
            assert vfx._SILHUETAS[frame].get_size() == frame.get_size()


# ── Config ───────────────────────────────────────────────────────────────────
@pytest.mark.parametrize('kwargs', [
    {'pesos_longe': {'canhao': 1}},
    {'cooldown_inicial': {'canhao': 1, 'burst': 1, 'dash': 1}},
    {'costas_graus': 0}, {'costas_graus': 90}, {'slam_frente_graus': 95},
])
def test_config_invalida(kwargs):
    with pytest.raises(ValueError):
        HunterConfig(**kwargs)
