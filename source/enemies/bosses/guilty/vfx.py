"""Efeitos visuais do Guilty: brilho azul, teleporte dourado, feixe da luz visível, esferas, faíscas e o
contador de sentinelas. As imagens são pintadas 1× (no spawn); por frame, só blits.

As funções `impacto_*` recebem o aviso da artilharia (gancho `ao_explodir`), não o Guilty: saem mesmo se
ele já tiver morrido. Nenhum `draw` usa `random` (a simulação continua determinística)."""
import math
import random
from functools import lru_cache

import pygame

from source.feats.particulas import emitir_leque, preparar
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.utils.fonts import carregar_fonte
from source.utils.superficies import SUPERFICIE_VAZIA, camada_alpha, silhueta_de

from .config import CFG

V2 = pygame.math.Vector2
FONTE = ('assets', 'fonts', 'cinzel', 'CinzelDecorative-Regular.otf')

FAISCAS_SENTINELA = ((255, 245, 190), (255, 205, 90), (255, 255, 255))
FAISCAS_SUPER = ((255, 200, 40), (255, 225, 110), (255, 160, 0))
FAISCAS_LUZ = ((60, 190, 255), (160, 235, 255), (20, 110, 255), (255, 255, 255))
FAISCAS_BARREIRA = (CFG.barreira_cor, (150, 220, 255), (255, 255, 255))
FAISCAS_TELEPORTE = ((255, 235, 120), (255, 200, 60), (255, 255, 220))
FAGULHAS_ACERTO = ((255, 90, 40), (255, 160, 60), (255, 230, 150), (220, 30, 30))
TAMANHOS_FAGULHA = (2, 3, 4)
_SORTEIO_VFX = random.Random()      # só visual: não mexe na sequência da simulação
POEIRA_FLOOD = ((84, 82, 34), (110, 95, 45), (70, 60, 30), (60, 78, 34), (130, 115, 60))


# ── Partículas ───────────────────────────────────────────────────────────────
def faiscas(posicao, quantidade, cores, velocidade=(120, 340), duracao_ms=(220, 480), tamanhos=(2, 3, 5)):
    emitir_leque(posicao, V2(1, 0), quantidade, cores, tamanhos, 360, velocidade, duracao_ms)


def impacto_da_chuva(aviso):
    faiscas(aviso.posicao, 14, FAISCAS_SENTINELA)
    aviso.game.camera.shake(intensidade=CFG.shake_chuva)


def impacto_da_super(aviso):
    faiscas(aviso.posicao, 30, FAISCAS_SUPER, velocidade=(150, 460), duracao_ms=(300, 600), tamanhos=(3, 4, 6))
    aviso.game.camera.shake(intensidade=CFG.shake_super)


def impacto_do_flood(aviso):
    """Nuvem de poeira: um terço é a onda que sai do centro; o resto nasce espalhado por toda a área
    da artilharia (densidade uniforme) e fica no ar."""
    onda = CFG.flood_poeira // 3
    emitir_leque(aviso.posicao, V2(1, 0), onda, POEIRA_FLOOD, (6, 9, 12), 360, (280, 620), (500, 1000))
    for _ in range(CFG.flood_poeira - onda):
        fora = V2(1, 0).rotate(random.uniform(0, 360))
        ponto = aviso.posicao + fora * (aviso.cfg.raio_explosao * 1.1 * math.sqrt(random.random()))
        emitir_leque(ponto, fora, 1, POEIRA_FLOOD, (6, 9, 12, 16), 80, (20, 150), (800, 1700))
    aviso.game.camera.shake(intensidade=CFG.shake_flood, duracao=400)


def impacto_da_luz(aviso, shake):
    faiscas(aviso.posicao, 28, FAISCAS_LUZ, velocidade=(180, 560), duracao_ms=(250, 550), tamanhos=(3, 4, 6))
    aviso.game.camera.shake(intensidade=shake)


# ── Imagens prontas ──────────────────────────────────────────────────────────
NIVEIS_BRILHO = 8


@lru_cache(maxsize=None)
def imagens_do_brilho():
    """Halo azul em NIVEIS_BRILHO intensidades (para somar na tela, fundo preto)."""
    raio = CFG.brilho_raio
    niveis = []
    for nivel in range(NIVEIS_BRILHO):
        forca = 0.45 + 0.55 * nivel / (NIVEIS_BRILHO - 1)
        imagem = pygame.Surface((raio * 2, raio * 2))
        for r in range(raio, 0, -2):
            queda = (1 - r / raio) ** 1.8 * forca
            pygame.draw.circle(imagem, [round(c * queda) for c in CFG.brilho_cor], (raio, raio), r)
        niveis.append(imagem)
    return tuple(niveis)


