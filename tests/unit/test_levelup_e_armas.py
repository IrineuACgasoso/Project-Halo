"""Registro de armas, sorteio da tela de upgrade e regras de upgrade (integridade dos dados: test_validacao.py)."""
import dataclasses
import inspect
import random
from collections import Counter
from types import SimpleNamespace

import pygame
import pytest

from source.data.weapon_data import WEAPON_DATA, WeaponStats
from source.enemies.standard.grunt import GruntRed
from source.feats.weapons.baseweapon import Arma, ArmaDeRajada
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.systems.hud import hud_draw
from source.systems.levelup import (ARMAS_REGISTRO, MAX_ARMAS, NIVEL_MAXIMO_POR_RARIDADE,
                                   PESO_SORTEIO_POR_RARIDADE, TelaDeUpgrade, gerar_opcoes,
                                   sortear_armas_novas)
from source.systems.levelup.constants import ArmaInfo
from source.systems.levelup.draw import titulo_da_opcao

IDS = sorted(ARMAS_REGISTRO)


# Integridade do registro e de weapon_data: `validar_armas` (test_validacao.py, roteiro D5).


# ── WeaponStats / _deve_melhorar ─────────────────────────────────────────────
def test_weaponstats_aliases_legados():
    s = WeaponStats(value=1, range_val=3, min_val=50)
    assert s['range'] == 3 and s['min'] == 50 and s['value'] == 1


@pytest.mark.parametrize('range_val, nivel, esperado', [
    (0, 2, False), (None, 2, False),
    (2, 4, True), (2, 3, False), (1, 7, True),
    ([3, 5], 5, True), ([3, 5], 4, False),
])
def test_deve_melhorar(range_val, nivel, esperado):
    assert Arma._deve_melhorar(range_val, nivel) is esperado


def test_aplicar_upgrades_respeita_minimo(player):
    rifle = player.armas['assault_rifle']
    meta = WEAPON_DATA['assault_rifle'].stats['cooldown']
    for _ in range(200):
        rifle.upgrade()
    if meta.min_val is not None:
        assert rifle.cooldown >= meta.min_val


# ── TelaDeUpgrade ────────────────────────────────────────────────────────────
@pytest.mark.parametrize('semente', range(10))
def test_opcoes_aleatorias_validas(player, semente):
    random.seed(semente)
    tela = TelaDeUpgrade(player.game.tela, player, player.game)
    ids = tela.ids_das_opcoes
    assert 1 <= len(ids) <= 3
    assert len(set(ids)) == len(ids)
    assert all(i in ARMAS_REGISTRO for i in ids)


def test_com_arsenal_cheio_so_oferece_upgrades(player):
    for id_arma in IDS[:MAX_ARMAS]:
        player.armas[id_arma] = SimpleNamespace(no_maximo=False)
    for semente in range(10):
        random.seed(semente)
        tela = TelaDeUpgrade(player.game.tela, player, player.game)
        assert set(tela.ids_das_opcoes) <= set(player.armas)


def _tecla(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key, mod=0)


def test_navegacao_e_confirmacao(player):
    random.seed(0)
    tela = TelaDeUpgrade(player.game.tela, player, player.game)
    assert len(tela.opcoes) == 3
    assert tela.handle_event(_tecla(pygame.K_a)) is None
    assert tela.opcao_selecionada == 2                     # volta circular
    assert tela.handle_event(_tecla(pygame.K_RETURN)) == tela.ids_das_opcoes[2]


def test_modo_unico_ignora_navegacao(player):
    tela = TelaDeUpgrade(player.game.tela, player, player.game, id_arma_forcada='assault_rifle')
    tela.handle_event(_tecla(pygame.K_d))
    assert tela.opcao_selecionada == 0
    assert tela.handle_event(_tecla(pygame.K_SPACE)) == 'assault_rifle'


def test_desenho_da_tela_nao_falha(player):
    random.seed(0)
    TelaDeUpgrade(player.game.tela, player, player.game).draw(player.game.tela)


