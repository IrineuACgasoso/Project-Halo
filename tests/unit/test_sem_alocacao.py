"""Roteiro C3: projéteis e efeitos sem alocação por frame.

- `utils/superficies.py` (máscara em cache, camada alpha reaproveitada, imagem vazia);
- **equivalência de pixels**: os efeitos de área desenhados pela camada reaproveitada saem
  idênticos ao código antigo (cópia literal dele aqui), inclusive cortados pela borda da tela;
- máscaras de inimigo/projétil vindas do cache; partículas com teto global; cache da granada
  de plasma e do brilho dos itens.
"""
import gc
import math
import random

import pygame
import pytest

from helpers import DT, blindar_jogador, contar_alocacoes, simular
from source.enemies.standard.grunt import GruntRed
from source.feats import particulas
from source.feats.effects import RaioEscudo, emitir_poeira
from source.feats.grenades import PlasmaGrenade
from source.feats.items import Items
from source.feats.items import draw as items_draw
from source.feats.projetil.projetil import ProjetilUniversal
from source.feats.skills.artilharia import ArtilhariaAviso
from source.feats.skills.cone_strike.config import CONE_STRIKE_PRESETS
from source.feats.skills.cone_strike.core import ConeStrikeAviso
from source.feats.skills.laserwarning import LaserWarning
from source.feats.skills.onda_emp.config import EMP_PRESETS
from source.feats.skills.onda_emp.core import OndaEMP
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.utils.superficies import SUPERFICIE_VAZIA, camada_alpha, mascara_de, rascunho

V = pygame.math.Vector2
TELA = (1280, 720)
FUNDO = (30, 60, 90)


# ------------------------------------------------------------------ #
# utils/superficies.py
# ------------------------------------------------------------------ #
def test_mascara_de_e_criada_uma_vez_e_igual_a_from_surface():
    s = pygame.Surface((20, 10), pygame.SRCALPHA)
    pygame.draw.circle(s, (255, 0, 0), (5, 5), 4)
    m = mascara_de(s)
    assert mascara_de(s) is m
    nova = pygame.mask.from_surface(s)
    assert m.count() == nova.count() and m.overlap_area(nova, (0, 0)) == nova.count()


def test_mascara_ignora_o_alpha_da_superficie():
    s = pygame.Surface((4, 4), pygame.SRCALPHA)
    s.fill((255, 255, 255, 255))
    antes = mascara_de(s).count()
    s.set_alpha(0)
    assert pygame.mask.from_surface(s).count() == antes == 16


def test_mascara_sai_do_cache_com_a_superficie():
    from source.utils import superficies
    gc.collect()   # lixo cíclico de testes anteriores (ex.: inimigo morto ↔ rotina) não entra na conta
    s = pygame.Surface((3, 3), pygame.SRCALPHA)
    mascara_de(s)
    antes = len(superficies._MASCARAS)
    del s
    gc.collect()
    assert len(superficies._MASCARAS) == antes - 1


def test_camada_alpha_recorta_limpa_e_reaproveita():
    tela = pygame.Surface(TELA)
    camada, area = camada_alpha(tela, (-50, -20, 100, 60))
    assert area == pygame.Rect(0, 0, 50, 40)
    assert camada.get_size() == TELA and camada.get_flags() & pygame.SRCALPHA
    assert camada.get_clip() == area
    camada.fill((255, 0, 0, 255))   # sujeira de um uso anterior
    de_novo, area2 = camada_alpha(tela, (10, 10, 5, 5))
    assert de_novo is camada
    assert de_novo.get_at((12, 12)) == (0, 0, 0, 0)        # a área pedida vem limpa
    assert de_novo.get_at((40, 30))[3] == 255               # fora dela, ninguém garante nada


@pytest.mark.parametrize('caixa', [(-100, -100, 50, 50), (2000, 0, 10, 10), (0, 0, 0, 10)])
def test_camada_alpha_fora_da_tela_devolve_none(caixa):
    camada, area = camada_alpha(pygame.Surface(TELA), caixa)
    assert camada is None and area.width * area.height == 0


def test_camada_alpha_caixa_invalida_lanca():
    with pytest.raises(TypeError):
        camada_alpha(pygame.Surface(TELA), 'caixa')


