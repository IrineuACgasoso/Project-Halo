"""Granada de plasma (do jogador e dos inimigos): o dano e o aviso são os da artilharia; muda o que se vê.

- Aviso: o círculo de sempre, com o núcleo da granada piscando cada vez mais rápido até estourar.
- Explosão (`ExplosaoPlasma`): clarão em camadas no espírito dos golpes da espada de energia (núcleo
  branco, brilho azul que se apaga, duas ondas de choque) e plasma estourando junto: faíscas rápidas e
  gotas maiores que sobem devagar. Só visual: sorteio próprio e sprite no grupo das partículas.

As cores e quantidades ficam em `EXPLOSAO_PLASMA_PRESETS`, com o mesmo nome do preset da artilharia."""
import random
from dataclasses import dataclass
from typing import Tuple

import pygame

from source.feats.particulas import emitir_leque
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.utils.superficies import SUPERFICIE_VAZIA, camada_alpha
from .core import ArtilhariaAviso

Cor = Tuple[int, int, int]
CorA = Tuple[int, int, int, int]
RAIO_REFERENCIA = 150      # as quantidades de partículas valem para este raio e escalam com ele
_SORTEIO = random.Random()


@dataclass(frozen=True)
class ExplosaoPlasmaConfig:
    duracao_ms: int = 420
    cor_nucleo: Cor = (245, 250, 255)                   # centro branco, some primeiro
    cor_brilho: CorA = (150, 205, 255, 190)             # clarão que se apaga
    cor_onda: CorA = (70, 150, 255, 235)                # onda de choque de fora
    cor_onda_interna: CorA = (195, 235, 255, 220)       # onda de dentro, mais clara
    faiscas: int = 28
    cores_faisca: Tuple[Cor, ...] = ((60, 170, 255), (150, 220, 255), (230, 245, 255))
    tamanhos_faisca: Tuple[int, ...] = (4, 5, 7)
    gotas: int = 9                                      # plasma estourando: bolhas que sobem
    cores_gota: Tuple[Cor, ...] = ((70, 110, 255), (120, 160, 255), (165, 120, 255))
    tamanhos_gota: Tuple[int, ...] = (8, 10, 12)
    piscar_ms: Tuple[int, int] = (220, 60)              # núcleo do aviso: do início ao estouro
    raio_piscar: int = 9
    shake: float = 0
    ondas_aviso: int = 0                                # anéis fechando para o centro durante o aviso
    onda_aviso_ms: int = 420                            # quanto cada anel leva da borda ao centro
    lentas: int = 0                                     # plasma que se espalha devagar e fica no ar
    cores_lenta: Tuple[Cor, ...] = ()
    tamanhos_lenta: Tuple[int, ...] = (5, 7, 9)
    velocidade_lenta: Tuple[float, float] = (0.12, 0.45)   # × raio, por segundo
    duracao_lenta_ms: Tuple[int, int] = (1000, 1800)


EXPLOSAO_PLASMA_PRESETS = {
    # Lançador do jogador: sem tremor (dispara muito)
    'plasma_grenade': ExplosaoPlasmaConfig(),
    # Arbiter: maior, mais plasma e um tremor
    'arbiter_plasma_grenade': ExplosaoPlasmaConfig(
        duracao_ms=480,
        faiscas=32,
        gotas=11,
        raio_piscar=12,
        shake=4,
    ),
    # Canhão do Hunter: paleta da PlasmaGun (verde-limão), maior, com anéis no aviso e plasma lento que
    # fica no ar. O tremor é do gancho do Hunter (`impacto_do_canhao`).
    'hunter_cannon': ExplosaoPlasmaConfig(
        duracao_ms=560,
        cor_nucleo=(250, 255, 230),
        cor_brilho=(170, 255, 0, 190),
        cor_onda=(110, 255, 30, 240),
        cor_onda_interna=(215, 255, 120, 225),
        faiscas=40,
        cores_faisca=((170, 255, 0), (215, 255, 120), (250, 255, 230)),
        tamanhos_faisca=(4, 6, 8),
        gotas=14,
        cores_gota=((95, 210, 20), (110, 255, 30), (170, 255, 0)),
        tamanhos_gota=(9, 12, 14),
        piscar_ms=(200, 50),
        raio_piscar=16,
        ondas_aviso=2,
        lentas=26,
        cores_lenta=((110, 255, 30), (170, 255, 0), (95, 210, 20), (215, 255, 120)),
    ),
}