# ── EventManager: aplicar escolha ────────────────────────────────────────────
def test_escolher_arma_possuida_faz_upgrade(novo_jogo):
    rifle = novo_jogo.player.armas['assault_rifle']
    novo_jogo.event_manager._aplicar_escolha_de_upgrade('assault_rifle')
    assert rifle.nivel == 2


@pytest.mark.parametrize('id_arma', [i for i in IDS if i != 'assault_rifle'])
def test_escolher_arma_nova_equipa_e_sobe_ate_o_maximo(novo_jogo, id_arma):
    # Antes da E6 subia até o nível 21 (sem teto); agora para exatamente no máximo da raridade.
    em = novo_jogo.event_manager
    em._aplicar_escolha_de_upgrade(id_arma)
    arma = novo_jogo.player.armas[id_arma]
    info = ARMAS_REGISTRO[id_arma]
    assert isinstance(arma, info.classe) and arma.nivel_maximo == info.nivel_maximo
    while arma.nivel < info.nivel_maximo:
        assert not arma.no_maximo
        # a tela de upgrade (preview de stats do próximo nível) não pode quebrar em nível alto
        TelaDeUpgrade(novo_jogo.tela, novo_jogo.player, novo_jogo, id_arma_forcada=id_arma).draw(novo_jogo.tela)
        em._aplicar_escolha_de_upgrade(id_arma)
    assert arma.nivel == info.nivel_maximo and arma.no_maximo
    em._aplicar_escolha_de_upgrade(id_arma)
    assert arma.nivel == info.nivel_maximo


# ── Raridade de fato (roteiro E6) ────────────────────────────────────────────
def test_maximos_e_pesos_decididos():
    # roteiro §8, itens 4 e 6
    assert NIVEL_MAXIMO_POR_RARIDADE == {'comum': 25, 'incomum': 20, 'rara': 15, 'epica': 10, 'lendaria': 5}
    assert PESO_SORTEIO_POR_RARIDADE == {'comum': 40, 'incomum': 25, 'rara': 20, 'epica': 10, 'lendaria': 5}


@pytest.mark.parametrize('id_arma', IDS)
def test_criar_passa_o_maximo_da_raridade(novo_jogo, id_arma):
    info = ARMAS_REGISTRO[id_arma]
    arma = info.criar(novo_jogo.player, novo_jogo)
    assert isinstance(arma, info.classe)
    assert arma.nivel == 1 and arma.nivel_maximo == NIVEL_MAXIMO_POR_RARIDADE[info.raridade]


def test_arma_inicial_nasce_com_o_maximo(novo_jogo):
    assert novo_jogo.player.armas['assault_rifle'].nivel_maximo == 25


def _ate_o_maximo(arma):
    while arma.upgrade():
        pass
    return arma


def _criar_no_maximo(game, id_arma):
    return _ate_o_maximo(ARMAS_REGISTRO[id_arma].criar(game.player, game))


def _numeros(arma):
    return {k: v for k, v in vars(arma).items() if isinstance(v, (int, float))}


@pytest.mark.parametrize('id_arma', IDS)
def test_upgrade_no_maximo_nao_faz_nada(novo_jogo, id_arma):
    arma = _criar_no_maximo(novo_jogo, id_arma)
    assert arma.nivel == ARMAS_REGISTRO[id_arma].nivel_maximo
    antes = _numeros(arma)
    assert arma.upgrade() is False
    assert _numeros(arma) == antes


def test_arma_criada_fora_do_registro_nao_tem_teto(novo_jogo):
    arma = ARMAS_REGISTRO['brick'].classe(novo_jogo.player, novo_jogo)
    for _ in range(30):
        assert arma.upgrade() is True
    assert arma.nivel == 31 and not arma.no_maximo


def test_upgrade_aplica_os_stats_do_nivel(novo_jogo):
    # a subida passa pelo gancho aplicar_nivel: o perfil dá +1 de dano no nível 2
    rifle = novo_jogo.player.armas['assault_rifle']
    dano = rifle.dano
    assert rifle.upgrade() is True
    assert rifle.nivel == 2 and rifle.dano == dano + 1