def test_rascunho_reaproveita_por_tamanho_e_vem_limpo():
    r = rascunho((30, 20))
    assert r.get_size() == (30, 20) and r.get_flags() & pygame.SRCALPHA
    r.fill((255, 255, 255, 255))
    de_novo = rascunho((30.0, 20.0))
    assert de_novo is r and de_novo.get_at((29, 19)) == (0, 0, 0, 0)
    assert rascunho((20, 30)) is not r


@pytest.mark.parametrize('tamanho', [(0, 10), (10, -1)])
def test_rascunho_tamanho_invalido_lanca(tamanho):
    with pytest.raises(ValueError):
        rascunho(tamanho)


def test_superficie_vazia_e_transparente():
    assert SUPERFICIE_VAZIA.get_size() == (1, 1)
    assert SUPERFICIE_VAZIA.get_at((0, 0))[3] == 0


# ------------------------------------------------------------------ #
# Equivalência de pixels: código antigo (cópia literal) × novo
# ------------------------------------------------------------------ #
def _artilharia_antiga(self, surface, offset):
    pos_ajustada = self.posicao - offset
    agora = relogio.agora()
    tamanho_surf = self.cfg.raio_explosao * 2
    temp_surface = pygame.Surface((tamanho_surf, tamanho_surf), pygame.SRCALPHA)
    centro_local = (self.cfg.raio_explosao, self.cfg.raio_explosao)
    if not self.explodiu:
        progresso = min((agora - self.tempo_criacao) / self.cfg.duracao, 1)
        raio_interno = int(self.cfg.raio_explosao * progresso)
        pygame.draw.circle(temp_surface, self.cfg.cor_borda, centro_local, self.cfg.raio_explosao, 4)
        if raio_interno > 0:
            pygame.draw.circle(temp_surface, self.cfg.cor_preenchimento, centro_local, raio_interno)
    elif self.dot_ativo:
        pygame.draw.circle(temp_surface, self.cfg.cor_borda, centro_local, self.cfg.raio_explosao, 3)
        pygame.draw.circle(temp_surface, self.cfg.cor_preenchimento, centro_local, self.cfg.raio_explosao)
    else:
        pygame.draw.circle(temp_surface, self.cfg.cor_explosao, centro_local, self.cfg.raio_explosao)
    surface.blit(temp_surface, (pos_ajustada.x - self.cfg.raio_explosao, pos_ajustada.y - self.cfg.raio_explosao))


def _cone_antigo_forma(self, surface, raio_atual, cor, espessura=0):
    if raio_atual <= 0:
        return
    if self.cfg.angulo_spray >= 360:
        centro = (self.cfg.raio, self.cfg.raio)
        pygame.draw.circle(surface, cor, centro, int(raio_atual), espessura)
        return
    angulo_base = math.atan2(self.direcao.y, self.direcao.x)
    metade_arco = math.radians(self.cfg.angulo_spray / 2)
    ang_min = angulo_base - metade_arco
    ang_max = angulo_base + metade_arco
    centro_local = (self.cfg.raio, self.cfg.raio)
    pontos_poligono = [centro_local]
    passos = max(5, int(self.cfg.angulo_spray / 5))
    passo_rad = (ang_max - ang_min) / passos
    for i in range(passos + 1):
        ang = ang_min + i * passo_rad
        px = centro_local[0] + math.cos(ang) * raio_atual
        py = centro_local[1] + math.sin(ang) * raio_atual
        pontos_poligono.append((px, py))
    if espessura > 0:
        pygame.draw.lines(surface, cor, True, pontos_poligono, espessura)
    else:
        pygame.draw.polygon(surface, cor, pontos_poligono)


