"""Zoom da câmera: transição, limites do mapa, o mundo reduzido na tela e quem depende da área visível."""
import pygame
import pytest

from helpers import DT, MapaSemImagem, contar_alocacoes, ir_para_fase, simular
from source.systems.camera import Camera
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.utils.reducao import reduzir, superficie_do_mundo

V = pygame.math.Vector2


def _camera(largura=4608, altura=3072):
    return Camera(1280, 720, MapaSemImagem(largura, altura))


# ── Camera ───────────────────────────────────────────────────────────────────
def test_camera_comeca_normal():
    camera = _camera()
    assert camera.zoom == 1 and camera.visao == camera.visao_maxima == (1280, 720)


def test_zoom_sem_duracao_vale_na_hora():
    camera = _camera()
    camera.definir_zoom(0.5)
    assert camera.zoom == 0.5 and camera.visao == (2560, 1440)


def test_zoom_anda_suave_e_so_para_um_lado():
    camera = _camera()
    camera.definir_zoom(0.5, 1000)
    valores = [camera.zoom]
    for _ in range(70):
        relogio.avancar(DT)
        camera.update(V(2000, 1500))
        valores.append(camera.zoom)
    assert valores[0] == 1 and valores[-1] == 0.5
    assert all(b <= a for a, b in zip(valores, valores[1:]))
    assert 0.5 < valores[30] < 1


def test_zoom_no_meio_pode_voltar_sem_salto():
    camera = _camera()
    camera.definir_zoom(0.5, 1000)
    for _ in range(30):
        relogio.avancar(DT)
        camera.update(V(2000, 1500))
    meio = camera.zoom
    camera.definir_zoom(1, 1000)
    assert camera.zoom == meio
    relogio.avancar(2)
    camera.update(V(2000, 1500))
    assert camera.zoom == 1 and camera.visao_maxima == (1280, 720)


def test_superficie_do_mundo_tem_tamanho_fixo_durante_a_transicao():
    camera = _camera()
    tamanhos = set()
    for alvo in (0.5, 1):
        camera.definir_zoom(alvo, 500)
        for _ in range(28):
            relogio.avancar(DT)
            camera.update(V(2000, 1500))
            tamanhos.add(camera.visao_maxima)
    assert tamanhos == {(2560, 1440)}


@pytest.mark.parametrize('alvo', [0, -1, 1.2])
def test_zoom_invalido(alvo):
    with pytest.raises(ValueError):
        _camera().definir_zoom(alvo)


def test_duracao_invalida():
    with pytest.raises(ValueError):
        _camera().definir_zoom(0.5, -1)


def test_mapa_pequeno_limita_o_zoom():
    """O mapa sempre cobre a tela: num mapa de 2304×1536, o mais afastado é 0,5556."""
    camera = _camera(2304, 1536)
    camera.definir_zoom(0.3)
    largura, altura = camera.visao
    assert largura <= 2304 and altura <= 1536
    assert camera.zoom == pytest.approx(1280 / 2304)


@pytest.mark.parametrize('jogador', [(0, 0), (4608, 3072), (2300, 1500)])
def test_camera_afastada_nao_sai_do_mapa(jogador):
    camera = _camera()
    camera.definir_zoom(0.5)
    camera.update(V(jogador))
    assert 0 <= camera.offset.x <= 4608 - 2560 and 0 <= camera.offset.y <= 3072 - 1440


def test_jogador_no_centro_da_visao():
    camera = _camera()
    camera.definir_zoom(0.5)
    camera.update(V(2300, 1500))
    assert camera.offset == V(2300 - 1280, 1500 - 720)


def test_restaurar_zoom():
    camera = _camera()
    camera.definir_zoom(0.5)
    camera.restaurar_zoom()
    assert camera.zoom == 1 and camera.zoom_alvo == 1 and camera.visao_maxima == (1280, 720)


def test_zoom_congela_com_o_jogo(novo_jogo):
    novo_jogo.camera.definir_zoom(0.5, 1000)
    antes = novo_jogo.camera.zoom
    pygame.time.wait(5)
    novo_jogo.draw()
    assert novo_jogo.camera.zoom == antes


def test_partida_nova_e_fase_nova_voltam_ao_normal(novo_jogo):
    novo_jogo.camera.definir_zoom(0.5)
    novo_jogo.stage_manager._trocar_dados_fase()
    assert novo_jogo.camera.zoom == 1


# ── Desenho ──────────────────────────────────────────────────────────────────
def test_reduzir_mostra_a_area_toda(tela):
    origem = superficie_do_mundo((800, 400), tela)
    origem.fill('black')
    origem.fill((255, 0, 0), (0, 0, 200, 200))
    origem.fill((0, 0, 255), (200, 0, 200, 200))
    destino = pygame.Surface((200, 100), 0, tela)
    reduzir(origem, (400, 200), destino)
    assert destino.get_at((10, 10))[:3] == (255, 0, 0) and destino.get_at((190, 90))[:3] == (0, 0, 255)