@lru_cache(maxsize=None)
def imagem_da_barreira():
    """Bolha translúcida, mais densa na borda (o anel é da EnergyAura)."""
    raio = CFG.barreira_raio
    imagem = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
    for r in range(raio, 0, -2):
        pygame.draw.circle(imagem, (*CFG.barreira_cor, round(14 + 120 * (r / raio) ** 5)), (raio, raio), r)
    for espessura, alpha in ((7, 120), (3, 230)):
        pygame.draw.circle(imagem, (150, 225, 255, alpha), (raio, raio), raio, espessura)
    return imagem


@lru_cache(maxsize=None)
def imagem_da_esfera(azul):
    """Esfera metálica cinza-escura; `azul` = acesa, prestes a disparar."""
    raio, halo = 17, 14
    centro = raio + halo
    imagem = pygame.Surface((centro * 2, centro * 2), pygame.SRCALPHA)
    if azul:
        for r in range(centro, raio, -2):
            alpha = round(110 * (1 - (r - raio) / halo))
            pygame.draw.circle(imagem, (*CFG.armadilha_cor, alpha), (centro, centro), r)
    escura, clara = ((10, 60, 130), (120, 215, 255)) if azul else ((28, 30, 34), (120, 126, 134))
    for r in range(raio, 0, -1):      # luz vinda do alto à esquerda
        t = (1 - r / raio) ** 0.8
        cor = [round(e + (c - e) * t) for e, c in zip(escura, clara)]
        desvio = round((raio - r) * 0.45)
        pygame.draw.circle(imagem, (*cor, 255), (centro - desvio, centro - desvio), r)
    pygame.draw.circle(imagem, (12, 13, 15, 255), (centro, centro), raio, 2)
    pygame.draw.line(imagem, (200, 240, 255, 255) if azul else (60, 64, 70, 255),
                     (centro - raio + 3, centro + 3), (centro + raio - 4, centro + 3), 2)
    return imagem


QUADROS_TELEPORTE = 18
TAMANHO_TELEPORTE = (220, 260)


@lru_cache(maxsize=None)
def quadros_do_teleporte():
    """Anéis dourados empilhados que sobem em volta dele, com um clarão e uma coluna de luz. Pintados no
    dobro do tamanho e reduzidos (borda suave), 1× por execução."""
    largura, altura = TAMANHO_TELEPORTE
    quadros = []
    for q in range(QUADROS_TELEPORTE):
        t = q / (QUADROS_TELEPORTE - 1)
        grande = pygame.Surface((largura * 2, altura * 2), pygame.SRCALPHA)
        cx, cy = largura, altura
        # Coluna de luz e clarão: crescem até o meio e somem
        pico = math.sin(math.pi * t) ** 1.5
        for i in range(10, 0, -1):
            meia = max(1, round(i * 9 * (0.4 + 0.6 * pico)))
            pygame.draw.ellipse(grande, (255, 215, 100, round(120 * pico * (11 - i) / 10)),
                                (cx - meia, cy - altura * 0.8, meia * 2, altura * 1.6))
        clarao = max(0.0, 1 - abs(t - 0.45) / 0.3)
        luz = pygame.Surface((360, 360), pygame.SRCALPHA)
        for i in range(30, 0, -1):
            alpha = round(235 * clarao * ((31 - i) / 30) ** 1.6)
            pygame.draw.circle(luz, (255, 245, 190, alpha), (180, 180), round(i * 6 * (0.5 + 0.5 * clarao)))
        grande.blit(luz, (cx - 180, cy - 180))
        # Anéis: cada um nasce um pouco depois do de baixo, abre, sobe e fecha
        for i in range(7):
            vida = (t - i * 0.07) / 0.55
            if not 0 < vida < 1:
                continue
            forca = math.sin(math.pi * vida)
            rx = round((70 + 100 * math.sin(math.pi * (0.25 + 0.6 * vida))) * (1 - 0.04 * i))
            ry = round(rx * 0.2)
            y = round(cy + 170 - i * 52 - 60 * vida)
            base = (255, 232, 110) if i % 2 else (255, 190, 30)
            for espessura, alpha, cor in ((26, 55, base), (16, 110, base), (8, 235, base), (3, 255, (255, 255, 225))):
                anel = pygame.Surface((rx * 2 + espessura, ry * 2 + espessura), pygame.SRCALPHA)
                pygame.draw.ellipse(anel, (*cor, round(alpha * forca)), anel.get_rect(), espessura)
                grande.blit(anel, anel.get_rect(center=(cx, y)))
        quadros.append(pygame.transform.smoothscale(grande, TAMANHO_TELEPORTE))
    return tuple(quadros)