def _cone_antigo(self, surface, offset):
    pos_ajustada = self.posicao - offset
    agora = relogio.agora()
    tamanho_surf = self.cfg.raio * 2
    temp_surface = pygame.Surface((tamanho_surf, tamanho_surf), pygame.SRCALPHA)
    if not self.explodiu:
        progresso = min((agora - self.tempo_criacao) / self.cfg.duracao, 1)
        raio_interno = int(self.cfg.raio * progresso)
        _cone_antigo_forma(self, temp_surface, self.cfg.raio, self.cfg.cor_borda, espessura=3)
        if raio_interno > 0:
            _cone_antigo_forma(self, temp_surface, raio_interno, self.cfg.cor_preenchimento, espessura=0)
    else:
        _cone_antigo_forma(self, temp_surface, self.cfg.raio, self.cfg.cor_explosao, espessura=0)
    surface.blit(temp_surface, (pos_ajustada.x - self.cfg.raio, pos_ajustada.y - self.cfg.raio))


def _emp_antigo(self, surface, deslocamento):
    tamanho_aba = int(self.raio_atual + 25)
    raio_int = int(self.raio_atual)
    if raio_int <= 0:
        return
    temp_surface = pygame.Surface((tamanho_aba * 2, tamanho_aba * 2), pygame.SRCALPHA)
    centro_local = (tamanho_aba, tamanho_aba)
    pygame.draw.circle(temp_surface, self.cfg.cor_externa, centro_local, raio_int + 10, 20)
    pygame.draw.circle(temp_surface, self.cfg.cor_central, centro_local, raio_int, self.cfg.espessura_borda)
    if raio_int > 20:
        pygame.draw.circle(temp_surface, self.cfg.cor_interna, centro_local, raio_int - 10, 15)
    pos_ajustada = self.posicao - deslocamento
    surface.blit(temp_surface, (pos_ajustada.x - tamanho_aba, pos_ajustada.y - tamanho_aba))


def _laser_antigo(self, surface, offset):
    temp_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    start_pos_ajustada = self.start_pos - offset
    end_pos_ajustada = self.end_pos - offset
    tempo_passado = relogio.agora() - self.tempo_criacao
    progresso = tempo_passado / self.duracao
    alpha = int(30 + (progresso * 90))
    cor_com_alpha = (*self.cor_laser[:3], alpha)
    pygame.draw.line(temp_surface, cor_com_alpha, start_pos_ajustada, end_pos_ajustada, self.largura)
    surface.blit(temp_surface, (0, 0))


# Posições de tela variadas: centro, frações, cortadas por cada borda, fora da tela.
POSICOES = [V(640, 360), V(640.6, 359.4), V(10.3, 500.7), V(-40.5, -30.2), V(1275.9, 715.1),
            V(-0.5, 200.5), V(300, -0.7), V(5000, 5000)]
OFFSETS = [V(0, 0), V(100.25, -37.75)]


def _iguais(desenhar_antigo, desenhar_novo, efeito):
    for pos in POSICOES:
        for offset in OFFSETS:
            efeito.posicao = pos + offset
            antiga, nova = pygame.Surface(TELA), pygame.Surface(TELA)
            antiga.fill(FUNDO)
            nova.fill(FUNDO)
            desenhar_antigo(efeito, antiga, offset)
            desenhar_novo(nova, offset)
            assert pygame.image.tobytes(antiga, 'RGB') == pygame.image.tobytes(nova, 'RGB'), \
                f'{type(efeito).__name__} difere em {pos} (offset {offset})'


def _estados_da_artilharia(efeito):
    """Telegraph no meio, DoT e explosão."""
    efeito.tempo_criacao = relogio.agora() - efeito.cfg.duracao // 2
    yield
    efeito.explodiu, efeito.dot_ativo = True, True
    yield
    efeito.dot_ativo = False
    yield


@pytest.mark.parametrize('preset', ['padrao', 'hunter_cannon', 'tartarus_leap', 'grave_pit'])
def test_artilharia_desenha_igual_ao_codigo_antigo(novo_jogo, preset):
    efeito = ArtilhariaAviso(V(0, 0), (), novo_jogo, preset=preset)
    for _ in _estados_da_artilharia(efeito):
        _iguais(_artilharia_antiga, efeito.draw, efeito)


@pytest.mark.parametrize('i, preset', enumerate(sorted(CONE_STRIKE_PRESETS)))
def test_cone_desenha_igual_ao_codigo_antigo(novo_jogo, i, preset):
    # Uma direção por preset, alternando as 3 formas (a prova com as 3 em todos rodou na C3)
    for direcao in [(V(1, 0), V(-0.3, 0.8), 135)[i % 3]]:
        efeito = ConeStrikeAviso(V(0, 0), direcao, (), novo_jogo, preset=preset)
        efeito.tempo_criacao = relogio.agora() - efeito.cfg.duracao // 3
        _iguais(_cone_antigo, efeito.draw, efeito)
        efeito.explodiu = True
        _iguais(_cone_antigo, efeito.draw, efeito)


