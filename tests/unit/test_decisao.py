"""IA de utilidade e memória adaptativa (roteiro F3): dado o contexto X, o Arbiter escolhe Y; o dano
volta para a habilidade que o gerou; a memória vale por luta."""
import pygame
import pytest

from helpers import DT
from source.enemies.base.boss import Habilidade, MemoriaDeCombate
from source.enemies.base.boss.decisao import EXIGENCIA, FATOR_MEMORIA, PACIENCIA_MS, Decisor
from source.systems.dano import AREA, Dano
from source.systems.eventos import DANO_CAUSADO, eventos

V = pygame.math.Vector2


@pytest.fixture
def arbiter(novo_jogo):
    novo_jogo.spawner.spawnar('arbiter')
    boss = novo_jogo.sessao.boss_atual
    boss.contexto.atualizar(boss, 0)
    return boss


def _prontas(boss, *nomes):
    boss.cd = {nome: (0 if nome in nomes else boss._agora + 10**9) for nome in boss.COOLDOWNS}


@pytest.mark.parametrize('dist, prontas, contexto, esperada', [
    (100, ('lamina', 'granada', 'carabina'), {}, 'lamina'),                       # colado: espada
    (500, ('lamina', 'granada', 'carabina'), {'parado_ms': 3000}, 'granada'),     # acampando
    (500, ('lamina', 'granada', 'carabina'), {'afastamento': 250}, 'carabina'),   # fugindo
    (720, ('lamina', 'granada', 'carabina'), {}, 'carabina'),                     # fora da granada
    (950, ('lamina', 'granada', 'carabina'), {}, None),                           # nada alcança
])
def test_arbiter_contexto_decide_a_habilidade(arbiter, monkeypatch, dist, prontas, contexto, esperada):
    # sem sorteio: entre finalistas ganha a maior nota
    monkeypatch.setattr('source.enemies.base.boss.decisao.random.choices',
                        lambda nomes, weights: [max(zip(weights, nomes))[1]])
    _prontas(arbiter, *prontas)
    arbiter.contexto.dist_sq = dist ** 2
    for campo, valor in contexto.items():
        setattr(arbiter.contexto, campo, valor)
    assert arbiter.decisor.escolher(arbiter, arbiter._agora) == esperada


@pytest.mark.parametrize('vida_jogador, esperada', [(1.0, 'carabina'), (0.1, 'investida')])
def test_arbiter_vai_para_cima_de_quem_esta_fraco(arbiter, monkeypatch, vida_jogador, esperada):
    monkeypatch.setattr('source.enemies.base.boss.decisao.random.choices',
                        lambda nomes, weights: [max(zip(weights, nomes))[1]])
    _prontas(arbiter, 'investida', 'carabina')
    arbiter.contexto.dist_sq = 500 ** 2
    arbiter.jogador.vida_atual = arbiter.jogador.vida_maxima * vida_jogador
    assert arbiter.decisor.escolher(arbiter, arbiter._agora) == esperada


def test_nota_fraca_espera_ate_a_paciencia_acabar(arbiter):
    decisor = Decisor({'carabina': Habilidade(peso=EXIGENCIA / 10)})
    _prontas(arbiter, 'carabina')
    assert decisor.escolher(arbiter, 1000) is None
    assert decisor.escolher(arbiter, 1000 + PACIENCIA_MS) == 'carabina'


def test_memoria_favorece_o_que_acerta_e_se_recupera():
    m = MemoriaDeCombate(['tiro', 'golpe'])
    assert m.fator('tiro') == m.fator('golpe') == m.fator('desconhecida') == 1.0
    for _ in range(4):
        m.registrar_uso('tiro')
        m.registrar_uso('golpe')
        m.registrar_dano('golpe', 100)
    assert FATOR_MEMORIA[0] <= m.fator('tiro') < 1.0 < m.fator('golpe') <= FATOR_MEMORIA[1]
    for _ in range(8):       # o jogador aprendeu a desviar do golpe e passou a levar os tiros
        m.registrar_uso('golpe')
        m.registrar_uso('tiro')
        m.registrar_dano('tiro', 100)
    assert m.fator('golpe') < 1.0 < m.fator('tiro')
    m.registrar_dano('golpe', float('inf'))      # golpe letal não pode envenenar as contas
    assert m.fator('golpe') < 1.0


@pytest.mark.parametrize('nome', ['carabina', 'granada', 'lamina'])
def test_dano_volta_para_a_habilidade_que_o_gerou(arbiter, nome):
    """Mesmo quando acerta depois de a rotina acabar (tiro em voo, granada que explode no chão)."""
    jogador = arbiter.jogador
    jogador.vida_maxima = jogador.vida_atual = 10 ** 6
    arbiter.posicao = jogador.posicao + V(200, 0)
    arbiter.rect.center = arbiter.hitbox.center = arbiter.posicao
    arbiter.iniciar(nome)
    if nome == 'carabina':
        arbiter.atirar_carabina(direcao=V(-1, 0))
    elif nome == 'granada':
        arbiter._lancar_granada(V(jogador.posicao))
    else:
        arbiter._lancar_cone('arbiter_energy_sword', V(-1, 0))
    arbiter.interromper_rotina()
    assert arbiter.habilidade_ativa is None
    ataques = [s for s in arbiter.game.player.groups()[0].sprites() if getattr(s, 'fonte', None) is arbiter]
    assert [a.habilidade for a in ataques] == [nome]

    game = arbiter.game
    arbiter.wait = 10 ** 9       # não decide mais nada
    arbiter.travamento = None
    for _ in range(round(5 / DT)):
        game.update(DT)
        jogador.vida_atual = jogador.vida_maxima
        if arbiter.decisor.memoria.dano[nome] > 0:
            break
    memoria = arbiter.decisor.memoria
    assert memoria.dano[nome] > 0
    assert all(d == 0 for n, d in memoria.dano.items() if n != nome)


def test_memoria_vale_por_luta_e_solta_o_barramento(novo_jogo, arbiter):
    golpe = Dano(50, AREA, arbiter, habilidade='lamina')
    eventos.emitir(DANO_CAUSADO, alvo=arbiter.jogador, dano=golpe, valor=50)
    eventos.emitir(DANO_CAUSADO, alvo=object(), dano=golpe, valor=50)      # outro alvo: não conta
    assert arbiter.decisor.memoria.dano['lamina'] == 50
    arbiter.kill()
    eventos.emitir(DANO_CAUSADO, alvo=arbiter.jogador, dano=golpe, valor=50)
    assert arbiter.decisor.memoria.dano['lamina'] == 50
    novo_jogo.spawner.spawnar('arbiter')
    assert set(novo_jogo.sessao.boss_atual.decisor.memoria.dano.values()) == {0.0}
