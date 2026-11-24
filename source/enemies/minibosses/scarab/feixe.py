"""Canhão de foco: o feixe contínuo com uma barreira mínima em volta do Scarab e o visual próprio.

A ponta persegue o jogador, mas nunca entra no círculo de `raio_sob` em volta do centro do chão: quem está
por baixo dele está coberto. Saiu da cobertura, ela volta a persegui-lo.
Nenhum `draw` usa `random` (a simulação continua determinística)."""
import math

import pygame

from source.feats.skills.continuousbeam import ContinuousBeam
from source.systems.dano import AREA, Dano
from source.systems.gameclock import relogio
from source.utils.superficies import camada_alpha
from source.utils.vetores import direcao_segura

from .config import CFG

V2 = pygame.math.Vector2

# (fração da largura, cor RGBA), de fora para dentro
CAMADAS = ((2.6, (10, 150, 40, 38)), (1.8, (20, 220, 60, 80)), (1.15, (70, 255, 100, 165)),
           (0.62, (190, 255, 195, 235)), (0.28, (255, 255, 255, 255)))
SEGMENTOS = 14


class FeixeDeFoco(ContinuousBeam):
    def __init__(self, scarab, cfg):
        super().__init__(scarab, color=cfg.cor, largura_base=cfg.largura, dano_por_segundo=cfg.dps,
                         suavizacao=cfg.suavizacao)
        self.cfg = cfg

    def comecar(self):
        """Nasce na barreira, para o lado do jogador."""
        centro = self.owner.centro_chao
        self.mira_atual = centro + direcao_segura(centro, self.game.player.posicao) * CFG.raio_sob

    def mirar(self, alvo_pos):
        centro = self.owner.centro_chao
        super().mirar(alvo_pos)
        if self.mira_atual.distance_squared_to(centro) < CFG.raio_sob ** 2:
            self.mira_atual = centro + direcao_segura(centro, self.mira_atual) * CFG.raio_sob

    def update(self, delta_time, alvo_pos):
        self.mirar(alvo_pos)
        jogador = self.game.player
        if self.owner.jogador_sob:
            return                        # coberto pelo casco
        if self.mira_atual.distance_squared_to(jogador.posicao) <= self.cfg.raio_impacto ** 2:
            jogador.receber_dano(Dano(self.dano_por_segundo * delta_time, AREA, self.owner, ignora_iframes=True))

    # ------------------------------------------------------------ desenho
    def draw(self, tela, deslocamento, origem_offset=None):
        agora = relogio.agora()
        de = self.owner.ponta_canhao - deslocamento
        ate = self.mira_atual - deslocamento
        eixo = direcao_segura(de, ate)
        normal = V2(-eixo.y, eixo.x)
        pulso = 1 + 0.10 * math.sin(agora * 0.021) + 0.05 * math.sin(agora * 0.067)
        largura = self.largura_base * pulso
        raio = self.cfg.raio_impacto * (0.85 + 0.12 * math.sin(agora * 0.033))

        margem = round(largura * 1.4 + raio * 1.5) + 4
        caixa = pygame.Rect(min(de.x, ate.x) - margem, min(de.y, ate.y) - margem,
                            abs(ate.x - de.x) + margem * 2, abs(ate.y - de.y) + margem * 2)
        camada, area = camada_alpha(tela, caixa)
        if camada is None:
            return
        # Impacto por baixo: poça de luz achatada no chão
        for fracao, (r, g, b, a) in CAMADAS[:3]:
            rx = raio * fracao * 0.75
            pygame.draw.ellipse(camada, (r, g, b, a), (ate.x - rx, ate.y - rx * 0.6, rx * 2, rx * 1.2))
        pontos = [(i / SEGMENTOS, de.lerp(ate, i / SEGMENTOS)) for i in range(SEGMENTOS + 1)]
        for fracao, cor in CAMADAS:
            cima, baixo = [], []
            for t, p in pontos:
                # Fino na boca, grosso na ponta, com pulsos de energia correndo para a frente
                meia = largura * fracao * 0.5 * (0.45 + 0.55 * t) * (1 + 0.13 * math.sin(t * 19 - agora * 0.03))
                cima.append(p + normal * meia)
                baixo.append(p - normal * meia)
            pygame.draw.polygon(camada, cor, cima + baixo[::-1])
        for k in (0, 1):                   # descargas em volta do feixe
            descarga = [p + normal * (largura * (0.9 + 0.5 * t) * math.sin(t * 31 + agora * 0.045 + k * 2.6 + i * 1.7))
                        for i, (t, p) in enumerate(pontos)]
            pygame.draw.lines(camada, (170, 255, 180, 210), False, descarga, 2)
        for fracao, cor in CAMADAS[2:]:    # clarão na boca e miolo do impacto
            pygame.draw.circle(camada, cor, de, max(1, round(largura * fracao * 0.75)))
            pygame.draw.circle(camada, cor, ate, max(1, round(raio * fracao * 0.45)))
        tela.blit(camada, area.topleft, area)

    def draw_carga(self, tela, deslocamento, progresso):
        """A esfera crescendo na boca do cano e o traço fino de mira (o aviso)."""
        agora = relogio.agora()
        de = self.owner.ponta_canhao - deslocamento
        raio = (6 + 34 * progresso) * (1 + 0.08 * math.sin(agora * 0.04))
        alcance = round(raio * 2.6) + 60
        camada, area = camada_alpha(tela, (de.x - alcance, de.y - alcance, alcance * 2, alcance * 2))
        if camada is not None:
            for fracao, cor in CAMADAS:
                pygame.draw.circle(camada, cor, de, max(1, round(raio * fracao * 0.75)))
            for i in range(10):            # fagulhas sendo sugadas
                t = 1 - ((agora * 0.0016 + i * 0.1) % 1)
                p = de + V2(raio + t * 58, 0).rotate(i * 36 + agora * 0.05)
                pygame.draw.circle(camada, (150, 255, 165, round(220 * (1 - t))), p, 3)
            tela.blit(camada, area.topleft, area)
        centro = self.owner.centro_chao
        alvo = self.game.player.posicao
        if centro.distance_squared_to(alvo) < CFG.raio_sob ** 2:
            alvo = centro + direcao_segura(centro, alvo) * CFG.raio_sob
        if int(agora / (140 - 90 * progresso)) % 2:
            pygame.draw.line(tela, (60, 210, 80), de, alvo - deslocamento, 2)
