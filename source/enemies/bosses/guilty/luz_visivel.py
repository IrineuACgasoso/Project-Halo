"""Luz visível forerunner: artilharias em cadeia no mesmo centro, cada uma maior e mais forte que a
anterior. Um feixe cai do céu no instante em que cada uma estoura. É a única coisa que fere o Guilty
com a barreira de pé (`GuiltyBarreira.atingido_pela_luz`)."""
import pygame

from source.feats.skills.artilharia import ArtilhariaAviso
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.utils.superficies import SUPERFICIE_VAZIA

from .config import CFG
from .vfx import FeixeDoCeu, impacto_da_luz


class LuzVisivel(pygame.sprite.Sprite):
    """Condutor invisível da cadeia."""

    def __init__(self, guilty, posicao):
        super().__init__(entity_manager.all_sprites)
        self.guilty = guilty
        self.posicao = pygame.math.Vector2(posicao)
        self.image = SUPERFICIE_VAZIA
        self.rect = self.image.get_rect(center=self.posicao)
        self.indice = -1
        self.aviso = None
        self._feixe_caiu = False
        self._proxima()

    def _proxima(self):
        self.indice += 1
        self._feixe_caiu = False
        self.aviso = ArtilhariaAviso(self.posicao, (entity_manager.all_sprites,), self.guilty.game, dono='BOSS',
                                     preset=CFG.luz_presets[self.indice], fonte=self.guilty,
                                     ao_explodir=self._estourou)

    def update(self, delta_time):
        if not self.guilty.alive():
            self.desfazer()
            return
        falta = self.aviso.cfg.duracao - (relogio.agora() - self.aviso.tempo_criacao)
        if not self._feixe_caiu and falta <= CFG.luz_raio_antes_ms:
            self._feixe_caiu = True
            FeixeDoCeu(self.posicao, self.aviso.cfg.raio_explosao)

    def _estourou(self, aviso):
        if not self.alive():      # desfeita neste mesmo frame
            return
        impacto_da_luz(aviso, CFG.shake_luz[self.indice])
        self.guilty.atingido_pela_luz(aviso)
        if self.indice + 1 < len(CFG.luz_presets):
            self._proxima()
        else:
            self.kill()

    def desfazer(self):
        """Some sem estourar (o Guilty morreu ou mudou de fase)."""
        if not self.aviso.explodiu:
            self.aviso.kill()
        self.kill()
