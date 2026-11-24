"""Fuel Rod: projétil (gota de plasma) e área (poça) próprios; antes, os da granada de plasma."""
import pygame
import pytest

from helpers import DT, contar_alocacoes
from source.enemies.standard.grunt import GruntRed
from source.feats.assets import ASSETS
from source.feats.grenades import FuelRodGrenade, PlasmaGrenade
from source.feats.skills.artilharia import ArtilhariaAviso, PocaDePlasma
from source.feats.skills.artilharia.config import ARTILHARIA_PRESETS, ArtilhariaConfig
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio

V = pygame.math.Vector2
PRESET = ARTILHARIA_PRESETS['fuel_rod']


def _carga(game, destino=V(400, 0), **kwargs):
    p = V(game.player.posicao)
    return FuelRodGrenade(posicao_inicial=p, posicao_alvo=p + destino, grupos=(entity_manager.all_sprites,),
                          game=game, dono='PLAYER', inimigos_grupo=entity_manager.inimigos_grupo, **kwargs)


def _poca(game, posicao=V(600, 600), **cfg):
    config = ArtilhariaConfig(**{**vars(PRESET), **cfg})
    return PocaDePlasma(V(posicao), (entity_manager.all_sprites,), game, dono='PLAYER', custom_config=config)


def _passos(sprite, n):
    for _ in range(n):
        relogio.avancar(DT)
        sprite.update(DT)


# ------------------------------------------------------------------ #
# Projétil
# ------------------------------------------------------------------ #
def test_arte_propria_e_achatada():
    arte = ASSETS['projectiles']['fuel_rod']
    assert arte is not ASSETS['projectiles']['plasma_grenade']
    largura, altura = arte.get_bounding_rect().size
    assert 1.3 < largura / altura < 2.2              # gota achatada, não uma bola nem um risco
    assert arte.get_at((40, 17))[:3] == (255, 255, 240)   # núcleo branco de tão quente


def test_nao_e_mais_a_granada_de_plasma(novo_jogo):
    assert not isinstance(_carga(novo_jogo), PlasmaGrenade)
    assert (PRESET.cor_borda, PRESET.cor_preenchimento) != (
        ARTILHARIA_PRESETS['plasma_grenade'].cor_borda, ARTILHARIA_PRESETS['plasma_grenade'].cor_preenchimento)


def test_acompanha_a_curva_do_arco(novo_jogo):
    """Sobe apontando para cima, passa reto no alto e desce apontando para baixo."""
    carga = _carga(novo_jogo)
    assert 0 < carga.angulo < 90
    while carga.start_pos.distance_to(carga.posicao) < carga.total_dist / 2:
        _passos(carga, 1)
    assert carga.angulo in (0, 350)
    while carga.start_pos.distance_to(carga.posicao) < carga.total_dist * 0.9:
        _passos(carga, 1)
    assert 270 < carga.angulo < 360


def test_alvo_no_mesmo_ponto_nao_quebra(novo_jogo):
    carga = _carga(novo_jogo, destino=V(0, 0))
    _passos(carga, 1)
    assert not carga.alive()


def test_o_rect_que_gruda_nao_depende_da_imagem(novo_jogo):
    carga = _carga(novo_jogo)
    for _ in range(20):
        _passos(carga, 1)
        assert carga.rect.size == (FuelRodGrenade.LADO_COLISAO,) * 2
        assert carga.image.get_width() > carga.rect.width


def test_rastro_so_no_voo(novo_jogo):
    alvo = GruntRed(posicao=novo_jogo.player.posicao + V(2000, 0), game=novo_jogo)
    carga = _carga(novo_jogo)
    _passos(carga, 12)
    assert len(entity_manager.particulas_grupo) >= 5
    carga._grudar(alvo)
    antes = len(entity_manager.particulas_grupo)
    _passos(carga, 12)
    assert len(entity_manager.particulas_grupo) == antes


def test_some_ao_virar_poca(novo_jogo):
    alvo = GruntRed(posicao=novo_jogo.player.posicao + V(300, 0), game=novo_jogo)
    carga = _carga(novo_jogo)
    carga._grudar(alvo)
    assert isinstance(carga.aviso, PocaDePlasma)
    while not carga.aviso.explodiu:
        assert carga.alive()
        _passos(carga.aviso, 1)
        carga.update(DT)
    assert not carga.alive() and carga.aviso.alive() and carga.aviso.dot_ativo


def test_voo_nao_aloca_depois_do_cache(novo_jogo):
    for _ in range(12):     # os primeiros voos enchem os caches (ângulo × halo e cor × tamanho do rastro)
        carga = _carga(novo_jogo)
        with contar_alocacoes() as c:
            while carga.start_pos.distance_to(carga.posicao) < carga.total_dist * 0.9:
                _passos(carga, 1)
        carga.kill()
    assert c.por_tipo['Surface'] == 0, dict(c.por_tipo)


