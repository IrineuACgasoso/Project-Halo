"""Animador dos bosses (roteiro F2): clips declarativos, hit frames, cópias por instância feitas
no spawn e máscaras do cache. A equivalência com a animação antiga do Arbiter (quadro, lado e
alpha a cada 0,5 s) fica em integration/test_golden_arbiter.py."""
import pygame
import pytest

from helpers import DT
from source.enemies.base.boss import Animador, BossBase, Clip
from source.systems.gameclock import relogio

V = pygame.math.Vector2
CORES = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]


def _quadros(n=4):
    """Quadros distinguíveis pela cor; o lado esquerdo é outra lista (como no cache de sprites)."""
    direita = []
    for cor in CORES[:n]:
        s = pygame.Surface((8, 8), pygame.SRCALPHA)
        s.fill((*cor, 255))
        direita.append(s)
    esquerda = [pygame.transform.flip(s, True, False) for s in direita]
    return {'left': esquerda, 'right': direita}


def _animador(clips=None, inicial='a', lado='right', agora=0, sprites=None):
    clips = clips if clips is not None else {'a': Clip(100)}
    return Animador(sprites or _quadros(), clips, inicial, lado, agora)


def _ate(animador, inicio, fim, passo=1):
    """Atualiza de `inicio` a `fim` ms (inclusive); devolve [(agora, quadro, evento)] das mudanças."""
    vistos = []
    anterior = (animador.clip, animador.passo)
    for agora in range(inicio, fim + 1, passo):
        animador.atualizar(agora)
        if (animador.clip, animador.passo) != anterior or animador.evento:
            vistos.append((agora, animador.quadro, animador.evento))
            anterior = (animador.clip, animador.passo)
    return vistos


# ------------------------------------------------------------------ #
def test_loop_avanca_so_depois_de_passar_o_tempo_e_volta_ao_inicio():
    a = _animador()
    a.atualizar(100)
    assert a.quadro == 0                      # exatamente 100 ms: ainda não (regra antiga: >)
    assert _ate(a, 101, 500) == [(101, 1, None), (202, 2, None), (303, 3, None), (404, 0, None)]


def test_sem_loop_para_no_ultimo_quadro():
    a = _animador({'a': Clip(100, quadros=(0, 1, 2), loop=False)})
    assert _ate(a, 1, 202) == [(101, 1, None), (202, 2, None)]
    assert not a.terminou                     # o último quadro também fica o tempo dele
    _ate(a, 203, 303)
    assert a.terminou and a.quadro == 2
    _ate(a, 304, 1000)
    assert a.terminou and a.quadro == 2


def test_sair_de_um_clip_terminado_volta_a_animar():
    """Golpe sem loop com os mesmos quadros do andar: o fim dele não congela o andar."""
    a = _animador({'andar': Clip(100), 'golpe': Clip(50, loop=False)}, inicial='golpe')
    _ate(a, 1, 220)                           # quadro 3 entrou em 153; terminou em 204
    assert a.terminou and a.quadro == 3
    a.tocar('andar')
    a.atualizar(230)
    assert (a.clip, a.terminou, a.quadro) == ('andar', False, 3)
    a.atualizar(254)                          # 101 ms desde a entrada do 3, no ritmo do andar
    assert a.quadro == 0


# ------------------------------------------------------------------ #
def test_evento_dispara_uma_vez_ao_entrar_no_quadro():
    a = _animador({'a': Clip(100, quadros=(0, 1, 2), eventos={1: 'impacto'})})
    vistos = _ate(a, 1, 700)
    assert [(t, e) for t, _, e in vistos if e] == [(101, 'impacto'), (404, 'impacto')]


# ------------------------------------------------------------------ #
class BossAnimado(BossBase):
    """Parado; a rotina 'golpe' toca um clip sem loop e marca o hit frame."""
    COOLDOWNS = {'golpe': (100000, 100000)}
    COOLDOWN_INICIAL = {'golpe': 0}
    ESTADOS = {**BossBase.ESTADOS, 'golpe': 'golpeando'}
    CLIPS = {'andar': Clip(200), 'golpe': Clip(100, quadros=(0, 1, 2, 3), loop=False, eventos={2: 'impacto'}),
             'gira': Clip(100)}
    CLIP_INICIAL = 'andar'

    def __init__(self, posicao, game, golpe='golpe', evento='impacto', limite_ms=5000):
        super().__init__(posicao, vida_base=1000, dano_base=10, velocidade_base=0, game=game,
                         sprite_key='arbiter', flip_sprite=True)
        self.golpe, self.evento_esperado, self.limite_ms = golpe, evento, limite_ms
        self.registro = []
        self.ligado = False

    def escolher_habilidade(self, agora):
        return 'golpe' if self.ligado and self.pronto('golpe') else None

    def rotina_golpe(self):
        self.registro.append(('inicio', self._agora))
        chegou = yield from self._tocar(self.golpe, self.evento_esperado, self.limite_ms)
        self.registro.append(('hit' if chegou else 'desistiu', self._agora, self.animador.quadro))
        self.agendar('golpe')


@pytest.fixture
def boss(novo_jogo):
    b = BossAnimado(novo_jogo.player.posicao + V(400, 0), novo_jogo)
    b.invencivel = False
    return b


FRAME_MS = DT * 1000
# a troca acontece no 1º frame com MAIS de 100 ms desde a anterior: 7 frames (116,7 ms) a 60 FPS
QUADRO_100_MS = 7 * FRAME_MS


def _passar(boss, ms):
    for _ in range(round(ms / (DT * 1000))):
        relogio.avancar(DT)
        boss.update(DT)


def test_alpha_de_um_boss_nao_vaza_para_outro(boss, novo_jogo):
    outro = BossAnimado(novo_jogo.player.posicao + V(-400, 0), novo_jogo)
    boss._aplicar_alpha(0)                     # camuflado
    _passar(boss, 450)                         # troca de quadro: o alpha vai junto
    assert boss.image.get_alpha() == 0
    assert all(imagem.get_alpha() == 255 for imagem in outro.animador.imagens)
    assert outro.image.get_alpha() == 255


def test_rotina_espera_o_hit_frame(boss):
    boss.ligado = True
    _passar(boss, DT * 1000)
    (_, inicio), = boss.registro
    _passar(boss, 400)
    _, (marca, quando, quadro) = boss.registro
    assert marca == 'hit' and quadro == 2
    # o passo 0 entra no frame do início, o 2 duas trocas depois; a rotina vê o evento 1 frame após
    assert quando - inicio == pytest.approx(2 * QUADRO_100_MS + FRAME_MS, abs=2)
    assert boss.estado_habilidade == 'idle'


def test_evento_que_nunca_vem_desiste_no_limite(novo_jogo):
    boss = BossAnimado(novo_jogo.player.posicao + V(400, 0), novo_jogo, golpe='gira', limite_ms=300)
    boss.ligado = True
    _passar(boss, 1000)
    (_, inicio), (marca, quando, _) = boss.registro
    assert marca == 'desistiu'
    assert quando - inicio == pytest.approx(300, abs=FRAME_MS + 2)