def test_arma_no_maximo_sai_do_sorteio_de_upgrade(novo_jogo):
    p = novo_jogo.player
    p.armas['assault_rifle'] = _criar_no_maximo(novo_jogo, 'assault_rifle')
    p.armas['brick'] = ARMAS_REGISTRO['brick'].criar(p, novo_jogo)
    for semente in range(50):
        ids = gerar_opcoes(p, random.Random(semente))
        assert 'assault_rifle' not in ids and len(ids) == 3 and len(set(ids)) == 3


def test_arsenal_cheio_com_uma_abaixo_do_maximo_oferece_so_ela(novo_jogo):
    p = novo_jogo.player
    p.armas.clear()
    for id_arma in IDS[:MAX_ARMAS - 1]:
        p.armas[id_arma] = _criar_no_maximo(novo_jogo, id_arma)
    p.armas[IDS[MAX_ARMAS - 1]] = ARMAS_REGISTRO[IDS[MAX_ARMAS - 1]].criar(p, novo_jogo)
    for semente in range(20):
        assert gerar_opcoes(p, random.Random(semente)) == [IDS[MAX_ARMAS - 1]]


def test_tudo_no_maximo_e_arsenal_cheio_nao_ha_opcao(novo_jogo):
    p = novo_jogo.player
    p.armas.clear()
    for id_arma in IDS[:MAX_ARMAS]:
        p.armas[id_arma] = _criar_no_maximo(novo_jogo, id_arma)
    assert gerar_opcoes(p) == []
    with pytest.raises(ValueError, match='sem opções'):
        TelaDeUpgrade(novo_jogo.tela, p, novo_jogo, ids_das_opcoes=[])


def test_tudo_no_maximo_com_vaga_so_oferece_armas_novas(novo_jogo):
    p = novo_jogo.player
    p.armas['assault_rifle'] = _criar_no_maximo(novo_jogo, 'assault_rifle')
    for semente in range(20):
        ids = gerar_opcoes(p, random.Random(semente))
        assert len(ids) == 3 and not set(ids) & set(p.armas)


def test_sorteio_de_armas_novas_respeita_os_pesos():
    # Uma arma de um pool com todas: a chance de cada uma é o peso dela / soma dos pesos.
    rng = random.Random(1234)
    n = 10_000
    contagem = Counter(sortear_armas_novas(IDS, 1, rng)[0] for _ in range(n))
    total = sum(ARMAS_REGISTRO[i].peso_sorteio for i in IDS)
    for id_arma in IDS:
        esperado = ARMAS_REGISTRO[id_arma].peso_sorteio / total
        assert abs(contagem[id_arma] / n - esperado) < 0.012, id_arma
    por_raridade = Counter()
    for id_arma, vezes in contagem.items():
        por_raridade[ARMAS_REGISTRO[id_arma].raridade] += vezes
    for raridade, peso in PESO_SORTEIO_POR_RARIDADE.items():
        qtd = sum(1 for i in IDS if ARMAS_REGISTRO[i].raridade == raridade)
        assert abs(por_raridade[raridade] / n - qtd * peso / total) < 0.02, raridade


def test_sorteio_de_armas_novas_sem_repeticao_e_com_limite():
    rng = random.Random(0)
    for k in range(len(IDS) + 2):
        escolhidas = sortear_armas_novas(IDS, k, rng)
        assert len(escolhidas) == min(k, len(IDS)) and len(set(escolhidas)) == len(escolhidas)
    assert sortear_armas_novas([], 3, rng) == []


def test_card_mostra_max_no_upgrade_que_leva_ao_maximo(novo_jogo):
    p = novo_jogo.player
    rifle = p.armas['assault_rifle']

    def titulo():
        return titulo_da_opcao(TelaDeUpgrade(novo_jogo.tela, p, novo_jogo, id_arma_forcada='assault_rifle').opcoes[0])

    assert titulo() == 'Rifle de Assalto (Nv. 2)'
    while rifle.nivel < rifle.nivel_maximo - 1:
        rifle.upgrade()
    assert titulo() == 'Rifle de Assalto (Nv. MAX)'


