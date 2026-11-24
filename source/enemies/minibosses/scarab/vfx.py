"""Efeitos visuais do Scarab: terra dos golpes, faíscas, núcleo pulsando, barras das patas, fumaça e arcos
da sobrecarga e as explosões do colapso. As imagens são pintadas 1× (no spawn).

Nenhum `draw` usa `random` (a simulação continua determinística)."""
import math
import random
from functools import lru_cache

import pygame

from source.feats.particulas import emitir, emitir_leque, imagem_pixel, preparar
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.utils.superficies import SUPERFICIE_VAZIA, camada_alpha, silhueta_de

from . import corpo
from .config import CASCO, CFG, ESCOTILHAS, NUCLEO, PATAS_VULNERAVEIS, PES, VARIANTES

V2 = pygame.math.Vector2
POR_CIMA = 2000                     # px abaixo do ponto, na ordem de desenho

TERRA = ((124, 96, 62), (96, 74, 48), (150, 122, 84), (76, 60, 42), (168, 142, 104))
FAISCAS_CURTO = ((150, 255, 170), (90, 255, 120), (255, 190, 90), (255, 255, 255))
FAISCAS_METAL = ((255, 220, 150), (200, 190, 230), (255, 255, 255))
FAISCAS_NUCLEO = ((120, 255, 110), (255, 190, 60), (255, 255, 220))
FOGO = ((255, 240, 190), (255, 180, 60), (255, 110, 25), (140, 60, 30))
FUMACA = ((40, 40, 44), (58, 58, 62), (30, 30, 34))
LUZ_ESCOTILHA = ((190, 110, 255), (140, 70, 240), (230, 190, 255))

COR_BRILHO = (255, 60, 40)          # a pata que o jogador alcança
TERRA_P, TERRA_M, TERRA_G = (7, 10, 13), (8, 12, 16), (9, 13, 17, 22)
FAISCA_P, FAISCA_M, FAISCA_G = (2, 3, 4), (4, 6, 8), (5, 8, 11)
TAMANHOS_FUMACA = (18, 26, 34)

BRILHO_ALPHA = (20, 85)
BRILHO_PERIODO_MS = 700
BARRA_PATA = (132, 13)


# ── Partículas ───────────────────────────────────────────────────────────────
def terra(posicao, quantidade, raio, velocidade, duracao_ms, tamanhos=TERRA_P):
    """Um anel de terra que sai da borda para fora e o resto brotando por toda a área."""
    posicao = V2(posicao)
    anel = quantidade // 3
    for _ in range(anel):
        fora = V2(1, 0).rotate(random.uniform(0, 360))
        emitir_leque(posicao + fora * raio * 0.75, fora, 1, TERRA, tamanhos, 40, velocidade, duracao_ms)
    for _ in range(quantidade - anel):
        fora = V2(1, 0).rotate(random.uniform(0, 360))
        ponto = posicao + fora * (raio * math.sqrt(random.random()))
        emitir_leque(ponto, fora, 1, TERRA, tamanhos, 110, (velocidade[0] * 0.3, velocidade[1] * 0.6), duracao_ms)


def faiscas(posicao, quantidade, cores, velocidade=(140, 420), duracao_ms=(220, 520), tamanhos=FAISCA_M):
    """Por cima do Scarab (que cobre quase tudo que está perto dele)."""
    emitir_leque(posicao, V2(1, 0), quantidade, cores, tamanhos, 360, velocidade, duracao_ms,
                 y_desenho=posicao[1] + POR_CIMA)


# ── Imagens prontas ──────────────────────────────────────────────────────────
NIVEIS_BRILHO = 8
RAIO_BRILHO = 150


