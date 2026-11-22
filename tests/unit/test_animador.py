"""Animador dos bosses (roteiro F2): clips declarativos, hit frames, cópias por instância feitas
no spawn e máscaras do cache. A equivalência com a animação antiga do Arbiter (quadro, lado e
alpha a cada 0,5 s) fica em integration/test_golden_arbiter.py."""
import pygame
import pytest

from helpers import DT, blindar_jogador, ir_para_fase
from source.enemies.base.boss import Animador, BossBase, Clip
from source.systems.gameclock import relogio
from source.utils.superficies import mascara_de

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
# Clip
# ------------------------------------------------------------------ #
def test_clip_valido_e_eventos_imutaveis():
    clip = Clip(120, quadros=(2, 0), loop=False, eventos={1: 'impacto'})
    assert (clip.ms_por_quadro, clip.quadros, clip.loop, dict(clip.eventos)) == (120, (2, 0), False, {1: 'impacto'})
    with pytest.raises(TypeError):
        clip.eventos[0] = 'outro'


@pytest.mark.parametrize('kwargs, trecho', [
    ({'ms_por_quadro': 0}, 'ms_por_quadro 0'),
    ({'ms_por_quadro': -5}, 'ms_por_quadro -5'),
    ({'ms_por_quadro': 1.5}, 'ms_por_quadro 1.5'),
    ({'ms_por_quadro': True}, 'ms_por_quadro True'),
    ({'ms_por_quadro': 100, 'quadros': ()}, 'quadros ()'),
    ({'ms_por_quadro': 100, 'quadros': [0, 1]}, 'quadros [0, 1]'),
    ({'ms_por_quadro': 100, 'quadros': (0, -1)}, 'quadros (0, -1)'),
    ({'ms_por_quadro': 100, 'quadros': (0, True)}, 'quadros (0, True)'),
    ({'ms_por_quadro': 100, 'loop': 1}, 'loop 1'),
    ({'ms_por_quadro': 100, 'eventos': [(0, 'x')]}, 'eventos'),
    ({'ms_por_quadro': 100, 'eventos': {-1: 'x'}}, 'passo de evento -1'),
    ({'ms_por_quadro': 100, 'quadros': (0, 1), 'eventos': {2: 'x'}}, 'evento no passo 2'),
    ({'ms_por_quadro': 100, 'eventos': {0: ''}}, 'nome de evento'),
])
def test_clip_invalido(kwargs, trecho):
    with pytest.raises(ValueError, match=trecho.replace('(', r'\(').replace(')', r'\)').replace('[', r'\[')):
        Clip(**kwargs)


# ------------------------------------------------------------------ #
# Animador: criação
# ------------------------------------------------------------------ #
def test_quadros_sao_copias_proprias_com_a_mascara_do_original():
    sprites = _quadros()
    a = _animador(sprites=sprites)
    for lado in ('left', 'right'):
        a.virar(-1 if lado == 'left' else 1)
        for i, original in enumerate(sprites[lado]):
            a.passo = i
            assert a.imagem is not original
            assert a.imagem.get_at((1, 1)) == original.get_at((1, 1))
            assert a.mascara is mascara_de(original)
    assert len(a.imagens) == 8 and len({id(s) for s in a.imagens}) == 8


def test_dois_animadores_nao_dividem_imagem():
    sprites = _quadros()
    a, b = _animador(sprites=sprites), _animador(sprites=sprites)
    a.imagem.set_alpha(0)
    assert b.imagem.get_alpha() == 255


@pytest.mark.parametrize('sprites, clips, inicial, lado, trecho', [
    ({'right': [pygame.Surface((2, 2))]}, None, 'a', 'right', 'precisa ter os lados'),
    ({'left': [], 'right': []}, None, 'a', 'right', 'mesmo número'),
    ({'left': [pygame.Surface((2, 2))], 'right': []}, None, 'a', 'right', 'mesmo número'),
    (None, {}, 'a', 'right', 'nenhum clip'),
    (None, {'a': 100}, 'a', 'right', 'não é um Clip'),
    (None, {'a': Clip(100, quadros=(0, 4))}, 'a', 'right', r'usa os quadros \[4\], mas o sprite tem 4'),
    (None, {'a': Clip(100, eventos={4: 'x'})}, 'a', 'right', 'evento além dos 4 quadros'),
    (None, None, 'a', 'cima', "lado 'cima'"),
])
def test_animador_invalido(sprites, clips, inicial, lado, trecho):
    with pytest.raises(ValueError, match=trecho):
        _animador(clips=clips, inicial=inicial, lado=lado, sprites=sprites)


