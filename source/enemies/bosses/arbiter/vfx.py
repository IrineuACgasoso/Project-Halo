"""Efeitos visuais do Arbiter: faíscas da espada, grito, aura da fase 2, costas expostas e sombra do salto.

Silhuetas em cache por quadro (`silhueta_de`, aquecidas no spawn); por frame, só `set_alpha` e blit.
Sorteio próprio (`_SORTEIO`): o efeito não mexe na sequência da simulação. `impacto_da_espada`
recebe o aviso (gancho `ao_explodir`), não o Arbiter: sai mesmo se ele já tiver morrido."""
import math
import random

import pygame

from source.feats.particulas import emitir_leque
from source.feats.skills.salto import desenhar_sombra
from source.systems.gameclock import relogio
from source.utils.superficies import silhueta_de

from .config import CFG

V2 = pygame.math.Vector2
_SORTEIO = random.Random()
CORES_FAISCA = (CFG.cor_energia, (150, 220, 255), (230, 245, 255))
TAMANHOS_FAISCA = (3, 4, 6)
COR_GRITO = (200, 235, 255)


def _pulso(agora, periodo_ms, limites):
    minimo, maximo = limites
    onda = 0.5 + 0.5 * math.sin(agora * 2 * math.pi / periodo_ms)
    return round(minimo + (maximo - minimo) * onda)


def faiscas(posicao, direcao, quantidade, abertura_graus=360, velocidade=(120, 360), duracao_ms=(250, 500)):
    emitir_leque(posicao, direcao, quantidade, CORES_FAISCA, TAMANHOS_FAISCA, abertura_graus,
                 velocidade, duracao_ms, sorteio=_SORTEIO)


def impacto_da_espada(aviso):
    """Leque de faíscas na direção do golpe (cone ou corte) e um tremor leve."""
    abertura = getattr(aviso.cfg, 'angulo_spray', 60)
    faiscas(aviso.posicao, aviso.direcao, 14, min(abertura, 360))
    aviso.game.camera.shake(intensidade=CFG.shake_golpe)


class ArbiterVFX:
    def iniciar_vfx(self):
        self._proxima_aura = 0
        for frames in self.sprites.values():          # silhuetas prontas no spawn, não no 1º uso
            for frame in frames:
                for cor in (CFG.cor_energia, CFG.cor_costas, COR_GRITO):
                    silhueta_de(frame, cor)

    def grito_vfx(self):
        self._grito_ate = self._agora + CFG.grito_ms
        faiscas(self.posicao, V2(1, 0), CFG.faiscas_grito, 360, velocidade=(200, 520), duracao_ms=(350, 700))
        self.game.camera.shake(intensidade=CFG.shake_grito)

    def _sobrepor(self, tela, deslocamento, cor, alpha):
        sil = silhueta_de(self.quadro_original, cor)
        sil.set_alpha(alpha)
        tela.blit(sil, (self.rect.x - deslocamento.x, self.rect.y - deslocamento.y))

    def draw_extras(self, tela, deslocamento):
        """Chamado pelo renderer depois dos sprites."""
        if self.altura_z > 0:
            desenhar_sombra(tela, self, deslocamento, self.hitbox.width * 1.4)
        if self.invisibilidade is not None:           # camuflado: nada que o entregue
            return
        agora = relogio.agora()
        if agora < self._grito_ate:
            fracao = (self._grito_ate - agora) / CFG.grito_ms
            self._sobrepor(tela, deslocamento, COR_GRITO, round(200 * fracao))
        if self.costas_expostas:
            self._sobrepor(tela, deslocamento, CFG.cor_costas, _pulso(agora, CFG.brilho_periodo_ms, CFG.brilho_alpha))
        elif self.fase >= 2:
            self._sobrepor(tela, deslocamento, CFG.cor_energia, _pulso(agora, CFG.aura_periodo_ms, CFG.aura_alpha))
            if agora >= self._proxima_aura:
                self._proxima_aura = agora + CFG.aura_particulas_ms
                pes = V2(self.posicao.x + _SORTEIO.uniform(-25, 25), self.rect.bottom - 20)
                faiscas(pes, V2(0, -1), 2, 30, velocidade=(60, 140), duracao_ms=(400, 700))