@lru_cache(maxsize=None)
def imagens_do_nucleo():
    """Halo verde com miolo laranja em NIVEIS_BRILHO intensidades (para somar na tela, fundo preto)."""
    niveis = []
    for nivel in range(NIVEIS_BRILHO):
        forca = 0.35 + 0.65 * nivel / (NIVEIS_BRILHO - 1)
        imagem = pygame.Surface((RAIO_BRILHO * 2, RAIO_BRILHO * 2))
        for r in range(RAIO_BRILHO, 0, -2):
            t = r / RAIO_BRILHO
            verde, laranja = (1 - t) ** 1.7, max(0.0, 1 - t / 0.38) ** 1.4
            cor = (60 * verde + 225 * laranja, 255 * verde, 70 * verde + 20 * laranja)
            pygame.draw.circle(imagem, [min(255, round(c * forca)) for c in cor], (RAIO_BRILHO, RAIO_BRILHO), r)
        niveis.append(imagem)
    return tuple(niveis)


QUADROS_EXPLOSAO = 10


@lru_cache(maxsize=None)
def quadros_da_explosao(raio):
    """Bola de fogo em blocos: clarão branco, laranja e fumaça rala."""
    bloco = 6
    quadros = []
    sorteio = random.Random(raio)
    celulas = [(x, y, sorteio.random()) for x in range(0, raio * 2, bloco) for y in range(0, raio * 2, bloco)]
    for q in range(QUADROS_EXPLOSAO):
        t = q / (QUADROS_EXPLOSAO - 1)
        imagem = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
        aberto = raio * (0.35 + 0.65 * math.sqrt(t))
        for x, y, ruido in celulas:
            d = math.hypot(x + bloco / 2 - raio, y + bloco / 2 - raio) / aberto
            calor = 1.15 - d * 0.9 - t * 0.85 + (ruido - 0.5) * 0.36
            if d > 1 - (ruido * 0.22) or calor < -0.35:
                continue
            if calor > 0.75:
                cor = (255, 250, 225, 255)
            elif calor > 0.42:
                cor = (255, 190, 70, 245)
            elif calor > 0.16:
                cor = (255, 105, 25, 225)
            elif calor > -0.05:
                cor = (120, 52, 30, 170)
            else:
                cor = (44, 42, 44, 110)
            imagem.fill(cor, (x, y, bloco, bloco))
        quadros.append(imagem)
    return tuple(quadros)


RAIOS_EXPLOSAO = (48, 72, 104)


class ExplosaoVFX(pygame.sprite.Sprite):
    """Só visual. Sai por cima do Scarab."""
    DURACAO_MS = 460

    def __init__(self, posicao, raio):
        super().__init__(entity_manager.all_sprites)
        self.quadros = quadros_da_explosao(raio)
        self.nascimento = relogio.agora()
        self.image = self.quadros[0]
        self.rect = self.image.get_rect(center=(round(posicao[0]), round(posicao[1])))
        self.y_desenho = self.rect.centery + POR_CIMA

    def update(self, delta_time):
        progresso = (relogio.agora() - self.nascimento) / self.DURACAO_MS
        if progresso >= 1:
            self.kill()
            return
        self.image = self.quadros[int(progresso * QUADROS_EXPLOSAO)]


class OndaDeChoqueVFX(pygame.sprite.Sprite):
    """O anel da detonação, abrindo até `raio`. Só visual (o dano é da artilharia)."""
    DURACAO_MS = 620

    def __init__(self, posicao, raio):
        super().__init__(entity_manager.all_sprites)
        self.posicao = V2(posicao)
        self.raio = raio
        self.nascimento = relogio.agora()
        self.image = SUPERFICIE_VAZIA     # o draw é próprio
        self.rect = self.image.get_rect(center=self.posicao)
        self.y_desenho = self.rect.centery + POR_CIMA

    @property
    def progresso(self):
        return (relogio.agora() - self.nascimento) / self.DURACAO_MS

    def update(self, delta_time):
        if self.progresso >= 1:
            self.kill()

    def draw(self, tela, deslocamento):
        t = min(1.0, self.progresso)
        centro = self.posicao - deslocamento
        raio = max(8, round(self.raio * (1 - (1 - t) ** 2.2)))
        camada, area = camada_alpha(tela, (centro.x - raio - 4, centro.y - raio - 4, raio * 2 + 8, raio * 2 + 8))
        if camada is None:
            return
        forca = 1 - t
        if t < 0.35:
            pygame.draw.circle(camada, (235, 255, 235, round(230 * (1 - t / 0.35))), centro, round(raio * 0.8))
        for espessura, cor, alpha in ((90, (40, 200, 80), 60), (46, (90, 255, 120), 130), (16, (230, 255, 235), 240)):
            pygame.draw.circle(camada, (*cor, round(alpha * forca)), centro, raio,
                               max(1, round(espessura * (0.4 + 0.6 * forca))))
        tela.blit(camada, area.topleft, area)