@pytest.mark.parametrize('preset', sorted(EMP_PRESETS))
def test_onda_emp_desenha_igual_ao_codigo_antigo(novo_jogo, preset):
    efeito = OndaEMP(V(0, 0), (), novo_jogo, atacante=novo_jogo.player, preset=preset)
    for raio in (0.5, 15.3, 80.7, 640.2):
        efeito.raio_atual = raio
        _iguais(_emp_antigo, efeito.draw, efeito)


def test_aviso_de_laser_desenha_igual_ao_codigo_antigo(novo_jogo):
    dono = GruntRed(posicao=V(300, 300), game=novo_jogo)
    aviso = LaserWarning(dono, novo_jogo.player, (), novo_jogo)
    aviso.tempo_criacao = relogio.agora() - 700
    for inicio, fim in ((V(300, 300), V(2000, 900)), (V(-200, 50.5), V(900.25, -400))):
        aviso.start_pos, aviso.end_pos = inicio, fim
        antiga, nova = pygame.Surface(TELA), pygame.Surface(TELA)
        antiga.fill(FUNDO)
        nova.fill(FUNDO)
        _laser_antigo(aviso, antiga, V(10, 20))
        aviso.draw(nova, V(10, 20))
        assert pygame.image.tobytes(antiga, 'RGB') == pygame.image.tobytes(nova, 'RGB')


def test_efeitos_de_area_nao_alocam_no_draw(novo_jogo):
    efeitos = [ArtilhariaAviso(V(640, 360), (), novo_jogo),
               ConeStrikeAviso(V(640, 360), V(1, 0), (), novo_jogo),
               OndaEMP(V(640, 360), (), novo_jogo, atacante=novo_jogo.player),
               LaserWarning(GruntRed(posicao=V(300, 300), game=novo_jogo), novo_jogo.player, (), novo_jogo)]
    efeitos[2].raio_atual = 200
    tela = pygame.Surface(TELA)
    for efeito in efeitos:
        efeito.draw(tela, V(0, 0))   # aquece a camada
    with contar_alocacoes() as c:
        for _ in range(10):
            for efeito in efeitos:
                efeito.draw(tela, V(0, 0))
    assert c.total == 0, dict(c.por_tipo)


def test_raio_de_escudo_desenha_a_linha_sem_alocar(novo_jogo):
    fonte = GruntRed(posicao=V(400, 300), game=novo_jogo)
    alvo = GruntRed(posicao=V(700, 500), game=novo_jogo)
    raio = RaioEscudo(fonte, alvo, (), cor=(255, 40, 0))
    assert raio.rect.collidepoint(fonte.rect.center) and raio.rect.collidepoint(alvo.rect.center)
    tela = pygame.Surface(TELA)
    tela.fill(FUNDO)
    raio.draw(tela, V(0, 0))
    meio = (V(fonte.rect.center) + V(alvo.rect.center)) / 2
    assert tela.get_at((round(meio.x), round(meio.y)))[:3] == (255, 255, 255)   # núcleo branco
    assert tela.get_at((5, 5))[:3] == FUNDO
    with contar_alocacoes() as c:
        for _ in range(10):
            raio.update(DT)
            raio.draw(tela, V(0, 0))
    assert c.total == 0, dict(c.por_tipo)


# ------------------------------------------------------------------ #
# Máscaras em cache
# ------------------------------------------------------------------ #
def test_inimigo_usa_a_mascara_do_frame_em_cache(novo_jogo):
    inimigo = GruntRed(posicao=novo_jogo.player.posicao + V(300, 0), game=novo_jogo)
    for _ in range(4):
        inimigo.frame_atual += 1
        inimigo.mostrar_frame_atual()
        origem = inimigo.sprites[inimigo.estado_animacao][inimigo.frame_atual]
        assert inimigo.mask is mascara_de(origem)
        assert inimigo.image is not origem   # cópia própria: o alpha é por inimigo
        assert inimigo.mask.count() == pygame.mask.from_surface(inimigo.image).count()


