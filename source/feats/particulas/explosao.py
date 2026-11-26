"""Explosão de impacto (martelada, pouso, fim de corrida): clarão com anel que se abre, faíscas que
saltam e caem e poeira em anel. Reaproveitável por qualquer golpe: `explosao_de_impacto(...)` direto
ou `gancho_explosao(...)` no `ao_explodir` de uma artilharia (o raio vem do aviso).

Só visual: sorteio próprio, desenho numa camada reaproveitada, partículas no teto global."""
import random

import pygame

from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.utils.superficies import SUPERFICIE_VAZIA, camada_alpha

from .motor import emitir_leque, preparar
from .poeira import CORES_PEDRA, TAMANHOS_NUVEM, anel_de_poeira, poeira_em_area

V2 = pygame.math.Vector2
SORTEIO = random.Random()

# (núcleo, meio, borda, faíscas)
PALETAS = {
    'fogo':      ((255, 250, 225), (255, 200, 80), (255, 110, 20),
                  ((255, 255, 235), (255, 225, 90), (255, 160, 25), (255, 85, 10))),
    'gravidade': ((235, 245, 255), (130, 190, 255), (70, 100, 255),
                  ((230, 245, 255), (140, 200, 255), (80, 140, 255), (150, 110, 255))),
    'vortice':   ((245, 235, 255), (190, 120, 255), (110, 40, 220),
                  ((245, 235, 255), (200, 150, 255), (150, 80, 255), (100, 40, 200))),
    'furia':     ((255, 240, 220), (255, 120, 60), (200, 20, 20),
                  ((255, 240, 200), (255, 150, 60), (255, 60, 30), (180, 20, 20))),
}
TAMANHOS_FAISCA = (4, 6, 8)


def preparar_explosao(paleta='fogo'):
    """Pinta já as faíscas e a poeira (no spawn de quem explode coisas)."""
    preparar(PALETAS[paleta][3], TAMANHOS_FAISCA)
    preparar(CORES_PEDRA, TAMANHOS_NUVEM)


class ClaraoExplosao(pygame.sprite.Sprite):
    """Bola de luz que encolhe, anel que se abre até `raio` e uma coroa de raios."""
    RAIOS = 12

    def __init__(self, posicao, raio, paleta='fogo', duracao_ms=380, y_desenho=None):
        super().__init__(entity_manager.all_sprites)
        self.posicao = V2(posicao)
        self.raio = raio
        self.nucleo, self.meio, self.borda, _ = PALETAS[paleta]
        self.duracao_ms = duracao_ms
        self.nascimento = relogio.agora()
        self.angulo = SORTEIO.uniform(0, 360)
        self.y_desenho = y_desenho
        self.image = SUPERFICIE_VAZIA       # o draw é próprio
        self.rect = pygame.Rect(0, 0, 1, 1)
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

    def update(self, delta_time, *args):
        if relogio.agora() - self.nascimento >= self.duracao_ms:
            self.kill()

    def draw(self, surface, offset):
        t = min(1.0, (relogio.agora() - self.nascimento) / self.duracao_ms)
        centro = self.posicao - offset
        r = self.raio
        camada, area = camada_alpha(surface, (round(centro.x - r) - 8, round(centro.y - r) - 8, 2 * r + 16, 2 * r + 16))
        if camada is None:
            return
        alpha = round(255 * (1 - t))
        pygame.draw.circle(camada, (*self.borda, round(110 * (1 - t))), centro, r * (0.55 + 0.45 * t))
        pygame.draw.circle(camada, (*self.meio, round(200 * (1 - t))), centro, r * 0.5 * (1 - t * 0.6))
        pygame.draw.circle(camada, (*self.nucleo, alpha), centro, r * 0.28 * (1 - t))
        base = V2(1, 0).rotate(self.angulo)
        for i in range(self.RAIOS):
            direcao = base.rotate(i * 360 / self.RAIOS)
            longo = r * (1.0 if i % 2 == 0 else 0.65)
            pygame.draw.line(camada, (*self.meio, alpha), centro + direcao * longo * 0.3 * (0.5 + t),
                             centro + direcao * longo * (0.45 + 0.55 * t), 6 if i % 2 == 0 else 4)
        pygame.draw.circle(camada, (*self.nucleo, alpha), centro, r * (0.3 + 0.7 * t), 5)
        surface.blit(camada, area.topleft, area)


def explosao_de_impacto(posicao, raio, paleta='fogo', game=None, shake=None, poeira=True, faiscas=1.0):
    """Clarão + faíscas + poeira em anel (e nuvem na área). `shake`: (intensidade, ms) na câmera de
    `game`. `faiscas`: multiplica a quantidade de faíscas."""
    posicao = V2(posicao)
    ClaraoExplosao(posicao, raio, paleta)
    cores = PALETAS[paleta][3]
    emitir_leque(posicao, (0, -1), round(34 * faiscas), cores, TAMANHOS_FAISCA, 360, velocidade=(180, 620),
                 duracao_ms=(400, 850), gravidade=520, sorteio=SORTEIO)
    if poeira:
        anel_de_poeira(posicao, raio, max(10, round(raio / 6)))
        poeira_em_area(posicao, raio * 0.8, max(8, round(raio / 10)))
    if shake is not None and game is not None:
        game.camera.shake(intensidade=shake[0], duracao=shake[1])


def gancho_explosao(paleta='fogo', shake=None, poeira=True, faiscas=1.0):
    """Para o `ao_explodir` de uma artilharia: a explosão no centro e no raio do aviso."""
    def ao_explodir(aviso):
        explosao_de_impacto(aviso.posicao, aviso.cfg.raio_explosao, paleta, aviso.game, shake, poeira, faiscas)
    return ao_explodir