# ------------------------------------------------------------------ #
# Poça
# ------------------------------------------------------------------ #
def test_dano_da_poca_e_o_da_artilharia(novo_jogo):
    """Impacto na explosão e 1 tique por segundo, só dentro do raio."""
    perto = GruntRed(posicao=V(600, 600), game=novo_jogo)
    longe = GruntRed(posicao=V(600 + PRESET.raio_explosao + 1, 600), game=novo_jogo)
    for inimigo in (perto, longe):
        inimigo.vida, inimigo.escudo_atual = 1000, 0
    poca = _poca(novo_jogo, dano=25, dano_por_segundo=3, duracao=100, duracao_dot=2500)
    _passos(poca, 240)
    assert not poca.alive()
    assert perto.vida == 1000 - 25 - 2 * 3 and longe.vida == 1000


def test_sem_dot_se_comporta_como_a_artilharia(novo_jogo):
    poca = _poca(novo_jogo, dot=False, duracao=50)
    _passos(poca, 60)
    assert isinstance(poca, ArtilhariaAviso) and not poca.alive()


def test_explosao_respinga_e_a_poca_solta_vapor(novo_jogo):
    poca = _poca(novo_jogo, duracao=50)
    _passos(poca, 2)
    assert len(entity_manager.particulas_grupo) == 0
    _passos(poca, 3)
    respingo = len(entity_manager.particulas_grupo)
    assert respingo >= PocaDePlasma.RESPINGOS
    _passos(poca, 30)
    assert len(entity_manager.particulas_grupo) > respingo


def test_poca_desenha_dentro_do_raio_e_esfria(novo_jogo):
    poca = _poca(novo_jogo, posicao=V(400, 400), duracao=50, duracao_dot=3000)
    _passos(poca, 60)
    tela = pygame.Surface((800, 800))
    poca.draw(tela, V(0, 0))
    _, verde, _, _ = tela.get_at((400, 400))
    assert verde > 60
    fora = pygame.mask.from_threshold(tela, (0, 0, 0), (1, 1, 1))
    for angulo in range(0, 360, 15):
        ponto = V(400, 400) + V(PRESET.raio_explosao + 2, 0).rotate(angulo)
        assert fora.get_at((round(ponto.x), round(ponto.y)))
    assert poca.alpha_da_poca(relogio.agora()) == 255
    fim = poca.dot_inicio + poca.cfg.duracao_dot
    assert 0 < poca.alpha_da_poca(fim - PocaDePlasma.MS_ESFRIANDO / 2) < 255
    assert poca.alpha_da_poca(fim) == poca.alpha_da_poca(fim + 1000) == 0


def test_poca_fica_por_baixo_de_quem_esta_dentro(novo_jogo):
    """Parada ou presa a um inimigo: o Renderer ordena pelo centery do rect."""
    inimigo = GruntRed(posicao=V(600, 600), game=novo_jogo)
    parada = _poca(novo_jogo, duracao=50)
    presa = PocaDePlasma(inimigo.posicao, (entity_manager.all_sprites,), novo_jogo, dono='PLAYER',
                         custom_config=ArtilhariaConfig(**{**vars(PRESET), 'duracao': 50}), grude=True, alvo=inimigo)
    for poca in (parada, presa):
        _passos(poca, 10)
        assert poca.dot_ativo and poca.rect.centery <= inimigo.rect.centery - PRESET.raio_explosao + 1
        assert poca.posicao == inimigo.posicao      # o dano e o desenho seguem no lugar


@pytest.mark.parametrize('raio', [60, 150, 200])
def test_quadros_seguem_o_raio(raio):
    from source.feats.skills.artilharia.poca_plasma import quadros_da_poca
    quadros = quadros_da_poca(raio)
    assert len(quadros) == len(ASSETS['effects']['fuel_rod_area'])
    assert all(q.get_size() == (raio * 2, raio * 2) for q in quadros)
    assert quadros_da_poca(raio) is quadros


def test_desenho_da_poca_nao_aloca(novo_jogo):
    poca = _poca(novo_jogo, posicao=V(400, 400), duracao=50)
    tela = novo_jogo.tela
    _passos(poca, 5)
    poca.draw(tela, V(0, 0))
    with contar_alocacoes() as c:
        for _ in range(60):
            relogio.avancar(DT)
            poca.draw(tela, V(0, 0))
    assert c.por_tipo['Surface'] == 0, dict(c.por_tipo)


# ------------------------------------------------------------------ #
# Ícones
# ------------------------------------------------------------------ #
def test_toda_arma_tem_icone():
    from source.systems.levelup import ARMAS_REGISTRO
    assert sorted(set(ARMAS_REGISTRO) - set(ASSETS['icons'])) == []
