"""Registro de armas, sorteio da tela de upgrade e regras de upgrade (integridade dos dados: test_validacao.py)."""
import random
from collections import Counter
from types import SimpleNamespace

import pygame
import pytest

from source.data.weapon_data import WEAPON_DATA
from source.enemies.standard.grunt import GruntRed
from source.feats.skills.invisibilidade import OCULTO
from source.feats.weapons.baseweapon import Arma, ArmaDeRajada
from source.systems.gameclock import relogio
from source.systems.levelup import (ARMAS_REGISTRO, MAX_ARMAS, PESO_SORTEIO_POR_RARIDADE, TelaDeUpgrade, gerar_opcoes,
                                   sortear_armas_novas)

IDS = sorted(ARMAS_REGISTRO)


# Integridade do registro e de weapon_data: `validar_armas` (test_validacao.py, roteiro D5).


# ── WeaponStats / _deve_melhorar ─────────────────────────────────────────────


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


def test_arma_no_maximo_sai_do_sorteio_de_upgrade(novo_jogo):
    p = novo_jogo.player
    p.armas['assault_rifle'] = _criar_no_maximo(novo_jogo, 'assault_rifle')
    p.armas['brick'] = ARMAS_REGISTRO['brick'].criar(p, novo_jogo)
    for semente in range(50):
        ids = gerar_opcoes(p, random.Random(semente))
        assert 'assault_rifle' not in ids and len(ids) == 3 and len(set(ids)) == 3


def test_tudo_no_maximo_e_arsenal_cheio_nao_ha_opcao(novo_jogo):
    p = novo_jogo.player
    p.armas.clear()
    for id_arma in IDS[:MAX_ARMAS]:
        p.armas[id_arma] = _criar_no_maximo(novo_jogo, id_arma)
    assert gerar_opcoes(p) == []
    with pytest.raises(ValueError, match='sem opções'):
        TelaDeUpgrade(novo_jogo.tela, p, novo_jogo, ids_das_opcoes=[])


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


def _camuflar(inimigo, fase):
    inimigo.iniciar_invisibilidade('padrao')
    inimigo.invisibilidade.fase = fase


def test_invisivel_e_morto_nunca_sao_alvo(novo_jogo):
    invisivel, morto, longe = _grunts(novo_jogo, 50, 60, 400)
    _camuflar(invisivel, OCULTO)
    morto.vida = 0
    arma = _mira(novo_jogo)
    grupo = [invisivel, morto, longe]
    assert arma.encontrar_inimigo_mais_proximo(grupo) is longe
    longe.alpha_atual = 0
    assert arma.encontrar_inimigo_mais_proximo(grupo) is None
    assert arma.encontrar_inimigo_mais_forte(grupo) is None


# ── Grupos pelo nome e rajada (roteiro E4) ───────────────────────────────────


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


def test_rajada_para_quando_o_alvo_some(novo_jogo):
    arma = _RajadaFalsa(novo_jogo.player)
    grunt, = _grunts(novo_jogo, 200)
    _rodar(arma, 0.05)
    assert len(arma.tiros) == 1 and arma.tiros_restantes == 2
    grunt.kill()
    _rodar(arma, 0.5)
    assert len(arma.tiros) == 1 and arma.tiros_restantes == 0


def test_light_rifle_mira_no_mais_forte(novo_jogo):
    """Única rajada que troca a busca: o mais forte no alcance, não o mais próximo."""
    novo_jogo.event_manager._aplicar_escolha_de_upgrade('light_rifle')
    arma = novo_jogo.player.armas['light_rifle']
    fraco, forte = _grunts(novo_jogo, 100, 400)
    fraco.vida, forte.vida = 10, 500
    assert arma.buscar_alvo() is forte
