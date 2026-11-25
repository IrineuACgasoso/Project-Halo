"""Arbiter reformulado: escudo e combo da quebra, postura sem escudo, costas expostas depois da
investida, esquiva, anti-stuck por salto, fase 2 e o que corre fora da rotina."""
from types import SimpleNamespace

import pygame
import pytest

from helpers import DT, blindar_jogador
from source.enemies.bosses.arbiter.config import CFG
from source.feats.skills.purge_grid import PurgeGrid
from source.systems.dano import PROJETIL, Dano
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.systems.mapmanager.grade_paredes import GradeParedes

V = pygame.math.Vector2
CENTRO = V(1500, 1500)


@pytest.fixture
def arbiter(novo_jogo):
    novo_jogo.spawner.spawnar('arbiter')
    b = novo_jogo.sessao.boss_atual
    b.posicao.update(CENTRO)
    b.sync_rect()
    b.invencivel = False
    b.travamento = None               # sem anti-stuck: cada teste o chama quando quer
    b.verificar_posicao_valida = lambda p: True
    blindar_jogador(novo_jogo.player)
    _jogador_em(b, V(400, 0))
    _sem_ia(b)
    return b


def _jogador_em(b, deslocamento):
    b.jogador.posicao.update(b.posicao + deslocamento)


def _sem_ia(b):
    """Só o que o teste iniciar: nada é escolhido nem corre fora da rotina."""
    b.cd = {nome: float('inf') for nome in b.cd}
    b.cd_fora = {nome: float('inf') for nome in b.cd_fora}
    b.cd_fora = {nome: float('inf') for nome in b.cd_fora}


def _passo(b, paredes=None):
    relogio.avancar(DT)
    b.update(DT, paredes)


def _ate(b, condicao, limite_s=15, paredes=None):
    for _ in range(round(limite_s / DT)):
        if condicao():
            return
        _passo(b, paredes)
    raise AssertionError('não aconteceu')


def _ferir(b, valor):
    b.receber_dano(Dano(valor, PROJETIL))


def test_quebra_do_escudo_vira_combo_mesmo_exausto_e_o_escudo_volta_sozinho(arbiter):
    b = arbiter
    b.cd['combo'] = 0
    b.wait = 10_000
    _ferir(b, b.escudo_maximo + 10)
    assert b.sem_escudo and b.escudo_atual == 0
    _passo(b)
    assert b.ultima_habilidade == 'combo' and b.rotina is not None
    _ate(b, lambda: b.rotina is None)
    assert not b.is_inofensivo and b.status.mult_velocidade > 1        # Fúria Honorável ainda ativa
    _ate(b, lambda: b.status.mult_velocidade == 1, limite_s=CFG.furia_ms / 1000 + 1)
    _ate(b, lambda: b.escudo_atual >= b.escudo_maximo,
         limite_s=(CFG.escudo_atraso_ms + CFG.escudo_regen_ms) / 1000 + 1)
    _passo(b)
    assert not b.sem_escudo and b.postura == 'neutra'


@pytest.mark.parametrize('razao_vida, dist, vida_jogador, fase, escolta, esperada', [
    (1.0, 200, 1.0, 1, 0, 'avanco'),    # recém-quebrado, inteiro e colado: segue no ataque
    (1.0, 200, 1.0, 1, 2, 'recuo'),     # ...mas com a escolta de Elites viva, recua para trás dela
    (0.45, 700, 1.0, 1, 0, 'recuo'),    # ferido e o jogador fugiu: recua para o escudo voltar
    (0.45, 700, 0.1, 1, 0, 'avanco'),   # ...mas o jogador está quase morto: vai para cima
    (0.30, 500, 1.0, 1, 0, 'recuo'),
    (0.30, 500, 1.0, 2, 0, 'avanco'),   # fase 2 recua menos
])
def test_postura_sem_escudo(arbiter, razao_vida, dist, vida_jogador, fase, escolta, esperada):
    b = arbiter
    b.sem_escudo, b.postura, b._furia_ate = True, 'neutra', None
    b.elites_invocados = [SimpleNamespace(alive=lambda: True)] * escolta
    b.fase, b.fase_cfg = fase, b.FASES[fase - 1]
    b.contexto.razao_vida, b.contexto.dist_sq = razao_vida, dist ** 2
    b.jogador.vida_atual = b.jogador.vida_maxima * vida_jogador
    b._avaliar_postura(b._agora)
    assert b.postura == esperada


