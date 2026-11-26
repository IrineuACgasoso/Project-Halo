"""Efeitos visuais do Tartarus: a barreira gravitacional (bolha), a sobrecarga, o rugido, o capacete
descartado e a aura vermelha da Fúria, o vapor de quando está ofegante, a sombra do salto e a barra de
esquivas no topo do HUD.

Silhuetas e bolha em cache (aquecidas no spawn); por frame, só `set_alpha` e blit. Sorteio próprio
(`_SORTEIO`). Os ganchos `onda_estourou` e `ponto_do_punho_estourou` recebem o aviso, não o Tartarus."""
import math
import random

import pygame

from source.feats.particulas import emitir_leque
from source.feats.particulas.energia import preparar_energia
from source.feats.particulas.explosao import explosao_de_impacto, preparar_explosao
from source.feats.particulas.lentidao import preparar_lentidao
from source.feats.particulas.poeira import poeira_em_area, poeira_no_retangulo, preparar_poeira
from source.feats.particulas.quebra_escudo import quebra_de_escudo
from source.feats.skills.salto import desenhar_sombra
from source.systems.gameclock import relogio
from source.utils.superficies import silhueta_de

from .config import CFG

V2 = pygame.math.Vector2
_SORTEIO = random.Random()
COR_GRITO = (255, 235, 215)
COR_VORTICE = (150, 70, 255)
CORES_BARREIRA = ((120, 140, 255), (170, 120, 255), (210, 220, 255))
CORES_SOBRECARGA = ((255, 230, 120), (255, 255, 220))
CORES_FURIA = ((255, 60, 30), (255, 140, 50), (255, 220, 140))
CORES_CAPACETE = ((150, 150, 160), (110, 110, 120), (215, 180, 70), (90, 90, 100))
CORES_VAPOR = ((235, 235, 240), (205, 210, 220))
TAMANHOS = (3, 4, 6)

_BOLHAS = {}       # (largura, altura) -> Surface
_FONTE = None
_TEXTOS = {}       # (texto, cor) -> Surface


def _pulso(agora, periodo_ms, limites):
    minimo, maximo = limites
    return round(minimo + (maximo - minimo) * (0.5 + 0.5 * math.sin(agora * 2 * math.pi / periodo_ms)))


def _bolha(largura, altura):
    """A barreira: elipse translúcida com aro claro (alpha dado por `set_alpha` antes do blit)."""
    chave = (largura, altura)
    bolha = _BOLHAS.get(chave)
    if bolha is None:
        bolha = _BOLHAS[chave] = pygame.Surface(chave, pygame.SRCALPHA)
        caixa = bolha.get_rect()
        pygame.draw.ellipse(bolha, (*CFG.cor_barreira, 90), caixa)
        pygame.draw.ellipse(bolha, (190, 200, 255, 230), caixa, 4)
        pygame.draw.ellipse(bolha, (235, 240, 255, 160), caixa.inflate(-18, -18), 2)
    return bolha


def _fonte():
    global _FONTE
    if _FONTE is None:
        _FONTE = pygame.font.SysFont('Consolas', 16, bold=True)
    return _FONTE


def _texto(texto, cor):
    surf = _TEXTOS.get((texto, cor))
    if surf is None:
        surf = _TEXTOS[(texto, cor)] = _fonte().render(texto, True, cor)
    return surf


def _faiscas(posicao, direcao, quantidade, cores, abertura=360, velocidade=(120, 360), duracao_ms=(300, 600),
             gravidade=0):
    emitir_leque(posicao, direcao, quantidade, cores, TAMANHOS, abertura, velocidade, duracao_ms,
                 gravidade=gravidade, sorteio=_SORTEIO)


# ------------------------------------------------------------------ ganchos dos golpes
def onda_estourou(aviso):
    """Esmagamento Sísmico: a fissura libera a energia (a `EnergiaDoChao` cuida dela), poeira em toda a
    área, estilhaços no pé do martelo e um tremor enorme."""
    cfg = aviso.cfg
    poeira_no_retangulo(aviso.posicao, aviso.direcao, cfg.altura, cfg.largura, CFG.onda_poeira)
    explosao_de_impacto(aviso.posicao + aviso.direcao * 60, 120, 'gravidade', aviso.game, CFG.onda_shake,
                        faiscas=0.8)


