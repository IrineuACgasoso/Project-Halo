"""Broadphase de inimigos (roteiro C2): mesmo resultado da força bruta, na mesma ordem."""
import random

import pygame
import pytest

from helpers import DT, blindar_jogador, simular
from source.systems.collision import BroadphaseInimigos, CollisionManager
from source.systems.entitymanager import entity_manager


class _Sonda(pygame.sprite.Sprite):
    """Um 'projétil' qualquer: só rect (e hitbox opcional), como o custom_collision lê."""

    def __init__(self, rect, hitbox=None):
        super().__init__()
        self.rect = pygame.Rect(rect)
        if hitbox is not None:
            self.hitbox = pygame.Rect(hitbox)


def _forca_bruta(sprite):
    return pygame.sprite.spritecollide(sprite, entity_manager.inimigos_grupo, False,
                                       CollisionManager.custom_collision)


def _horda_mista(game, n=250):
    """Inimigos da fase 0 + os bosses com colisão especial: Scarab (círculo), Didact (hitbox)
    e Jega (collision_rect calculado)."""
    game.spawner.update = lambda dt: None
    for nome in ('scarab', 'didact', 'jega'):
        game.spawner.spawnar(nome)
    while len(entity_manager.inimigos_grupo) < n:
        game.spawner.spawnar('normal')


def _caixa_dos_inimigos():
    caixa = pygame.Rect(entity_manager.inimigos_grupo.sprites()[0].rect)
    return caixa.unionall([i.rect for i in entity_manager.inimigos_grupo])


def test_equivalencia_com_forca_bruta_em_sondas_aleatorias(novo_jogo):
    _horda_mista(novo_jogo)
    simular(novo_jogo, 0.5)   # os inimigos andam, animam e trocam de rect
    cm = novo_jogo.collision_manager
    cm.broadphase.reconstruir(entity_manager.inimigos_grupo)
    caixa = _caixa_dos_inimigos().inflate(200, 200)
    rng = random.Random(7)
    com_acerto = 0
    for _ in range(3000):
        w, h = rng.randint(1, 120), rng.randint(1, 120)
        rect = (rng.randint(caixa.left, caixa.right), rng.randint(caixa.top, caixa.bottom), w, h)
        sonda = _Sonda(rect, hitbox=(rect[0] + 2, rect[1] + 2, w, h) if rng.random() < 0.3 else None)
        esperado = _forca_bruta(sonda)
        assert cm.colidindo_com_inimigos(sonda) == esperado
        com_acerto += bool(esperado)
    assert com_acerto > 300, 'as sondas quase não acertaram: o teste não provaria nada'


def test_equivalencia_para_o_jogador(novo_jogo):
    _horda_mista(novo_jogo)
    cm = novo_jogo.collision_manager
    player = novo_jogo.player
    for inimigo in entity_manager.inimigos_grupo.sprites()[:40]:
        player.posicao.update(inimigo.rect.center)
        player.rect.center = player.hitbox.center = inimigo.rect.center
        cm.broadphase.reconstruir(entity_manager.inimigos_grupo)
        esperado = _forca_bruta(player)
        assert esperado, 'o jogador em cima do inimigo deveria colidir'
        assert cm.colidindo_com_inimigos(player) == esperado


def test_equivalencia_em_combate_quadro_a_quadro(novo_jogo, monkeypatch):
    """Simulação com armas de projétil: toda consulta do CollisionManager é conferida com a
    força bruta, no próprio frame."""
    blindar_jogador(novo_jogo.player)
    for arma in ('needler', 'carabin', 'shotgun', 'machine_gun'):
        while getattr(novo_jogo.player.armas.get(arma), 'nivel', 0) < 5:
            novo_jogo.event_manager._aplicar_escolha_de_upgrade(arma)
    _horda_mista(novo_jogo, n=120)
    cm = novo_jogo.collision_manager
    original = cm.colidindo_com_inimigos
    conferidas = []

    def conferir(sprite):
        resultado = original(sprite)
        assert resultado == _forca_bruta(sprite)
        conferidas.append(bool(resultado))
        return resultado

    monkeypatch.setattr(cm, 'colidindo_com_inimigos', conferir)
    simular(novo_jogo, 4)
    assert sum(conferidas) > 50, 'quase nenhum acerto: o teste não provaria nada'


def test_grupo_vazio_nao_tem_candidatos():
    bp = BroadphaseInimigos()
    grupo = pygame.sprite.Group()
    bp.reconstruir(grupo)
    assert bp.candidatos(pygame.Rect(0, 0, 10, 10), grupo) == []


def test_candidatos_na_ordem_do_grupo_e_so_os_que_tocam():
    grupo = pygame.sprite.Group()
    sprites = [_Sonda((x, 0, 10, 10)) for x in (50, 0, 25, 500)]
    grupo.add(*sprites)
    bp = BroadphaseInimigos()
    bp.reconstruir(grupo)
    assert bp.candidatos(pygame.Rect(0, 0, 60, 10), grupo) == sprites[:3]
    assert bp.candidatos(pygame.Rect(1000, 1000, 5, 5), grupo) == []


def test_inimigo_que_saiu_do_grupo_nao_e_candidato():
    grupo = pygame.sprite.Group()
    a, b = _Sonda((0, 0, 10, 10)), _Sonda((5, 5, 10, 10))
    grupo.add(a, b)
    bp = BroadphaseInimigos()
    bp.reconstruir(grupo)
    a.kill()
    assert bp.candidatos(pygame.Rect(0, 0, 20, 20), grupo) == [b]


def test_inimigo_circular_e_sempre_candidato():
    grupo = pygame.sprite.Group()
    circular = _Sonda((0, 0, 10, 10))
    circular.usar_circulo = True
    grupo.add(circular)
    bp = BroadphaseInimigos()
    bp.reconstruir(grupo)
    assert bp.candidatos(pygame.Rect(5000, 5000, 1, 1), grupo) == [circular]


def test_reconstruir_troca_o_conteudo():
    grupo = pygame.sprite.Group(_Sonda((0, 0, 10, 10)))
    bp = BroadphaseInimigos()
    bp.reconstruir(grupo)
    grupo.empty()
    novo = _Sonda((100, 100, 10, 10))
    grupo.add(novo)
    bp.reconstruir(grupo)
    assert bp.candidatos(pygame.Rect(0, 0, 200, 200), grupo) == [novo]


@pytest.mark.parametrize('rect', [None, 'texto'])
def test_consulta_sem_rect_lanca(rect):
    bp = BroadphaseInimigos()
    bp.reconstruir(pygame.sprite.Group())
    with pytest.raises((TypeError, AttributeError)):
        bp.candidatos(rect, pygame.sprite.Group())


def test_update_reconstroi_o_broadphase_a_cada_frame(novo_jogo):
    cm = novo_jogo.collision_manager
    _horda_mista(novo_jogo, n=20)
    cm.update(DT)
    assert cm.broadphase.inimigos == entity_manager.inimigos_grupo.sprites()
    entity_manager.inimigos_grupo.sprites()[0].kill()
    cm.update(DT)
    assert len(cm.broadphase.inimigos) == len(entity_manager.inimigos_grupo)