def test_hud_mostra_max_na_arma_no_maximo(novo_jogo):
    p = novo_jogo.player
    rifle = p.armas['assault_rifle']
    fonte = pygame.font.Font(None, 16)
    hud_draw._draw_weapon_slots(novo_jogo.tela, p, fonte)
    assert hud_draw._TEXTOS[('slot', 0)][0] == 'L1'
    _ate_o_maximo(rifle)
    hud_draw._draw_weapon_slots(novo_jogo.tela, p, fonte)
    assert hud_draw._TEXTOS[('slot', 0)][0] == 'MAX'


# ── Estado de alvo (roteiro E2) ──────────────────────────────────────────────
class _Mira(Arma):
    """Só as buscas de alvo da base (sem disparo)."""
    def __init__(self, jogador):
        self.jogador = jogador

    def disparar(self):
        return False


def _mira(game):
    return _Mira(game.player)


def _grunts(game, *deslocamentos):
    return [GruntRed(posicao=game.player.posicao + pygame.Vector2(dx, 0), game=game) for dx in deslocamentos]


@pytest.mark.parametrize('ajuste, alvejavel', [
    (lambda g: None, True),
    (lambda g: setattr(g, 'alpha_atual', 0), False),
    (lambda g: setattr(g, 'invis_phase', 'fade_out'), False),
    (lambda g: setattr(g, 'invis_phase', 'hold'), False),
    (lambda g: setattr(g, 'invis_phase', 'fade_in'), True),   # reaparecendo: já é alvo
    (lambda g: setattr(g, 'vida', 0), False),
])
def test_alvejavel(novo_jogo, ajuste, alvejavel):
    grunt, = _grunts(novo_jogo, 100)
    ajuste(grunt)
    assert grunt.alvejavel is alvejavel
    assert grunt.vivo is (grunt.vida > 0)


def test_invisivel_e_morto_nunca_sao_alvo(novo_jogo):
    invisivel, morto, longe = _grunts(novo_jogo, 50, 60, 400)
    invisivel.invis_phase, morto.vida = 'hold', 0
    arma = _mira(novo_jogo)
    grupo = [invisivel, morto, longe]
    assert arma.encontrar_inimigo_mais_proximo(grupo) is longe
    longe.alpha_atual = 0
    assert arma.encontrar_inimigo_mais_proximo(grupo) is None
    assert arma.encontrar_inimigo_mais_forte(grupo) is None


def test_mais_forte_e_escolhido_por_vida_dentro_do_raio(novo_jogo):
    fraco, forte, fora = _grunts(novo_jogo, 100, 200, 900)
    fraco.vida, forte.vida, fora.vida = 10, 50, 999
    arma = _mira(novo_jogo)
    assert arma.encontrar_inimigo_mais_forte([fraco, forte, fora], raio_maximo=500) is forte


# ── Grupos pelo nome e rajada (roteiro E4) ───────────────────────────────────
GRUPOS_DA_ARMA = ('all_sprites', 'inimigos_grupo', 'items_grupo', 'auras_grupo')


def test_ninguem_recebe_grupos_por_posicao():
    """A lista posicional de grupos (que fez o Fuel Rod mirar nos itens) não existe mais."""
    assert 'grupos' not in {f.name for f in dataclasses.fields(ArmaInfo)}
    com_grupos = [i for i, info in ARMAS_REGISTRO.items()
                  if 'grupos' in inspect.signature(info.classe).parameters]
    assert com_grupos == []


@pytest.mark.parametrize('nome', GRUPOS_DA_ARMA)
def test_grupo_da_arma_nao_pode_ser_trocado(novo_jogo, nome):
    rifle = novo_jogo.player.armas['assault_rifle']
    with pytest.raises(AttributeError):
        setattr(rifle, nome, pygame.sprite.Group())
    assert getattr(rifle, nome) is getattr(entity_manager, nome)


