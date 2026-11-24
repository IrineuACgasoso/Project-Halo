"""Roteiro C4: culling pela câmera e HUD sem alocação quando nada muda."""
import pygame
import pytest

from helpers import DT, blindar_jogador, contar_alocacoes, simular
from source.systems.entitymanager import entity_manager
from source.systems.hud import hud_draw

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


class _FonteContada:
    """Embrulha uma Font (tipo em C, não dá para trocar o método) e conta os render."""

    def __init__(self, fonte):
        self._fonte = fonte
        self.renders = 0

    def render(self, *args, **kwargs):
        self.renders += 1
        return self._fonte.render(*args, **kwargs)


def _contar_renders(hud):
    fontes = {}
    for nome in ('_font_hud', '_font_xp', '_font_boss', '_font_score', '_font_timer'):
        fontes[nome] = _FonteContada(getattr(hud, nome))
        setattr(hud, nome, fontes[nome])
    return fontes


# ------------------------------------------------------------------ #
# Culling
# ------------------------------------------------------------------ #
def test_sprite_fora_da_tela_nao_e_desenhado(novo_jogo):
    deslocamento = V(1000, 500)
    largura, altura = novo_jogo.tela.get_size()
    grupos = (entity_manager.all_sprites,)
    dentro = _SpriteImagem((1100, 600, 20, 20), grupos)
    na_borda = _SpriteImagem((1000 - 19, 500 - 19, 20, 20), grupos)   # 1 px de imagem na tela
    fora = [_SpriteImagem(r, grupos) for r in ((1000 - 40, 600, 20, 20), (1000 + largura + 10, 600, 20, 20),
                                               (1100, 500 - 50, 20, 20), (1100, 500 + altura + 5, 20, 20))]
    visiveis = novo_jogo.renderer._sprites_visiveis(novo_jogo.tela, deslocamento)
    assert dentro in visiveis and na_borda in visiveis
    assert not any(s in visiveis for s in fora)


def test_imagem_maior_que_o_rect_conta_pela_imagem(novo_jogo):
    sprite = _SpriteImagem((0, 0, 10, 10), (entity_manager.all_sprites,))
    sprite.image = pygame.Surface((400, 400))   # rect pequeno fora, imagem entra na tela
    sprite.rect.topleft = (1000 - 300, 500)
    assert sprite in novo_jogo.renderer._sprites_visiveis(novo_jogo.tela, V(1000, 500))


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
# HUD
# ------------------------------------------------------------------ #
def _aquecer(game):
    for _ in range(3):
        game.draw()


def test_draw_sem_mudanca_de_valor_nao_aloca_nem_renderiza_texto(novo_jogo):
    """Catraca do draw em 'jogando' (C4): estado parado = zero Surface e zero Font.render."""
    blindar_jogador(novo_jogo.player)
    for arma in ('needler', 'carabin'):
        novo_jogo.event_manager._aplicar_escolha_de_upgrade(arma)
    novo_jogo.player.escudo_atual = novo_jogo.player.escudo_maximo = 50
    novo_jogo.player.experiencia_atual = 10
    simular(novo_jogo, 1)
    fontes = _contar_renders(novo_jogo.hud)
    _aquecer(novo_jogo)
    for f in fontes.values():
        f.renders = 0
    with contar_alocacoes() as c:
        for _ in range(30):
            novo_jogo.draw()
    assert c.total == 0, dict(c.por_tipo)
    assert sum(f.renders for f in fontes.values()) == 0
    assert novo_jogo.renderer._erros_logados == set()


def test_draw_com_boss_parado_nao_aloca(novo_jogo):
    blindar_jogador(novo_jogo.player)
    novo_jogo.spawner.spawnar('hunter')
    simular(novo_jogo, 1, desenhar_a_cada=1)   # o draw do HUD escolhe o foco da barra do boss
    assert novo_jogo.hud.foco_barra_vida is not None
    fontes = _contar_renders(novo_jogo.hud)
    _aquecer(novo_jogo)
    for f in fontes.values():
        f.renders = 0
    with contar_alocacoes() as c:
        for _ in range(30):
            novo_jogo.draw()
    assert c.total == 0, dict(c.por_tipo)
    assert sum(f.renders for f in fontes.values()) == 0


def test_texto_renderiza_de_novo_so_quando_o_valor_muda(novo_jogo):
    fontes = _contar_renders(novo_jogo.hud)
    _aquecer(novo_jogo)
    placar = fontes['_font_score']
    placar.renders = 0
    novo_jogo.draw()
    assert placar.renders == 0
    novo_jogo.pontuacao = getattr(novo_jogo, 'pontuacao', 0) + 7
    novo_jogo.draw()
    novo_jogo.draw()
    assert placar.renders == 1


def test_barra_reaproveita_a_surface_e_redesenha_quando_muda():
    chave = ('teste', (40, 8))
    a, redesenhar = hud_draw._camada_barra(chave, (40, 8), (10, (1, 2, 3)))
    assert redesenhar
    a.fill((255, 0, 0, 255))
    b, redesenhar = hud_draw._camada_barra(chave, (40, 8), (10, (1, 2, 3)))
    assert b is a and not redesenhar and b.get_at((0, 0)) == (255, 0, 0, 255)
    c, redesenhar = hud_draw._camada_barra(chave, (40, 8), (11, (1, 2, 3)))
    assert c is a and redesenhar and c.get_at((0, 0)) == (0, 0, 0, 0)   # volta limpa
    d, redesenhar = hud_draw._camada_barra(chave, (50, 8), (11, (1, 2, 3)))
    assert d is not a and d.get_size() == (50, 8) and redesenhar


def test_barra_de_vida_acompanha_o_valor(novo_jogo):
    player = novo_jogo.player
    tela = pygame.Surface(novo_jogo.tela.get_size())
    largura = pygame.display.get_surface().get_width()
    rect = pygame.Rect(largura - hud_draw._MARGEM_X - hud_draw._VIDA_W,
                       hud_draw._MARGEM_Y + hud_draw._ESCUDO_H + hud_draw._GAP,
                       hud_draw._VIDA_W, hud_draw._VIDA_H)
    ponto = (rect.x + rect.width * 3 // 4, rect.centery)   # dentro dos 75% finais da barra
    player.vida_atual = player.vida_maxima
    hud_draw._draw_player_bars(tela, player)
    cheia = tela.get_at(ponto)
    player.vida_atual = player.vida_maxima * 0.5
    tela.fill((0, 0, 0))
    hud_draw._draw_player_bars(tela, player)
    assert tela.get_at(ponto) != cheia   # a metade final da barra se apagou


@pytest.mark.parametrize('texto', ['', 'LVL 1'])
def test_texto_vazio_ou_normal_nao_quebra(novo_jogo, texto):
    fonte = _FonteContada(novo_jogo.hud._font_hud)
    s1 = hud_draw._texto(('teste', texto), fonte, texto, (255, 255, 255))
    s2 = hud_draw._texto(('teste', texto), fonte, texto, (255, 255, 255))
    assert s1 is s2 and fonte.renders == 1


def test_partida_com_draw_nao_registra_erro_de_render(novo_jogo):
    blindar_jogador(novo_jogo.player)
    simular(novo_jogo, 3, desenhar_a_cada=1)
    assert novo_jogo.renderer._erros_logados == set()
    novo_jogo.update(DT)