# ── Sprites de efeito ────────────────────────────────────────────────────────
class TeleporteVFX(pygame.sprite.Sprite):
    """O clarão dourado do teleporte (um na partida, outro na chegada)."""
    DURACAO_MS = 420

    def __init__(self, posicao):
        super().__init__(entity_manager.all_sprites)
        self.quadros = quadros_do_teleporte()
        self.nascimento = relogio.agora()
        self.image = SUPERFICIE_VAZIA     # o draw é próprio
        self.rect = pygame.Rect((0, 0), TAMANHO_TELEPORTE)
        self.rect.center = (round(posicao[0]), round(posicao[1]))
        faiscas(posicao, 22, FAISCAS_TELEPORTE, velocidade=(60, 260), duracao_ms=(300, 650))

    @property
    def progresso(self):
        return (relogio.agora() - self.nascimento) / self.DURACAO_MS

    def update(self, delta_time):
        if self.progresso >= 1:
            self.kill()

    def draw(self, tela, deslocamento):
        quadro = self.quadros[min(QUADROS_TELEPORTE - 1, int(self.progresso * QUADROS_TELEPORTE))]
        tela.blit(quadro, (self.rect.x - deslocamento.x, self.rect.y - deslocamento.y))


class FeixeDoCeu(pygame.sprite.Sprite):
    """Coluna azul que despenca do topo da tela até o chão, com descargas em volta."""
    QUEDA_MS = 60
    CAMADAS = ((1.0, (0, 80, 255, 60)), (0.72, (0, 130, 255, 110)), (0.45, (80, 200, 255, 190)),
               (0.2, (255, 255, 255, 255)))

    def __init__(self, posicao, raio):
        super().__init__(entity_manager.all_sprites)
        self.posicao = V2(posicao)
        self.meia_largura = 26 + raio * 0.2
        self.nascimento = relogio.agora()
        self.image = SUPERFICIE_VAZIA     # o draw é próprio
        self.rect = self.image.get_rect(center=self.posicao)

    def update(self, delta_time):
        if relogio.agora() - self.nascimento >= CFG.luz_raio_ms:
            self.kill()

    def draw(self, tela, deslocamento):
        agora = relogio.agora()
        idade = agora - self.nascimento
        x, chao = self.posicao.x - deslocamento.x, self.posicao.y - deslocamento.y
        fim = chao * min(1.0, idade / self.QUEDA_MS)
        fecha = max(0.0, 1 - max(0, idade - self.QUEDA_MS) / (CFG.luz_raio_ms - self.QUEDA_MS))
        meia = self.meia_largura * (0.25 + 0.75 * fecha) * (1 + 0.08 * math.sin(agora * 0.09))
        margem = int(meia * 1.6) + 4
        camada, area = camada_alpha(tela, (int(x) - margem, 0, margem * 2, max(0, int(fim)) + margem))
        if camada is None:
            return
        for fracao, (r, g, b, alpha) in self.CAMADAS:
            m = meia * fracao
            pygame.draw.rect(camada, (r, g, b, round(alpha * (0.35 + 0.65 * fecha))), (x - m, 0, m * 2, fim))
            pygame.draw.ellipse(camada, (r, g, b, alpha), (x - m * 1.5, fim - m * 0.45, m * 3, m * 0.9))
        for lado in (-1, 1):              # descargas em ziguezague, tremendo
            pontos = [(x + lado * meia * (0.75 + 0.5 * math.sin(agora * 0.05 + i * 2.4 + lado)), fim * i / 9)
                      for i in range(10)]
            pygame.draw.lines(camada, (170, 235, 255, round(230 * fecha)), False, pontos, 2)
        tela.blit(camada, area.topleft, area)