class _RajadaFalsa(ArmaDeRajada):
    """Rajada com stats fixos que só anota os tiros (sem projétil)."""
    def __init__(self, jogador):
        super().__init__(jogador=jogador)
        self.cooldown, self.burst_count, self.burst_interval, self.raio_maximo = 1000, 3, 100, 500
        self.tiros = []

    def atirar(self, alvo):
        self.tiros.append((relogio.agora(), alvo))


def _rodar(arma, segundos):
    for _ in range(round(segundos * 60)):
        relogio.avancar(1 / 60)
        arma.update(1 / 60)


def test_rajada_dispara_burst_count_tiros_espacados(novo_jogo):
    arma = _RajadaFalsa(novo_jogo.player)
    grunt, = _grunts(novo_jogo, 200)
    _rodar(arma, 0.9)                       # 1 ativação (cooldown de 1 s)
    assert [alvo for _, alvo in arma.tiros] == [grunt] * 3
    instantes = [t for t, _ in arma.tiros]
    assert all(b - a > arma.burst_interval for a, b in zip(instantes, instantes[1:]))
    assert arma.tiros_restantes == 0

    _rodar(arma, 0.5)                       # a ativação seguinte só vem depois do cooldown (1 s)
    assert len(arma.tiros) == 6


def test_rajada_em_andamento_nao_reinicia(novo_jogo):
    arma = _RajadaFalsa(novo_jogo.player)
    _grunts(novo_jogo, 200)
    assert arma.disparar() and arma.tiros_restantes == 3
    assert not arma.disparar()              # no meio da rajada, disparar não recarrega os tiros
    assert arma.tiros_restantes == 3


def test_rajada_para_quando_o_alvo_some(novo_jogo):
    arma = _RajadaFalsa(novo_jogo.player)
    grunt, = _grunts(novo_jogo, 200)
    _rodar(arma, 0.05)
    assert len(arma.tiros) == 1 and arma.tiros_restantes == 2
    grunt.kill()
    _rodar(arma, 0.5)
    assert len(arma.tiros) == 1 and arma.tiros_restantes == 0


def test_rajada_sem_alvo_no_alcance_nao_atira(novo_jogo):
    arma = _RajadaFalsa(novo_jogo.player)
    _grunts(novo_jogo, 600)                 # fora do raio_maximo (500)
    _rodar(arma, 1.0)
    assert arma.tiros == [] and arma.ultimo_tiro == 0


def test_light_rifle_mira_no_mais_forte(novo_jogo):
    """Única rajada que troca a busca: o mais forte no alcance, não o mais próximo."""
    novo_jogo.event_manager._aplicar_escolha_de_upgrade('light_rifle')
    arma = novo_jogo.player.armas['light_rifle']
    fraco, forte = _grunts(novo_jogo, 100, 400)
    fraco.vida, forte.vida = 10, 500
    assert arma.buscar_alvo() is forte


@pytest.mark.parametrize('id_arma', ['dizimator', 'needler', 'carabin', 'light_rifle', 'machine_gun'])
def test_rajada_real_cria_um_projetil_por_tiro(novo_jogo, id_arma):
    novo_jogo.player.armas.pop('assault_rifle').ultimo_tiro = float('inf')
    novo_jogo.event_manager._aplicar_escolha_de_upgrade(id_arma)
    arma = novo_jogo.player.armas[id_arma]
    assert isinstance(arma, ArmaDeRajada)
    grunt, = _grunts(novo_jogo, 150)
    grunt.vida = grunt.escudo_atual = 10 ** 9
    antes = set(entity_manager.projeteis_jogador_grupo)
    assert arma.disparar()
    for _ in range(arma.burst_count * (arma.burst_interval // 16 + 2)):
        relogio.avancar(1 / 60)
        ArmaDeRajada.update(arma, 1 / 60)   # sem o cooldown da base disparar outra ativação
        if arma.tiros_restantes == 0:
            break
    novos = [p for p in entity_manager.projeteis_jogador_grupo if p not in antes]
    assert len(novos) == arma.burst_count