def test_set_image_sem_origem_calcula_a_mascara(novo_jogo):
    inimigo = GruntRed(posicao=novo_jogo.player.posicao + V(300, 0), game=novo_jogo)
    imagem = pygame.Surface((10, 10), pygame.SRCALPHA)
    imagem.fill((255, 255, 255, 255), (0, 0, 5, 10))
    inimigo.set_image(imagem)
    assert inimigo.mask.count() == 50


def test_projeteis_iguais_compartilham_a_mascara(novo_jogo):
    a = ProjetilUniversal(V(0, 0), (), novo_jogo, 'PLAYER', 'm50', direcao_custom=V(1, 0))
    b = ProjetilUniversal(V(50, 0), (), novo_jogo, 'PLAYER', 'm50', direcao_custom=V(1, 0))
    assert a.image is b.image and a.mask is b.mask


@pytest.mark.integration
def test_update_da_horda_nao_cria_mascara(novo_jogo):
    """O update da horda criava ~12 máscaras por frame (animação dos inimigos)."""
    blindar_jogador(novo_jogo.player)
    novo_jogo.spawner.update = lambda dt: None
    while len(entity_manager.inimigos_grupo) < 150:
        novo_jogo.spawner.spawnar('normal')
    simular(novo_jogo, 1)   # aquece os caches
    with contar_alocacoes() as c:
        simular(novo_jogo, 2)
    assert c.por_tipo['mask.from_surface'] <= 2, dict(c.por_tipo)   # só projétil em ângulo novo


# ------------------------------------------------------------------ #
# Partículas
# ------------------------------------------------------------------ #
def test_particula_anda_some_com_fade_e_morre(novo_jogo):
    base = particulas.imagem_pixel((255, 0, 0), 4)
    p = particulas.emitir(V(100, 100), base, (60, 0), 500)
    assert p in entity_manager.particulas_grupo and p in entity_manager.all_sprites
    alphas = []
    for _ in range(round(0.4 / DT)):
        relogio.avancar(DT)
        p.update(DT)
        alphas.append(p.image.get_alpha())
    assert p.posicao.x == pytest.approx(124, abs=0.5)
    assert alphas == sorted(alphas, reverse=True) and alphas[-1] < 100
    relogio.avancar(0.2)
    p.update(DT)
    assert not p.alive()


def test_teto_global_descarta_as_novas(novo_jogo, monkeypatch):
    monkeypatch.setattr(particulas, 'TETO_PARTICULAS', 5)
    base = particulas.imagem_pixel((0, 255, 0), 3)
    criadas = [particulas.emitir(V(0, 0), base, (0, 0), 1000) for _ in range(8)]
    assert sum(p is not None for p in criadas) == 5
    assert len(entity_manager.particulas_grupo) == 5
    criadas[0].kill()
    assert particulas.emitir(V(0, 0), base, (0, 0), 1000) is not None


def test_descarte_nao_muda_a_sequencia_do_random(novo_jogo, monkeypatch):
    random.seed(99)
    for _ in range(5):
        emitir_poeira(V(0, 0))
    esperado = random.random()
    monkeypatch.setattr(particulas, 'TETO_PARTICULAS', 0)
    random.seed(99)
    for _ in range(5):
        assert emitir_poeira(V(0, 0)) is None
    assert random.random() == esperado


def test_particulas_nao_alocam_depois_do_aquecimento(novo_jogo):
    base = particulas.imagem_pixel((1, 2, 3), 5, 'circulo')
    for nivel in range(256):
        particulas.variante_alpha(base, nivel)
    with contar_alocacoes() as c:
        vivas = [particulas.emitir(V(i, 0), base, (10, 10), 300) for i in range(50)]
        for _ in range(20):
            relogio.avancar(DT)
            for p in vivas:
                p.update(DT)
    assert c.total == 0, dict(c.por_tipo)


