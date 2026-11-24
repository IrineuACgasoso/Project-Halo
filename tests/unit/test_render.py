"""Roteiro C4: culling pela câmera e HUD sem alocação quando nada muda."""
import pygame

from helpers import DT, blindar_jogador, simular
from source.systems.entitymanager import entity_manager

V = pygame.math.Vector2


class _SpriteImagem(pygame.sprite.Sprite):
    def __init__(self, rect, grupos=()):
        super().__init__(*grupos)
        self.rect = pygame.Rect(rect)
        self.image = pygame.Surface(self.rect.size)


class _SpriteComDraw(pygame.sprite.Sprite):
    """Como a artilharia: rect 1x1, desenha bem mais que isso."""

    def __init__(self, pos, grupos=()):
        super().__init__(*grupos)
        self.rect = pygame.Rect(pos, (1, 1))
        self.desenhos = 0

    def draw(self, tela, deslocamento):
        self.desenhos += 1


# ------------------------------------------------------------------ #


def test_sprite_com_draw_proprio_sempre_entra(novo_jogo):
    longe = _SpriteComDraw((99999, 99999), (entity_manager.all_sprites,))
    novo_jogo.renderer._draw_sprites(novo_jogo.tela, V(0, 0))
    assert longe.desenhos == 1


def test_sprite_sem_imagem_e_ignorado_sem_erro(novo_jogo):
    sem_imagem = _SpriteImagem((10, 10, 5, 5), (entity_manager.all_sprites,))
    sem_imagem.image = None
    quebrado = _SpriteImagem((10, 10, 5, 5), (entity_manager.all_sprites,))
    del quebrado.image
    visiveis = novo_jogo.renderer._sprites_visiveis(novo_jogo.tela, V(0, 0))
    assert sem_imagem not in visiveis
    novo_jogo.renderer._draw_sprites(novo_jogo.tela, V(0, 0))
    assert novo_jogo.renderer._erros_logados == set()


def test_culling_nao_muda_nenhum_pixel(novo_jogo, monkeypatch):
    """Horda real com tremor de câmera: o mundo desenhado com e sem culling é idêntico."""
    blindar_jogador(novo_jogo.player)
    novo_jogo.spawner.update = lambda dt: None
    while len(entity_manager.inimigos_grupo) < 150:
        novo_jogo.spawner.spawnar('normal')
    renderer = novo_jogo.renderer
    com_culling = renderer._sprites_visiveis
    sem_culling = lambda tela, deslocamento: list(entity_manager.all_sprites)   # noqa: E731
    cortados = 0
    for i in range(12):
        simular(novo_jogo, 0.25)
        if i % 3 == 0:
            novo_jogo.camera.shake(9, duracao=100)
            novo_jogo.camera.update(novo_jogo.player.posicao)
        quadros = []
        for funcao in (sem_culling, com_culling):
            monkeypatch.setattr(renderer, '_sprites_visiveis', funcao)
            renderer._draw_mundo()
            quadros.append(pygame.image.tobytes(novo_jogo.tela, 'RGB'))
        assert quadros[0] == quadros[1], f'quadro {i} difere'
        deslocamento = novo_jogo.camera.offset + novo_jogo.camera.shake_offset
        cortados += len(entity_manager.all_sprites) - len(com_culling(novo_jogo.tela, deslocamento))
    assert cortados > 100, 'quase nada ficou fora da tela: o teste não provaria nada'
    assert renderer._erros_logados == set()


# ------------------------------------------------------------------ #


def test_partida_com_draw_nao_registra_erro_de_render(novo_jogo):
    blindar_jogador(novo_jogo.player)
    simular(novo_jogo, 3, desenhar_a_cada=1)
    assert novo_jogo.renderer._erros_logados == set()
    novo_jogo.update(DT)
