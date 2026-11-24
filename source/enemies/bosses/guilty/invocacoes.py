"""Invocações do Guilty: cada uma no seu tempo, sem parar a ronda.

Os callbacks `ao_explodir` guardam o Guilty: com ele morto (ou fora da fase), a artilharia só estoura."""
import random

import pygame

from source.enemies.standard.infection import FloodCarry, FloodElite, FloodMarine
from source.enemies.standard.sentinel import Sentinel, SentinelMajor
from source.feats.skills.artilharia import ArtilhariaAviso
from source.systems.entitymanager import entity_manager
from source.systems.status import Lentidao, aplicar

from .armadilha import ArmadilhaForerunner
from .config import CFG
from .luz_visivel import LuzVisivel
from .vfx import impacto_da_chuva, impacto_da_super, impacto_do_flood

V2 = pygame.math.Vector2
FORMAS_FLOOD = (FloodMarine, FloodElite, FloodCarry)


def _vivos(inimigos):
    return [i for i in inimigos if i.alive()]


class GuiltyInvocacoes:
    def atualizar_invocacoes(self):
        """1× por frame, com ou sem rotina ativa. Só com a barreira de pé."""
        if not self.barreira_ativa:
            return
        if self.fase == 1:
            if self.invocacao_pronta('chuva'):
                self.chover_sentinela()
            if self.invocacao_pronta('armadilha'):
                self.armar_armadilha()
        elif self.fase == 2:
            if self.invocacao_pronta('chuva_super'):
                self.chover_super_sentinelas()
            if self.invocacao_pronta('infestacao'):
                self.infestar()

    def invocacao_pronta(self, nome):
        return self._agora >= self.proxima_invocacao[nome]

    def agendar_invocacao(self, nome):
        self.proxima_invocacao[nome] = self._agora + self.novo_cooldown(*CFG.intervalo[nome])

    def encerrar_invocacoes(self):
        """A barreira mudou: o que está no ar se desfaz (as artilharias comuns só estouram)."""
        if self.armadilha is not None:
            self.armadilha.desfazer()
            self.armadilha = None
        if self.luz is not None:
            self.luz.desfazer()
            self.luz = None

    def _aviso(self, posicao, preset, ao_explodir):
        return ArtilhariaAviso(posicao, (entity_manager.all_sprites,), self.game, dono='BOSS', preset=preset,
                               fonte=self, ao_explodir=ao_explodir)

    def _ponto_valido(self, sortear, tentativas=12):
        """O primeiro ponto sorteado que caia no chão da arena (senão, onde o jogador está)."""
        for _ in range(tentativas):
            ponto = sortear()
            if self.verificar_posicao_valida(ponto):
                return ponto
        return V2(self.jogador.posicao)

    # ------------------------------------------------------------ fase 1: chuva de sentinelas
    def chover_sentinela(self):
        self.agendar_invocacao('chuva')
        self.sentinelas = _vivos(self.sentinelas)
        if len(self.sentinelas) + self.avisos_chuva >= CFG.chuva_max_vivas:
            return None
        ponto = self._ponto_valido(lambda: self.jogador.posicao
                                   + V2(random.uniform(*CFG.chuva_raio), 0).rotate(random.uniform(0, 360)))
        self.avisos_chuva += 1
        return self._aviso(ponto, 'guilty_sentinela', self._cair_sentinela)

    def _cair_sentinela(self, aviso):
        self.avisos_chuva -= 1
        impacto_da_chuva(aviso)
        if self.alive() and self.fase == 1 and self.barreira_ativa:
            self.sentinelas.append(self._materializar(Sentinel, aviso.posicao))

    def _materializar(self, classe, posicao):
        sentinela = classe(V2(posicao), self.game)
        sentinela.materializar()
        return sentinela

    # ------------------------------------------------------------ fase 1: armadilha forerunner
    def armar_armadilha(self):
        self.agendar_invocacao('armadilha')
        if self.armadilha is None or not self.armadilha.alive():
            self.armadilha = ArmadilhaForerunner(self)

    # ------------------------------------------------------------ fase 2: super sentinelas
    def chover_super_sentinelas(self):
        """Três artilharias a 120° uma da outra, à mesma distância de onde o jogador está."""
        self.agendar_invocacao('chuva_super')
        self.super_sentinelas = _vivos(self.super_sentinelas)
        if len(self.super_sentinelas) + 3 > CFG.super_max_vivas:
            return []
        for _ in range(12):       # gira o triângulo até os 3 vértices caírem no chão, se der
            giro = random.uniform(0, 360)
            pontos = [self.jogador.posicao + V2(CFG.super_dist, 0).rotate(giro + 120 * i) for i in range(3)]
            if all(self.verificar_posicao_valida(p) for p in pontos):
                break
        return [self._aviso(p, 'guilty_super_sentinela', self._cair_super_sentinela) for p in pontos]

    def _cair_super_sentinela(self, aviso):
        impacto_da_super(aviso)
        if self.alive() and self.fase == 2:
            self.super_sentinelas.append(self._materializar(SentinelMajor, aviso.posicao))

    # ------------------------------------------------------------ fase 2: infestação
    def infestar(self):
        self.agendar_invocacao('infestacao')
        self.floods = _vivos(self.floods)
        if len(self.floods) + CFG.flood_quantidade > CFG.flood_max_vivos:
            return None
        meia_l, meia_a = CFG.flood_tela
        ponto = self._ponto_valido(lambda: self.jogador.posicao + V2(random.uniform(-meia_l, meia_l),
                                                                     random.uniform(-meia_a, meia_a)))
        return self._aviso(ponto, 'guilty_flood', self._brotar_flood)

    def _brotar_flood(self, aviso):
        impacto_do_flood(aviso)
        raio = aviso.cfg.raio_explosao
        if self.jogador.posicao.distance_squared_to(aviso.posicao) <= raio * raio:
            aplicar(self.jogador, Lentidao(CFG.flood_lentidao, CFG.flood_lentidao_ms), fonte=self,
                    chave='guilty_flood')
        if not (self.alive() and self.fase == 2):
            return
        for i in range(CFG.flood_quantidade):
            ponto = aviso.posicao + V2(raio * 0.5, 0).rotate(360 * i / CFG.flood_quantidade)
            if not self.verificar_posicao_valida(ponto):
                ponto = V2(aviso.posicao)
            self.floods.append(random.choice(FORMAS_FLOOD)(posicao=ponto, game=self.game))

    # ------------------------------------------------------------ fase 2: luz visível
    def invocar_luz(self):
        self.agendar_invocacao('luz')
        if self.luz is None or not self.luz.alive():
            self.luz = LuzVisivel(self, self.jogador.posicao)