# ── No próprio Scarab ────────────────────────────────────────────────────────
class ScarabVFX:
    def iniciar_vfx(self):
        corpo.preparar(COR_BRILHO)
        preparar(TERRA, {*TERRA_P, *TERRA_M, *TERRA_G})
        preparar((*FAISCAS_CURTO, *FAISCAS_METAL, *FAISCAS_NUCLEO, *FOGO, *LUZ_ESCOTILHA),
                 {*FAISCA_P, *FAISCA_M, *FAISCA_G})
        preparar(FUMACA, TAMANHOS_FUMACA)
        imagens_do_nucleo()
        for raio in RAIOS_EXPLOSAO:
            quadros_da_explosao(raio)
        self._proximo_efeito = {}         # nome -> ms: limita as partículas dos efeitos contínuos

    def _pode(self, nome, intervalo_ms):
        """True no máximo uma vez a cada `intervalo_ms` de jogo."""
        agora = relogio.agora()
        if agora < self._proximo_efeito.get(nome, 0):
            return False
        self._proximo_efeito[nome] = agora + intervalo_ms
        return True

    def tremer(self, intensidade, duracao_ms):
        """O tremor mais forte ganha (o `camera.shake` puro vale o último): o feixe treme a cada frame e
        não pode apagar o do stomp."""
        camera = self.game.camera
        if relogio.agora() < camera.shake_timer and camera.shake_intensidade > intensidade:
            return
        camera.shake(intensidade=intensidade, duracao=duracao_ms)

    def _ponto_do_casco(self):
        x0, y0, x1, y1 = CASCO
        desce = 140 if self.pose == 'caido' else 0
        return self.no_mundo((random.uniform(x0, x1), random.uniform(y0, y1) + desce))

    # ------------------------------------------------------------ golpes
    def impacto_do_passo(self, pata):
        terra(pata.posicao, CFG.terra_passo, 90, (70, 230), (450, 850))
        self.tremer(*CFG.shake_passo)

    def impacto_da_sismica(self, posicao, raio):
        terra(posicao, CFG.terra_sismica, raio, (150, 480), (600, 1200), TERRA_M)
        self.tremer(*CFG.shake_sismica)

    def impacto_do_stomp(self, raio):
        terra(self.centro_chao, CFG.terra_stomp, raio * 1.15, (220, 640), (800, 1700), TERRA_G)
        self.tremer(*CFG.shake_stomp)

    # ------------------------------------------------------------ acertos
    def efeito_na_pata(self, pata):
        if self._pode('pata', 70):
            x, y = PES[pata.nome]
            faiscas(self.no_mundo((x, y - random.uniform(60, 260))), 5, FAISCAS_METAL, (100, 300), (160, 340), FAISCA_P)

    def efeito_na_carapaca(self):
        """Ricochete: poucas faíscas, do lado do jogador."""
        if self._pode('carapaca', 110):
            faiscas(self.posicao + (self.jogador.posicao - self.posicao) * 0.35, 3, FAISCAS_METAL, (80, 220),
                    (120, 260), FAISCA_P)

    def efeito_no_nucleo(self):
        if self._pode('nucleo', 60):
            faiscas(self.no_mundo(NUCLEO), 7, FAISCAS_NUCLEO)

    # ------------------------------------------------------------ queda e fases
    def efeito_da_queda(self, pata):
        faiscas(pata.posicao - V2(0, 130), 60, FAISCAS_CURTO, (160, 560), (350, 800), FAISCA_G)
        terra(self.centro_chao, CFG.terra_queda, 380, (120, 420), (600, 1300), TERRA_M)
        ExplosaoVFX(pata.posicao - V2(0, 120), RAIOS_EXPLOSAO[1])
        self.tremer(*CFG.shake_queda)

    def efeito_ao_erguer(self):
        terra(self.centro_chao, CFG.terra_queda // 2, 340, (90, 300), (500, 1000))
        self.tremer(CFG.shake_queda[0] * 0.4, 300)

    def entrar_na_fase(self):
        """A carapaça racha (a arte muda): estilhaços por todo o casco."""
        for _ in range(8):
            faiscas(self._ponto_do_casco(), 9, FAISCAS_CURTO, (140, 460), (300, 700))
        self.tremer(12, 400)

    def efeito_da_sobrecarga(self):
        for _ in range(4):
            ExplosaoVFX(self._ponto_do_casco(), RAIOS_EXPLOSAO[0])
        self.tremer(18, 700)

    def efeito_da_escotilha(self):
        if self._pode('escotilha', 60):
            for ponto in ESCOTILHAS:
                emitir_leque(self.no_mundo(ponto), V2(0, 1), 3, LUZ_ESCOTILHA, FAISCA_M, 70, (60, 220), (300, 600))

    def efeito_do_desembarque(self, posicao):
        faiscas(posicao, 14, LUZ_ESCOTILHA, (60, 240), (300, 600))

    # ------------------------------------------------------------ colapso
    def explosao_em_cadeia(self, progresso):
        ponto = self._ponto_do_casco()
        ExplosaoVFX(ponto, random.choice(RAIOS_EXPLOSAO))
        faiscas(ponto, 8, FOGO, (120, 420), (300, 700))
        self.tremer(8 + 18 * progresso, 160)

    def efeito_da_detonacao(self, raio):
        OndaDeChoqueVFX(self.centro_chao, raio)
        for _ in range(14):
            ExplosaoVFX(self._ponto_do_casco(), RAIOS_EXPLOSAO[2])
        faiscas(self.centro_chao - V2(0, 120), 160, FOGO, (200, 900), (600, 1400), FAISCA_G)
        terra(self.centro_chao, 260, raio * 0.6, (260, 760), (900, 1800), TERRA_G)
        self.tremer(*CFG.shake_detonacao)

    # ------------------------------------------------------------ por frame (só partículas)
    def atualizar_vfx(self, agora):
        if self.desabado and self.pata_quebrada is not None and self._pode('curto', 90):
            faiscas(self.pata_quebrada.posicao - V2(0, random.uniform(40, 200)), 5, FAISCAS_CURTO, (80, 300), (200, 480))
        if self.feixe_estado == 'disparo' and self._pode('feixe', 30):
            faiscas(self.feixe.mira_atual, 4, FAISCAS_CURTO, (120, 420), (200, 480))
        if self.critico and self._pode('fumaca', 70):
            emitir(self._ponto_do_casco(), imagem_pixel(random.choice(FUMACA), random.choice(TAMANHOS_FUMACA), 'circulo'),
                   (random.uniform(-25, 25), random.uniform(-120, -60)), random.uniform(1100, 2000),
                   y_desenho=self.y_desenho + POR_CIMA)

    # ------------------------------------------------------------ desenho
    def draw(self, tela, deslocamento):
        x, y = int(self.rect.x - deslocamento.x), int(self.rect.y - deslocamento.y)
        if self.morrendo:                       # sacode cada vez mais até detonar
            agora = relogio.agora()
            x += round(5 * math.sin(agora * 0.11))
            y += round(4 * math.sin(agora * 0.17))
        if not tela.get_rect().colliderect(x, y, self.rect.width, self.rect.height):
            return
        corpo.desenhar(tela, x, y, self)
        if self.pose == 'em_pe' and not self.morrendo:
            self._brilho_da_pata(tela, x, y)
        if self.nucleo_exposto:
            self._brilho_do_nucleo(tela, deslocamento)
        if self.critico or self.morrendo:
            self._arcos(tela, x, y)

    def _brilho_da_pata(self, tela, x, y):
        """A pata que o jogador alcança de onde está pulsa em vermelho (como as costas do Hunter)."""
        pata = self.pata_exposta
        if pata is None:
            return
        imagem, rx, ry = corpo.recorte(VARIANTES[0], f'em_pe_{pata.nome}', self.animador.lado)
        sil = silhueta_de(imagem, COR_BRILHO)
        minimo, maximo = BRILHO_ALPHA
        onda = 0.5 + 0.5 * math.sin(relogio.agora() * 2 * math.pi / BRILHO_PERIODO_MS)
        sil.set_alpha(round(minimo + (maximo - minimo) * onda))
        sobe = pata.extra_y + (self.impulso_y if pata.nome == 'centro' else 0)
        tela.blit(sil, (x + rx, y + ry - round(sobe)))

    def _brilho_do_nucleo(self, tela, deslocamento):
        centro = self.no_mundo(NUCLEO) - deslocamento
        onda = 0.5 + 0.5 * math.sin(relogio.agora() * 0.012)
        imagem = imagens_do_nucleo()[round(onda * (NIVEIS_BRILHO - 1))]
        tela.blit(imagem, (centro.x - RAIO_BRILHO, centro.y - RAIO_BRILHO), special_flags=pygame.BLEND_RGB_ADD)

    def _arcos(self, tela, x, y):
        """Arcos elétricos verdes correndo pela carapaça; mudam de lugar a cada 120 ms."""
        agora = relogio.agora()
        x0, y0, x1, y1 = CASCO
        desce = 140 if self.pose == 'caido' else 0
        for k in range(3):
            semente = int(agora // 120) * 7 + k * 31
            if semente % 3 == 0:
                continue
            ax = x0 + (semente * 97) % (x1 - x0)
            ay = y0 + (semente * 61) % (y1 - y0) + desce
            pontos = []
            for i in range(7):
                px = ax + i * 22 * (1 if semente % 2 else -1)
                py = ay + 26 * math.sin(semente * 1.3 + i * 2.1 + agora * 0.02)
                pontos.append((x + (px if self.animador.lado == 'left' else corpo.espelhar_x(px)), y + py))
            pygame.draw.lines(tela, (40, 200, 70), False, pontos, 5)
            pygame.draw.lines(tela, (215, 255, 220), False, pontos, 2)

    def draw_laser(self, tela, deslocamento):
        if self.feixe_estado == 'disparo':
            self.feixe.draw(tela, deslocamento)
        elif self.feixe_estado == 'carga':
            restante = self.feixe_fim - relogio.agora()
            self.feixe.draw_carga(tela, deslocamento, 1 - max(0, restante) / CFG.feixe.carga_ms)

    def draw_extras(self, tela, deslocamento):
        """A vida de cada pata, por cima de tudo; caído, o tempo que o núcleo ainda fica aberto."""
        if self.morrendo:
            return
        if self.desabado:
            if self.nucleo_exposto:
                restante = (self.nucleo_ate - relogio.agora()) / CFG.exposto_ms
                centro = self.no_mundo(NUCLEO) - deslocamento
                self._barra(tela, centro.x, centro.y - 92, restante, (120, 255, 110), True)
            return
        exposta = self.pata_exposta
        for nome in PATAS_VULNERAVEIS:
            pata = self.patas[nome]
            pe = pata.posicao - deslocamento
            razao = pata.vida / pata.vida_maxima
            cor = (90, 230, 110) if razao > 0.5 else (245, 165, 50) if razao > 0.25 else (240, 60, 45)
            self._barra(tela, pe.x, pe.y + 26, razao, cor, pata is exposta)

    @staticmethod
    def _barra(tela, x, y, razao, cor, destaque):
        largura, altura = BARRA_PATA
        fundo = pygame.Rect(round(x - largura / 2), round(y), largura, altura)
        pygame.draw.rect(tela, (10, 10, 14), fundo)
        cheio = round((largura - 4) * max(0.0, min(1.0, razao)))
        if cheio > 0:
            pygame.draw.rect(tela, cor, (fundo.x + 2, fundo.y + 2, cheio, altura - 4))
        pygame.draw.rect(tela, (255, 255, 255) if destaque else (92, 88, 104), fundo, 2)