# ── No próprio Guilty ────────────────────────────────────────────────────────
class GuiltyVFX:
    def iniciar_vfx(self):
        # Tudo pintado no spawn, não no 1º uso
        imagens_do_brilho()
        imagem_da_barreira()
        quadros_do_teleporte()
        for azul in (False, True):
            imagem_da_esfera(azul)
        for quadros in self.sprites.values():   # pisque vermelho do acerto da luz
            for quadro in quadros:
                silhueta_de(quadro, CFG.acerto_pisca_cor)
        preparar(FAGULHAS_ACERTO, TAMANHOS_FAGULHA)
        self._contador = (None, None, None)     # (quantidade, sombra, texto)
        self._acerto_em = None                  # quando a luz o feriu pela última vez (pisque vermelho)

    @property
    def flutuacao(self):
        """Sobe e desce no ar (só o desenho e a origem dos feixes)."""
        return CFG.flutuacao_px * math.sin(relogio.agora() * 2 * math.pi / CFG.flutuacao_ms)

    def draw(self, tela, deslocamento):
        x = self.rect.centerx - deslocamento.x
        y = self.rect.centery - deslocamento.y + self.flutuacao
        raio = CFG.brilho_raio
        if not tela.get_rect().colliderect(x - raio, y - raio, raio * 2, raio * 2):
            return
        if self.alpha_atual > 0:
            pulso = 0.75 + 0.25 * math.sin(relogio.agora() * 2 * math.pi / CFG.brilho_periodo_ms)
            nivel = round(pulso * self.alpha_atual / 255 * (NIVEIS_BRILHO - 1))
            tela.blit(imagens_do_brilho()[nivel], (x - raio, y - raio), special_flags=pygame.BLEND_RGB_ADD)
        tela.blit(self.image, (x - self.rect.width / 2, y - self.rect.height / 2))
        self._desenhar_pisque_do_acerto(tela, x, y)
        if self.barreira_ativa:
            # No centro do corpo, sem flutuar: é o círculo que barra de verdade
            tela.blit(imagem_da_barreira(), (self.rect.centerx - deslocamento.x - CFG.barreira_raio,
                                             self.rect.centery - deslocamento.y - CFG.barreira_raio))

    def efeito_da_barreira(self):
        """A barreira subiu ou caiu: coroa de faíscas e tremor."""
        for i in range(24):
            direcao = V2(1, 0).rotate(i * 15)
            emitir_leque(self.posicao + direcao * CFG.barreira_raio, direcao, 2, FAISCAS_BARREIRA, (3, 4, 6), 60,
                         (80, 320), (300, 650))
        self.game.camera.shake(intensidade=CFG.shake_barreira, duracao=350)

    def efeito_do_acerto(self):
        """A própria luz o feriu: faíscas fortes saindo dele, fagulhas quentes caindo e o pisque vermelho."""
        faiscas(self.posicao, 40, FAISCAS_LUZ, velocidade=(160, 520), duracao_ms=(300, 700), tamanhos=(3, 5, 7))
        centro = V2(self.posicao.x, self.posicao.y + self.flutuacao)
        emitir_leque(centro, V2(0, -1), 22, FAGULHAS_ACERTO, TAMANHOS_FAGULHA, 300, (90, 260), (380, 800),
                     gravidade=420, sorteio=_SORTEIO_VFX)
        self._acerto_em = relogio.agora()

    def _desenhar_pisque_do_acerto(self, tela, x, y):
        """Silhueta vermelha por cima do corpo, acesa metade de cada período, enquanto dura o pisque."""
        if self._acerto_em is None:
            return
        idade = relogio.agora() - self._acerto_em
        if idade >= CFG.acerto_pisca_ms:
            self._acerto_em = None
            return
        if (idade // (CFG.acerto_pisca_periodo_ms / 2)) % 2:
            return
        silhueta = silhueta_de(self.image, CFG.acerto_pisca_cor)
        silhueta.set_alpha(round(CFG.acerto_pisca_alpha * (1 - 0.5 * idade / CFG.acerto_pisca_ms)))
        tela.blit(silhueta, (x - self.rect.width / 2, y - self.rect.height / 2))

    # ------------------------------------------------------------ HUD
    def hud_draw(self, tela):
        """Fase 1, barreira de pé: quantas sentinelas faltam (chamado pelo HUD)."""
        if self.fase != 1 or not self.barreira_ativa:
            return
        feitas, total = self.sentinelas_derrotadas, CFG.sentinelas_para_cair
        if self._contador[0] != feitas:
            fonte = carregar_fonte(FONTE, 22)
            texto = f'SENTINELAS DERROTADAS  {feitas} / {total}'
            self._contador = (feitas, fonte.render(texto, True, (0, 0, 0)),
                              fonte.render(texto, True, (150, 220, 255)))
        _, sombra, texto = self._contador
        destino = texto.get_rect(center=(tela.get_width() // 2, 64))
        painel = pygame.Rect(0, 0, 470, 62)
        painel.center = (tela.get_width() // 2, 71)
        camada, area = camada_alpha(tela, painel)
        pygame.draw.rect(camada, (4, 14, 26, 190), painel, border_radius=8)
        pygame.draw.rect(camada, (*CFG.barreira_cor, 200), painel, 2, border_radius=8)
        tela.blit(camada, area.topleft, area)
        tela.blit(sombra, destino.move(2, 2))
        tela.blit(texto, destino)
        barra = pygame.Rect(0, 0, 300, 6)
        barra.center = (tela.get_width() // 2, 86)
        pygame.draw.rect(tela, (10, 25, 40), barra)
        pygame.draw.rect(tela, CFG.barreira_cor, (*barra.topleft, round(barra.width * feitas / total), barra.height))
        pygame.draw.rect(tela, (150, 220, 255), barra, 1)