def ponto_do_punho_estourou(aviso):
    """Cada ponto do Punho de Rukt: um pouco de poeira (a energia liberada é da `EnergiaDoChao`)."""
    poeira_em_area(aviso.posicao, aviso.cfg.raio_explosao * 0.6, 4)


class TartarusVFX:
    def iniciar_vfx(self):
        agora = relogio.agora()
        self._grito_ate = 0
        self._clarao_barreira_ate = 0
        self._proxima_brasa = agora
        self._proximo_vapor = agora
        self._proxima_faisca = agora
        hb = self.hitbox
        self._bolha = _bolha(round(hb.width * 2.0), round(hb.height * 1.25))
        for frames in self.sprites.values():          # silhuetas prontas no spawn, não no 1º uso
            for frame in frames:
                for cor in (COR_GRITO, CFG.cor_furia, CFG.cor_sobrecarga):
                    silhueta_de(frame, cor)
        for paleta in ('gravidade', 'vortice', 'furia'):
            preparar_energia(paleta)
        for paleta in ('fogo', 'gravidade', 'vortice', 'furia'):
            preparar_explosao(paleta)
        preparar_poeira()
        jogador = self.jogador
        preparar_lentidao(q for lado in getattr(jogador, 'sprites', {}).values() for q in lado)
        _fonte()

    # -------------------------------------------------------------- momentos
    def grito_vfx(self, ms):
        self._grito_ate = self._agora + ms
        _faiscas(self.posicao, V2(0, -1), 40, CORES_FURIA, velocidade=(200, 560), duracao_ms=(350, 750))
        self.game.camera.shake(*CFG.grito_shake)

    def barreira_caiu_vfx(self, longa=False):
        """A barreira estoura: fagulhas violeta e amarelas e um clarão (longa: tremor também)."""
        self._clarao_barreira_ate = self._agora + 300
        self.proxima_quebra_escudo = 0                 # a quebra visual sai sempre
        quebra_de_escudo(self, cores=CORES_BARREIRA, cores_destaque=CORES_SOBRECARGA)
        if longa:
            self.game.camera.shake(8, 450)

    def barreira_voltou_vfx(self):
        self._clarao_barreira_ate = self._agora + 300
        _faiscas(V2(self.posicao.x, self.rect.bottom - 30), V2(0, -1), 22, CORES_BARREIRA, 140,
                 velocidade=(100, 260), duracao_ms=(350, 650))

    def descartar_capacete_vfx(self):
        """Fúria: o capacete cerimonial voa em pedaços e uma explosão vermelha sai do corpo."""
        cabeca = V2(self.posicao.x, self.rect.top + self.rect.height * 0.18)
        _faiscas(cabeca, V2(0, -1), 26, CORES_CAPACETE, 160, velocidade=(220, 520), duracao_ms=(700, 1200),
                 gravidade=700)
        explosao_de_impacto(self.posicao, 200, 'furia', faiscas=1.2, poeira=True)

    # -------------------------------------------------------------- desenho
    def _sobrepor(self, tela, deslocamento, cor, alpha):
        sil = silhueta_de(self.quadro_original, cor)
        sil.set_alpha(alpha)
        tela.blit(sil, (self.rect.x - deslocamento.x, self.rect.y - deslocamento.y))

    def _desenhar_bolha(self, tela, deslocamento, alpha):
        bolha = self._bolha
        bolha.set_alpha(alpha)
        tela.blit(bolha, (self.hitbox.centerx - bolha.get_width() / 2 - deslocamento.x,
                          self.hitbox.centery - bolha.get_height() / 2 - deslocamento.y))

    def draw_extras(self, tela, deslocamento):
        """Chamado pelo renderer depois dos sprites."""
        if self.altura_z > 0:
            desenhar_sombra(tela, self, deslocamento, self.hitbox.width * 1.6)
        agora = relogio.agora()
        if self._furia:
            self._sobrepor(tela, deslocamento, CFG.cor_furia, _pulso(agora, CFG.furia_periodo_ms, CFG.furia_alpha))
            if agora >= self._proxima_brasa:
                self._proxima_brasa = agora + CFG.furia_brasas_ms
                pes = V2(self.posicao.x + _SORTEIO.uniform(-40, 40), self.rect.bottom - 25)
                _faiscas(pes, V2(0, -1), 2, CORES_FURIA, 40, velocidade=(60, 160), duracao_ms=(450, 800))
        if agora < self._grito_ate:
            self._sobrepor(tela, deslocamento, COR_GRITO, round(190 * (self._grito_ate - agora) / CFG.grito_ms))
        if self.ofegante and agora >= self._proximo_vapor:
            self._proximo_vapor = agora + CFG.ofegante_vapor_ms
            cabeca = V2(self.posicao.x + _SORTEIO.uniform(-15, 15), self.rect.top + self.rect.height * 0.2)
            _faiscas(cabeca, V2(0, -1), 3, CORES_VAPOR, 50, velocidade=(30, 80), duracao_ms=(600, 1000))
        clarao = agora < self._clarao_barreira_ate
        if self.barreira_ativa:
            alpha = 230 if clarao else _pulso(agora, CFG.barreira_periodo_ms, CFG.barreira_alpha)
            self._desenhar_bolha(tela, deslocamento, min(255, alpha))
        elif not self.quebra_longa:
            # sobrecarga: a bolha falha e solta faíscas (vai voltar)
            if (agora // 70) % 3 == 0:
                self._desenhar_bolha(tela, deslocamento, 70)
            if agora >= self._proxima_faisca:
                self._proxima_faisca = agora + 140
                ponto = V2(self.hitbox.center) + V2(self.hitbox.width * 0.9, 0).rotate(_SORTEIO.uniform(0, 360))
                _faiscas(ponto, ponto - V2(self.hitbox.center), 3, CORES_SOBRECARGA, 90,
                         velocidade=(80, 200), duracao_ms=(150, 300))

    # -------------------------------------------------------------- HUD
    def hud_draw(self, tela):
        """A barra de esquivas no topo (embaixo do cronômetro do Halo). Cheia, derruba a barreira; caída,
        a barra esvazia com o tempo que falta para ela voltar."""
        if self.halo is not None and self.halo.disparou_em is not None:
            return                                     # o Halo disparou: tudo some no branco
        largura, altura = 340, 12
        x = (tela.get_width() - largura) // 2
        y = 76
        meta = CFG.meta_esquivas
        if self.quebra_longa:
            inicio, fim = self._quebra
            fracao = max(0.0, min(1.0, (fim - self._agora) / max(1, fim - inicio)))
            rotulo, cor = 'BARREIRA CAÍDA', (255, 120, 50)
        else:
            fracao = self.esquivas / meta
            sobrecarga = not self.barreira_ativa
            rotulo = f'SOBRECARGA  ·  ESQUIVAS {self.esquivas}/{meta}' if sobrecarga else f'ESQUIVAS {self.esquivas}/{meta}'
            cor = CFG.cor_sobrecarga if sobrecarga else (130, 170, 255)
        pygame.draw.rect(tela, (12, 12, 24), (x - 2, y - 2, largura + 4, altura + 4))
        if fracao > 0:
            pygame.draw.rect(tela, cor, (x, y, round(largura * fracao), altura))
        if not self.quebra_longa:
            for i in range(1, meta):
                sx = x + round(largura * i / meta)
                pygame.draw.line(tela, (12, 12, 24), (sx, y), (sx, y + altura - 1), 2)
        pygame.draw.rect(tela, (200, 210, 255), (x - 2, y - 2, largura + 4, altura + 4), 1)
        texto = _texto(rotulo, cor)
        tela.blit(texto, texto.get_rect(midbottom=(tela.get_width() // 2, y - 3)))
