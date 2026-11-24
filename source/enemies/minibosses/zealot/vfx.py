"""Efeitos visuais do Zealot: rastro azul do dash, faíscas dos golpes e da quebra do escudo.

A distorção de quando ele está invisível não é daqui: é de todo inimigo camuflado
(`feats/skills/invisibilidade/distorcao.py`). As funções `impacto_*` recebem o aviso da habilidade
(gancho `ao_explodir`), não o Zealot: saem mesmo se ele já tiver morrido."""
from collections import deque

import pygame

from source.feats.particulas import emitir_leque
from source.systems.gameclock import relogio
from source.utils.superficies import silhueta_de

from .config import CFG

V2 = pygame.math.Vector2

CORES_FAISCA = (CFG.cor_energia, (150, 235, 255), (20, 130, 255))
TAMANHOS_FAISCA = (3, 4, 6)


def faiscas(posicao, direcao, quantidade, abertura_graus=360, velocidade=(120, 320), duracao_ms=(250, 500)):
    emitir_leque(posicao, direcao, quantidade, CORES_FAISCA, TAMANHOS_FAISCA, abertura_graus,
                 velocidade, duracao_ms)


def impacto_da_estocada(aviso):
    """Faíscas ao longo da lâmina, indo para a frente."""
    grupos = 4
    for i in range(grupos):
        ponto = aviso.posicao + aviso.direcao * (aviso.cfg.altura * (i + 1) / grupos)
        faiscas(ponto, aviso.direcao, CFG.faiscas_golpe // grupos, 70)
    aviso.game.camera.shake(intensidade=CFG.shake_golpe)


def impacto_do_cone(cone):
    """Leque de faíscas com a abertura do cone."""
    faiscas(cone.posicao, cone.direcao, CFG.faiscas_golpe, cone.cfg.angulo_spray, velocidade=(250, 600))
    cone.game.camera.shake(intensidade=CFG.shake_golpe)


class ZealotVFX:
    def iniciar_vfx(self):
        maximo = CFG.rastro_duracao_ms // CFG.rastro_intervalo_ms + 1
        self.rastro = deque(maxlen=maximo)         # (ms, x, y, quadro)
        self._proximo_rastro = 0
        for frames in self.sprites.values():       # silhuetas prontas no spawn, não no 1º dash
            for frame in frames:
                silhueta_de(frame, CFG.cor_energia)

    def marcar_rastro(self, agora):
        if agora >= self._proximo_rastro:
            self._proximo_rastro = agora + CFG.rastro_intervalo_ms
            self.rastro.append((agora, self.rect.x, self.rect.y, self.quadro_original))

    def draw_extras(self, tela, deslocamento):
        """Chamado pelo renderer depois dos sprites: as silhuetas do dash, sumindo."""
        agora = relogio.agora()
        while self.rastro and agora - self.rastro[0][0] >= CFG.rastro_duracao_ms:
            self.rastro.popleft()
        for quando, x, y, quadro in self.rastro:
            sil = silhueta_de(quadro, CFG.cor_energia)
            sil.set_alpha(round(CFG.rastro_alpha * (1 - (agora - quando) / CFG.rastro_duracao_ms)))
            tela.blit(sil, (x - deslocamento.x, y - deslocamento.y))

    def quebra_do_escudo(self):
        faiscas(self.posicao, V2(1, 0), CFG.faiscas_escudo, 360, velocidade=(150, 420), duracao_ms=(300, 650))
        self.game.camera.shake(intensidade=CFG.shake_escudo)