class AvisoPlasma(ArtilhariaAviso):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vfx = EXPLOSAO_PLASMA_PRESETS.get(self.preset, EXPLOSAO_PLASMA_PRESETS['plasma_grenade'])
        self._gancho = self.ao_explodir
        self.ao_explodir = self._estourar

    def _estourar(self, aviso):
        ExplosaoPlasma(self.posicao, self.cfg.raio_explosao, self.vfx)
        camera = getattr(self.game, 'camera', None)
        if self.vfx.shake and camera is not None:
            camera.shake(intensidade=self.vfx.shake)
        if self._gancho is not None:
            self._gancho(aviso)

    def draw(self, surface, offset):
        if self.explodiu:          # quem desenha a explosão é a ExplosaoPlasma
            return
        cfg, vfx = self.cfg, self.vfx
        idade = relogio.agora() - self.tempo_criacao
        progresso = min(idade / cfg.duracao, 1.0)
        raio = cfg.raio_explosao
        x, y = int(self.posicao.x - offset.x), int(self.posicao.y - offset.y)
        camada, area = camada_alpha(surface, (x - raio, y - raio, raio * 2, raio * 2))
        if camada is None:
            return
        pygame.draw.circle(camada, cfg.cor_borda, (x, y), raio, 4)
        if progresso > 0:
            pygame.draw.circle(camada, cfg.cor_preenchimento, (x, y), max(1, int(raio * progresso)))
        if vfx.ondas_aviso:
            r, g, b, _ = vfx.cor_onda
            pygame.draw.circle(camada, (r, g, b, round(40 + 50 * progresso)), (x, y), raio, 12)   # brilho da borda
            for k in range(vfx.ondas_aviso):
                fase = (idade / vfx.onda_aviso_ms + k / vfx.ondas_aviso) % 1.0
                pygame.draw.circle(camada, (r, g, b, round(200 * fase)), (x, y), max(2, round(raio * (1 - fase))), 3)
        inicio, fim = vfx.piscar_ms
        periodo = inicio + (fim - inicio) * progresso
        aceso = int(idade // periodo) % 2 == 0
        cor = vfx.cor_nucleo if aceso else vfx.cor_onda[:3]
        pygame.draw.circle(camada, (*vfx.cor_onda[:3], 200), (x, y), round(vfx.raio_piscar * 1.6))
        pygame.draw.circle(camada, (*cor, 255), (x, y), vfx.raio_piscar)
        surface.blit(camada, area.topleft, area)


class ExplosaoPlasma(pygame.sprite.Sprite):
    """O estouro: camadas que crescem e se apagam em `duracao_ms`, mais as partículas do plasma."""

    def __init__(self, posicao, raio, vfx):
        super().__init__(entity_manager.all_sprites, entity_manager.particulas_grupo)
        self.posicao = pygame.math.Vector2(posicao)
        self.raio = raio
        self.vfx = vfx
        self.nascimento = relogio.agora()
        self.y_desenho = self.posicao.y - raio            # no chão: o plasma que estoura sai por cima
        self.image = SUPERFICIE_VAZIA
        self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))
        escala = raio / RAIO_REFERENCIA
        emitir_leque(self.posicao, (1, 0), round(vfx.faiscas * escala), vfx.cores_faisca, vfx.tamanhos_faisca,
                     velocidade=(raio * 1.6, raio * 3.2), duracao_ms=(220, 450), sorteio=_SORTEIO)
        emitir_leque(self.posicao, (1, 0), round(vfx.gotas * escala), vfx.cores_gota, vfx.tamanhos_gota,
                     velocidade=(raio * 0.5, raio * 1.4), duracao_ms=(450, 800), gravidade=-90,
                     sorteio=_SORTEIO)
        if vfx.lentas:
            lenta_min, lenta_max = vfx.velocidade_lenta
            emitir_leque(self.posicao, (1, 0), round(vfx.lentas * escala), vfx.cores_lenta, vfx.tamanhos_lenta,
                         velocidade=(raio * lenta_min, raio * lenta_max), duracao_ms=vfx.duracao_lenta_ms,
                         gravidade=-25, sorteio=_SORTEIO)

    def update(self, delta_time, paredes=None):
        if relogio.agora() - self.nascimento >= self.vfx.duracao_ms:
            self.kill()

    def draw(self, surface, offset):
        vfx, raio = self.vfx, self.raio
        resta = 1.0 - min(1.0, (relogio.agora() - self.nascimento) / vfx.duracao_ms)
        abre = 1.0 - resta ** 3                         # cresce rápido e assenta
        x, y = int(self.posicao.x - offset.x), int(self.posicao.y - offset.y)
        alcance = round(raio * 1.12)
        camada, area = camada_alpha(surface, (x - alcance, y - alcance, alcance * 2, alcance * 2))
        if camada is None:
            return
        r, g, b, a = vfx.cor_brilho
        pygame.draw.circle(camada, (r, g, b, round(a * resta * resta)), (x, y), max(1, round(raio * (0.55 + 0.45 * abre))))
        r, g, b, a = vfx.cor_onda
        pygame.draw.circle(camada, (r, g, b, round(a * resta)), (x, y), max(1, round(raio * (0.35 + 0.75 * abre))),
                           max(2, round(raio * 0.10 * resta)))
        r, g, b, a = vfx.cor_onda_interna
        pygame.draw.circle(camada, (r, g, b, round(a * resta)), (x, y), max(1, round(raio * (0.2 + 0.55 * abre))),
                           max(1, round(raio * 0.05 * resta)))
        if resta > 0.35:
            nucleo = (resta - 0.35) / 0.65
            pygame.draw.circle(camada, (*vfx.cor_nucleo, round(255 * nucleo)), (x, y), max(1, round(raio * 0.45 * nucleo)))
        surface.blit(camada, area.topleft, area)
