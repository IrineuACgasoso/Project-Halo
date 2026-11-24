"""Armadilha forerunner: duas esferas vêm de fora da tela e fecham uma linha com o jogador no meio.
Param por um instante; uma delas fica azul e dispara um feixe na outra. Quem ficou na linha leva o
golpe (uma vez) e queima. As esferas não são inimigos: ninguém as mira nem as acerta."""
import random

import pygame

from source.feats.skills.continuousbeam import ContinuousBeam
from source.systems.dano import AREA, Dano
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.systems.status import Queimadura, aplicar
from source.utils.collision_utils import empurrao_do_segmento
from source.utils.superficies import SUPERFICIE_VAZIA

from .config import CFG
from .vfx import faiscas, imagem_da_esfera

V2 = pygame.math.Vector2
BUSCA, PARADA, DISPARO, SAIDA = 'busca', 'parada', 'disparo', 'saida'


class EsferaForerunner(pygame.sprite.Sprite):
    def __init__(self, game, posicao):
        super().__init__(entity_manager.all_sprites)
        self.game = game                 # o ContinuousBeam lê `game` e `posicao` do dono
        self.posicao = V2(posicao)
        self.image = imagem_da_esfera(azul=False)
        self.rect = self.image.get_rect(center=self.posicao)

    def mover_ate(self, alvo, passo):
        """Anda até `passo` px na direção de `alvo`. Devolve se chegou."""
        self.posicao.move_towards_ip(alvo, passo)
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        return self.posicao.distance_squared_to(alvo) <= CFG.armadilha_tolerancia ** 2

    def acender(self):
        self.image = imagem_da_esfera(azul=True)
        self.rect = self.image.get_rect(center=self.rect.center)


class ArmadilhaForerunner(pygame.sprite.Sprite):
    """Condutor das duas esferas; desenha o feixe."""

    def __init__(self, guilty):
        super().__init__(entity_manager.all_sprites)
        self.guilty = guilty
        self.jogador = guilty.jogador
        self.eixo = V2(1, 0).rotate(random.uniform(0, 360))
        self.esferas = [EsferaForerunner(guilty.game, self.jogador.posicao
                                         + self.eixo * (lado * CFG.armadilha_dist_inicio)) for lado in (1, -1)]
        self.emissora, self.receptora = random.sample(self.esferas, 2)
        # Sem dano próprio: só a ponta que avança e o desenho (o golpe é do segmento inteiro, 1×)
        self.feixe = ContinuousBeam(self.emissora, color=CFG.armadilha_cor,
                                    largura_base=CFG.armadilha_feixe_largura,
                                    suavizacao=CFG.armadilha_feixe_suavizacao)
        self.acertou = False
        self.image = SUPERFICIE_VAZIA     # o draw é próprio
        self.rect = self.image.get_rect(center=self.jogador.posicao)
        self._entrar(BUSCA)

    def _entrar(self, estado):
        self.estado = estado
        self.inicio = relogio.agora()

    def update(self, delta_time):
        if not self.guilty.alive():
            self.desfazer()
            return
        passou = relogio.agora() - self.inicio
        if self.estado == BUSCA:
            self._buscar(delta_time, passou)
        elif self.estado == PARADA:
            if passou >= CFG.armadilha_parada_ms - CFG.armadilha_azul_ms:
                self.emissora.acender()
            if passou >= CFG.armadilha_parada_ms:
                self.feixe.mira_atual = V2(self.emissora.posicao)
                self._entrar(DISPARO)
        elif self.estado == DISPARO:
            self._disparar(passou)
        else:
            self._sair(delta_time, passou)

    def _buscar(self, delta_time, passou):
        """Cada esfera persegue a sua ponta da linha (o jogador no meio); valem quando as duas chegam."""
        passo = CFG.armadilha_velocidade * delta_time
        chegaram = [esfera.mover_ate(self.jogador.posicao + self.eixo * (lado * CFG.armadilha_dist), passo)
                    for esfera, lado in zip(self.esferas, (1, -1))]
        if all(chegaram) or passou >= CFG.armadilha_busca_max_ms:
            self.rect.center = self.emissora.rect.center
            self._entrar(PARADA)

    def _disparar(self, passou):
        self.feixe.mirar(self.receptora.posicao)
        restante = 1 - passou / CFG.armadilha_disparo_ms
        if restante <= 0:
            faiscas(self.receptora.posicao, 14, (CFG.armadilha_cor, (220, 245, 255)))
            self._entrar(SAIDA)
            return
        self.guilty.game.camera.shake(intensidade=CFG.shake_armadilha * restante, duracao=60)
        if not self.acertou and self._atinge_o_jogador():
            self.acertou = True
            self.jogador.receber_dano(Dano(CFG.armadilha_dano, AREA, self.guilty, ignora_iframes=True))
            aplicar(self.jogador, Queimadura(CFG.armadilha_queimadura_dps, CFG.armadilha_queimadura_ms),
                    fonte=self.guilty, chave='guilty_armadilha')

    def _atinge_o_jogador(self):
        p, a, b = self.jogador.posicao, self.emissora.posicao, self.feixe.mira_atual
        return empurrao_do_segmento(p.x, p.y, a.x, a.y, b.x, b.y, CFG.armadilha_alcance) is not None

    def _sair(self, delta_time, passou):
        """Disparam para fora pela própria linha."""
        for esfera, lado in zip(self.esferas, (1, -1)):
            esfera.mover_ate(esfera.posicao + self.eixo * (lado * 1000), CFG.armadilha_velocidade * 2 * delta_time)
        if passou >= CFG.armadilha_saida_ms:
            self.desfazer()

    def desfazer(self):
        for esfera in self.esferas:
            esfera.kill()
        self.kill()

    def draw(self, superficie, deslocamento):
        if self.estado == DISPARO:
            self.feixe.draw(superficie, deslocamento)