def test_investida_atordoa_e_expoe_so_as_costas(arbiter):
    b = arbiter
    b.adicionar_escudo(0)
    b.iniciar('investida')
    _ate(b, lambda: b.costas_expostas)
    costas = b._costas[0]
    assert costas.x == pytest.approx(-1) and b.is_inofensivo        # investiu para +x

    _jogador_em(b, costas * 150)
    vida = b.vida
    _ferir(b, 100)
    assert vida - b.vida == pytest.approx(100 * CFG.costas_mult)
    _jogador_em(b, -costas * 150)
    vida = b.vida
    _ferir(b, 100)
    assert vida - b.vida == pytest.approx(100)

    _ate(b, lambda: b.rotina is None)
    assert not b.costas_expostas and not b.is_inofensivo


def test_muito_dano_em_pouco_tempo_vira_esquiva_de_lado(arbiter, monkeypatch):
    b = arbiter
    monkeypatch.setattr('source.enemies.bosses.arbiter.attacks.random.random', lambda: 1.0)   # sem spray
    b.cd['esquiva'] = 0
    b.wait = 10_000
    inicio = V(b.posicao)
    _ferir(b, 1.5 * CFG.esquiva_limiar * (b.vida_maxima + b.escudo_maximo))
    _passo(b)
    assert b.ultima_habilidade == 'esquiva'
    _ate(b, lambda: b.rotina is None)
    desvio = b.posicao - inicio
    assert desvio.length() > 150 and abs(desvio.normalize().dot(V(1, 0))) < 0.2   # perpendicular


def test_anti_stuck_salta_por_cima_da_parede_sem_poder_ser_mirado(arbiter):
    b = arbiter
    _jogador_em(b, V(500, 0))
    paredes = GradeParedes([{'tipo': 'linha', 'pontos': [V(1650, 1200), V(1650, 1800)]}])
    b.iniciar('antistuck')
    _ate(b, lambda: b.no_ar, paredes=paredes)
    assert not b.alvejavel and b.invulneravel
    _ate(b, lambda: b.rotina is None, paredes=paredes)
    assert b.posicao.x > 1650 and b.alvejavel


def test_fase_2_descarta_carabina_e_invocacao_e_o_bombardeio_nao_para_a_rotina(arbiter):
    b = arbiter
    b.vida = b.vida_maxima * 0.3
    _passo(b)
    assert b.fase == 2
    assert b.pontuar_carabina(b.contexto) == 0
    b.cd_fora['invocacao'] = 0
    b.iniciar('granada')
    rotina = b.rotina
    b.cd_fora['bombardeio'] = 0
    _passo(b)
    assert b.rotina is rotina and b.elites_invocados == []
    bombardeios = [s for s in entity_manager.all_sprites if isinstance(s, PurgeGrid)]
    assert len(bombardeios) == 1
    pontos = [p for _, p in bombardeios[0].fila_spawn]
    meio = sum(pontos, V()) / len(pontos)
    assert meio.distance_to(b.jogador.posicao) < 1                   # linha centrada no jogador


def test_invocacao_respeita_o_teto_de_elites(arbiter):
    b = arbiter
    b.cd_fora['invocacao'] = 0
    for _ in range(4):
        b._fora_da_rotina()
        b.cd_fora['invocacao'] = 0
    assert len(b.elites_invocados) == CFG.max_elites