@pytest.mark.parametrize('alpha,esperado', [(-50, 0), (0, 0), (255, 255), (999, 255)])
def test_variante_alpha_limita_a_faixa(alpha, esperado):
    base = particulas.imagem_pixel((9, 9, 9), 2)
    assert particulas.variante_alpha(base, alpha).get_alpha() == esperado
    assert len({particulas.variante_alpha(base, a) for a in range(256)}) == particulas.NIVEIS_ALPHA


@pytest.mark.parametrize('kwargs', [dict(tamanho=0), dict(tamanho=-3), dict(forma='estrela')])
def test_imagem_pixel_invalida_lanca(kwargs):
    with pytest.raises(ValueError):
        particulas.imagem_pixel((1, 1, 1), **{'tamanho': 3, **kwargs})


def test_particula_com_duracao_invalida_lanca(novo_jogo):
    with pytest.raises(ValueError):
        particulas.emitir(V(0, 0), particulas.imagem_pixel((1, 1, 1), 2), (0, 0), 0)


def test_nova_partida_zera_as_particulas(game):
    from helpers import voltar_ao_menu
    voltar_ao_menu(game)
    game.iniciar_novo_jogo()
    emitir_poeira(V(0, 0))
    assert len(entity_manager.particulas_grupo) == 1
    voltar_ao_menu(game)
    game.iniciar_novo_jogo()
    assert len(entity_manager.particulas_grupo) == 0


def test_coleta_de_item_emite_particulas_no_grupo(novo_jogo):
    item = Items(novo_jogo.player.posicao + V(5, 0), 'exp_shard', (entity_manager.all_sprites,
                                                                   entity_manager.items_grupo))
    item.coletar(novo_jogo.player)
    assert 6 <= len(entity_manager.particulas_grupo) <= 9


# ------------------------------------------------------------------ #
# Granada de plasma e brilho dos itens
# ------------------------------------------------------------------ #
def test_granada_de_plasma_reaproveita_a_composta(novo_jogo):
    granada = PlasmaGrenade(V(100, 100), V(400, 100), (entity_manager.all_sprites,), novo_jogo,
                            'PLAYER', entity_manager.inimigos_grupo)
    vistas = set()
    for _ in range(120):   # 2 s: o pulso percorre todos os níveis
        relogio.avancar(DT)
        granada.update(DT)
        vistas.add(id(granada.image))
    assert len(vistas) <= (220 - 90) // PlasmaGrenade.PASSO_ALPHA_PULSO + 1
    with contar_alocacoes() as c:
        for _ in range(60):
            relogio.avancar(DT)
            granada.update(DT)
    assert c.por_tipo['Surface'] == 0, dict(c.por_tipo)


def test_composta_da_granada_igual_a_composicao_antiga(novo_jogo):
    granada = PlasmaGrenade(V(100, 100), V(400, 100), (entity_manager.all_sprites,), novo_jogo,
                            'PLAYER', entity_manager.inimigos_grupo)
    for alpha in (90, 150, 220):
        glow = granada._obter_glow_base().copy()
        glow.set_alpha(alpha)
        cw, ch = granada.tamanho_canvas
        antiga = pygame.Surface(granada.tamanho_canvas, pygame.SRCALPHA)
        gw, gh = glow.get_size()
        antiga.blit(glow, (cw / 2 - gw / 2, ch / 2 - gh / 2), special_flags=pygame.BLEND_RGBA_ADD)
        bw, bh = granada.tamanho
        antiga.blit(granada.image_base, (cw / 2 - bw / 2, ch / 2 - bh / 2))
        nova = granada._obter_composta(alpha)
        assert pygame.image.tobytes(antiga, 'RGBA') == pygame.image.tobytes(nova, 'RGBA')


def test_brilho_do_item_reaproveita_frames(novo_jogo):
    item = Items(novo_jogo.player.posicao + V(300, 0), 'exp_shard', (entity_manager.all_sprites,
                                                                     entity_manager.items_grupo))
    for _ in range(60):
        relogio.avancar(DT)
        item.update(DT)
    frames = set()
    with contar_alocacoes() as c:
        for _ in range(240):
            relogio.avancar(DT)
            item.update(DT)
            frames.add(id(item.image))
    assert c.total == 0
    assert len(frames) <= (255 - 125) // items_draw.PASSO_ALPHA_PULSO + 1