def test_clip_inexistente_e_erro():
    with pytest.raises(KeyError, match='"b" não existe'):
        _animador(inicial='b')
    a = _animador()
    with pytest.raises(KeyError, match='"correr" não existe'):
        a.tocar('correr')


# ------------------------------------------------------------------ #
# Tempo
# ------------------------------------------------------------------ #
def test_loop_avanca_so_depois_de_passar_o_tempo_e_volta_ao_inicio():
    a = _animador()
    a.atualizar(100)
    assert a.quadro == 0                      # exatamente 100 ms: ainda não (regra antiga: >)
    assert _ate(a, 101, 500) == [(101, 1, None), (202, 2, None), (303, 3, None), (404, 0, None)]


def test_clip_com_quadros_escolhidos():
    a = _animador({'a': Clip(50, quadros=(3, 1))})
    assert a.quadro == 3
    assert [q for _, q, _ in _ate(a, 1, 200)] == [1, 3, 1]


def test_sem_loop_para_no_ultimo_quadro():
    a = _animador({'a': Clip(100, quadros=(0, 1, 2), loop=False)})
    assert _ate(a, 1, 202) == [(101, 1, None), (202, 2, None)]
    assert not a.terminou                     # o último quadro também fica o tempo dele
    _ate(a, 203, 303)
    assert a.terminou and a.quadro == 2
    _ate(a, 304, 1000)
    assert a.terminou and a.quadro == 2


def test_mesma_sequencia_so_muda_o_ritmo():
    """andar -> investida não reinicia o ciclo (é o que o Arbiter fazia com velocidade_animacao)."""
    a = _animador({'andar': Clip(200), 'investida': Clip(80)}, inicial='andar')
    _ate(a, 1, 201)
    assert a.quadro == 1                      # trocou em 201
    a.tocar('investida')
    a.atualizar(250)
    assert (a.clip, a.quadro) == ('investida', 1)    # 49 ms desde a troca: mantém o passo
    a.atualizar(282)
    assert a.quadro == 2                      # 81 ms desde a troca de quadro, no ritmo novo


def test_sequencia_diferente_recomeca_do_primeiro():
    a = _animador({'a': Clip(100), 'b': Clip(100, quadros=(3, 2))})
    _ate(a, 1, 202)
    assert a.quadro == 2
    a.tocar('b')
    a.atualizar(230)
    assert (a.clip, a.passo, a.quadro) == ('b', 0, 3)
    a.atualizar(330)
    assert a.passo == 0                       # relógio recomeçou em 230
    a.atualizar(331)
    assert a.quadro == 2


def test_reiniciar_recomeca_o_mesmo_clip():
    a = _animador({'golpe': Clip(100, quadros=(0, 1), loop=False)}, inicial='golpe')
    _ate(a, 1, 300)
    assert a.terminou
    a.tocar('golpe')                          # sem reiniciar: continua parado no fim
    a.atualizar(301)
    assert a.terminou and a.passo == 1
    a.tocar('golpe', reiniciar=True)
    a.atualizar(302)
    assert (a.terminou, a.passo) == (False, 0)
    a.tocar('golpe')                          # o reiniciar vale uma vez só
    a.atualizar(350)
    assert a.passo == 0


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


def test_ultimo_pedido_ganha():
    a = _animador({'a': Clip(100), 'b': Clip(100, quadros=(2,)), 'c': Clip(100, quadros=(3,))})
    a.tocar('b')
    a.tocar('c')
    a.atualizar(1)
    assert (a.clip, a.quadro) == ('c', 3)


# ------------------------------------------------------------------ #
# Hit frames e lados
# ------------------------------------------------------------------ #
def test_evento_dispara_uma_vez_ao_entrar_no_quadro():
    a = _animador({'a': Clip(100, quadros=(0, 1, 2), eventos={1: 'impacto'})})
    vistos = _ate(a, 1, 700)
    assert [(t, e) for t, _, e in vistos if e] == [(101, 'impacto'), (404, 'impacto')]


def test_evento_no_primeiro_quadro_dispara_no_inicio():
    a = _animador({'a': Clip(100), 'golpe': Clip(100, quadros=(2, 3), eventos={0: 'saque'})})
    assert a.evento is None
    a.tocar('golpe')
    a.atualizar(10)
    assert a.evento == 'saque'
    a.atualizar(11)
    assert a.evento is None
    b = _animador({'golpe': Clip(100, eventos={0: 'saque'})}, inicial='golpe')
    assert b.evento == 'saque'               # o clip inicial também