def test_superficie_do_mundo_e_reaproveitada(tela):
    assert superficie_do_mundo((800, 400), tela) is superficie_do_mundo((800, 400), tela)


def test_zoom_mostra_o_que_estava_fora_da_tela(novo_jogo):
    """Um item a 900 px do jogador só aparece com a câmera afastada."""
    ir_para_fase(novo_jogo, 3)
    jogador = novo_jogo.player
    jogador.posicao.update(2300, 1500)
    jogador.hitbox.center = jogador.rect.center = (2300, 1500)

    class Marca(pygame.sprite.Sprite):
        def __init__(self):
            super().__init__(entity_manager.all_sprites)
            self.image = pygame.Surface((40, 40))
            self.image.fill((255, 0, 255))
            self.rect = self.image.get_rect(center=(3200, 1500))

    Marca()
    camera = novo_jogo.camera
    camera.update(jogador.posicao)
    novo_jogo.renderer._draw_mundo()
    assert novo_jogo.tela.get_at((1279, 360))[:3] != (255, 0, 255)
    camera.definir_zoom(0.5)
    camera.update(jogador.posicao)
    novo_jogo.renderer._draw_mundo()
    assert novo_jogo.tela.get_at((640 + 450, 360))[:3] == (255, 0, 255)
    assert novo_jogo.renderer._erros_logados == set()


@pytest.mark.parametrize('zoom', [1, 0.5625])
def test_desenhar_com_zoom_nao_aloca_por_frame(novo_jogo, zoom):
    novo_jogo.spawner.update = lambda dt: None
    novo_jogo.camera.definir_zoom(zoom)
    novo_jogo.update(DT)
    for _ in range(3):
        novo_jogo.draw()
    with contar_alocacoes() as contador:
        for _ in range(10):
            novo_jogo.draw()
    assert contador.total == 0, contador.por_tipo


def test_borda_do_mapa_com_tremor_nao_deixa_rastro(novo_jogo):
    """Fora do mapa é preto, não o quadro anterior."""
    camera = novo_jogo.camera
    camera.definir_zoom(0.5)
    camera.update(V(0, 0))
    camera.shake_offset.update(-60, -60)
    mundo = superficie_do_mundo(camera.visao_maxima, novo_jogo.tela)
    mundo.fill((255, 0, 255))
    novo_jogo.renderer._draw_mundo()
    assert mundo.get_at((mundo.get_width() - 2, mundo.get_height() - 2))[:3] != (255, 0, 255)


def test_y_desenho_manda_na_ordem(novo_jogo):
    """Quem declara `y_desenho` sai por cima de quem tem o rect mais baixo na tela."""
    class Quadro(pygame.sprite.Sprite):
        def __init__(self, cor, y, y_desenho=None):
            super().__init__(entity_manager.all_sprites)
            self.image = pygame.Surface((60, 60))
            self.image.fill(cor)
            self.rect = self.image.get_rect(center=(300, y))
            if y_desenho is not None:
                self.y_desenho = y_desenho

    for sprite in list(entity_manager.all_sprites):
        sprite.kill()
    Quadro((255, 0, 0), 310)                       # mais baixo: normalmente por cima
    Quadro((0, 255, 0), 300, y_desenho=900)
    novo_jogo.renderer._draw_sprites(novo_jogo.tela, V(0, 0))
    assert novo_jogo.tela.get_at((300, 300))[:3] == (0, 255, 0)


def test_tijolo_rebate_na_borda_do_que_aparece(novo_jogo):
    from source.feats.projetil.brick import Brick
    jogador = novo_jogo.player

    def ate_onde(zoom):
        novo_jogo.camera.restaurar_zoom()
        novo_jogo.camera.definir_zoom(zoom)
        tijolo = Brick(jogador.posicao, (entity_manager.all_sprites,), jogador, novo_jogo, V(1, 0), 1, 1500, 3)
        longe = 0
        for _ in range(120):
            tijolo.update(DT)
            longe = max(longe, tijolo.posicao.x - jogador.posicao.x)
        tijolo.kill()
        return longe

    assert ate_onde(1) == pytest.approx(640 - 24, abs=1)
    assert ate_onde(0.5) == pytest.approx(1280 - 24, abs=1)


def test_mundo_continua_rodando_com_zoom(novo_jogo):
    novo_jogo.camera.definir_zoom(0.6, 400)
    simular(novo_jogo, 1, desenhar_a_cada=4)
    assert novo_jogo.renderer._erros_logados == set()