def test_virar_troca_o_lado_e_mantem_o_quadro():
    sprites = _quadros()
    a = _animador(sprites=sprites)
    _ate(a, 1, 101)
    a.virar(-3)
    assert (a.lado, a.quadro) == ('left', 1)
    assert a.imagem.get_at((1, 1)) == sprites['left'][1].get_at((1, 1))
    a.virar(0)
    assert a.lado == 'left'
    a.virar(0.5)
    assert a.lado == 'right'


# ------------------------------------------------------------------ #
# BossBase
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


def test_boss_nasce_mostrando_o_animador(boss):
    assert boss.image is boss.animador.imagem and boss.mask is boss.animador.mascara
    assert (boss.animador.clip, boss.animador.lado, boss.animador.quadro) == ('andar', 'right', 0)


def test_boss_padrao_tem_um_clip_em_loop():
    assert BossBase.CLIP_INICIAL in BossBase.CLIPS and BossBase.CLIPS[BossBase.CLIP_INICIAL].loop


def test_alpha_segue_de_um_quadro_ao_outro(boss):
    boss._aplicar_alpha(90)
    imagem_antes = boss.image
    _passar(boss, 450)
    assert boss.image is not imagem_antes
    assert boss.image.get_alpha() == 90


def test_alpha_de_um_boss_nao_vaza_para_outro(boss, novo_jogo):
    outro = BossAnimado(novo_jogo.player.posicao + V(-400, 0), novo_jogo)
    boss._aplicar_alpha(0)                     # camuflado
    _passar(boss, 450)                         # troca de quadro: o alpha vai junto
    assert boss.image.get_alpha() == 0
    assert all(imagem.get_alpha() == 255 for imagem in outro.animador.imagens)
    assert outro.image.get_alpha() == 255


def test_boss_vira_para_o_jogador_no_fim_do_frame(boss, novo_jogo):
    boss.posicao = novo_jogo.player.posicao + V(400, 0)   # jogador à esquerda
    _passar(boss, DT * 1000)
    assert boss.animador.lado == 'left'
    assert boss.image is boss.animador.imagem


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


def test_sem_evento_espera_o_clip_terminar(novo_jogo):
    boss = BossAnimado(novo_jogo.player.posicao + V(400, 0), novo_jogo, evento=None)
    boss.ligado = True
    _passar(boss, 1000)
    (_, inicio), (marca, quando, quadro) = boss.registro
    assert marca == 'hit' and quadro == 3
    assert quando - inicio == pytest.approx(4 * QUADRO_100_MS + FRAME_MS, abs=2)   # o 3 também dura o tempo dele


def test_evento_que_nunca_vem_desiste_no_limite(novo_jogo):
    boss = BossAnimado(novo_jogo.player.posicao + V(400, 0), novo_jogo, golpe='gira', limite_ms=300)
    boss.ligado = True
    _passar(boss, 1000)
    (_, inicio), (marca, quando, _) = boss.registro
    assert marca == 'desistiu'
    assert quando - inicio == pytest.approx(300, abs=FRAME_MS + 2)


@pytest.mark.integration
def test_luta_do_arbiter_so_usa_imagens_do_spawn(novo_jogo):
    """Zero alocação de imagem no update do boss: a catraca não vê `Surface.copy` (método em C),
    então aqui toda imagem e máscara mostradas precisam ser as preparadas no spawn."""
    blindar_jogador(novo_jogo.player)
    ir_para_fase(novo_jogo, 4)
    novo_jogo.spawner.spawnar('arbiter')
    boss = novo_jogo.sessao.boss_atual
    boss.invencivel = False
    imagens = {id(s) for s in boss.animador.imagens}
    mascaras = {id(mascara_de(s)) for lado in ('left', 'right') for s in boss.sprites[lado]}
    vistas = set()
    for _ in range(round(20 / DT)):                       # passa pela camuflagem e por várias habilidades
        novo_jogo.update(DT)
        assert id(boss.image) in imagens and id(boss.mask) in mascaras
        vistas.add((boss.animador.lado, boss.animador.quadro, boss.animador.clip))
    assert len({(lado, quadro) for lado, quadro, _ in vistas}) >= 6
    assert {'andar', 'parado'} <= {clip for _, _, clip in vistas}
