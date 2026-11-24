"""O andar do Scarab: passos que são ataques, virar com atraso e o repouso com o jogador por baixo.

Um passo ergue duas patas (frente + trás, depois centro + oculta), com uma artilharia em cada ponto onde
elas vão pisar. As patas voltam ao chão no mesmo frame em que a artilharia estoura: os dois contam o
mesmo tempo, a partir do mesmo instante."""
from dataclasses import replace
from functools import lru_cache

import pygame

from source.feats.skills.artilharia import ArtilhariaAviso
from source.feats.skills.artilharia.config import ARTILHARIA_PRESETS
from source.systems.entitymanager import entity_manager

from .config import CFG

PARES = (('frente', 'tras'), ('centro', 'oculta'))


@lru_cache(maxsize=None)
def config_do_passo(duracao_ms):
    return replace(ARTILHARIA_PRESETS['scarab_passo'], duracao=duracao_ms)


class ScarabMovement:
    # ------------------------------------------------------------ passos
    @property
    def no_passo(self):
        return any(pata.erguida for pata in self.patas.values())

    @property
    def em_repouso(self):
        """Com o jogador por baixo ele não anda, não vira e não anima (um passo já no ar termina)."""
        return self.jogador_sob

    def atualizar_passo(self, agora):
        if self.no_passo:
            if agora >= self.pousa_em:
                self.pousar()
        elif self.rotina is None and not self.em_repouso and agora >= self.proximo_passo_em:
            self.erguer_par()

    def erguer_par(self):
        par = PARES[self.par_do_passo]
        self.par_do_passo = 1 - self.par_do_passo
        duracao = CFG.passo_ms[self.fase - 1]
        self.pousa_em = self._agora + duracao
        self.torreta_recuada = not self.torreta_recuada
        for nome in par:
            pata = self.patas[nome]
            pata.erguida = True
            self.avisar(pata.posicao, custom_config=config_do_passo(duracao), grude=True, alvo=pata)

    def pousar(self):
        for pata in self.patas.values():
            if pata.erguida:
                pata.erguida = False
                self.impacto_do_passo(pata)
        self.proximo_passo_em = self._agora + CFG.apoio_ms[self.fase - 1]

    def avisar(self, posicao, **kwargs):
        """Cria uma artilharia dele e a guarda (a queda e a morte cancelam as que ainda não estouraram)."""
        aviso = ArtilhariaAviso(posicao, (entity_manager.all_sprites,), self.game, dono='BOSS', fonte=self, **kwargs)
        self.avisos = [a for a in self.avisos if a.alive() and not a.explodiu]
        self.avisos.append(aviso)
        return aviso

    def cancelar_avisos(self):
        """As patas vão ao chão sem pisar."""
        for aviso in self.avisos:
            if not aviso.explodiu:
                aviso.kill()
        self.avisos = []
        for pata in self.patas.values():
            pata.erguida = False
            pata.extra_y = 0.0
        self.proximo_passo_em = self._agora + CFG.apoio_ms[self.fase - 1]

    # ------------------------------------------------------------ andar
    def andar(self):
        """Padrão de todo frame sem rotina: levar o centro do chão até o jogador, aos trancos."""
        if self.em_repouso:
            self.parar()
            return
        para = self.jogador.posicao - self.centro_chao
        if para.length_squared() == 0:
            self.parar()
            return
        fator = CFG.mult_no_ar if self.no_passo else CFG.mult_apoio
        if para.length_squared() > CFG.dist_longe ** 2:
            fator *= CFG.mult_longe
        self._ir(para.normalize(), fator)

    def parar(self):
        self._dir_mov = pygame.math.Vector2(0, 0)
        self.velocidade = 0

    def aplicar_colisao_mapa(self, grade_paredes):
        """Ele passa por cima de prédios e muros; só não sai do mapa."""
        mapa, margem = self.game.mapa, CFG.margem_mapa
        self.posicao.x = max(margem, min(self.posicao.x, mapa.largura_mapa_pixels - margem))
        self.posicao.y = max(margem, min(self.posicao.y, mapa.altura_mapa_pixels - margem))

    # ------------------------------------------------------------ virar (atraso do Hunter)
    @property
    def pode_virar(self):
        return self.rotina is None and not self.no_passo and not self.em_repouso

    def orientar(self):
        """Jogador do outro lado inicia o timer; mudar de lado de novo não o reinicia. Vencido o tempo,
        vale o lado do jogador naquele instante, assim que as 4 patas estiverem no chão."""
        dx = self.jogador.posicao.x - self.posicao.x
        lado_jogador = 'right' if dx > 0 else 'left' if dx < 0 else self.animador.lado
        if self.virar_em is None:
            if lado_jogador != self.animador.lado and not self.em_repouso:
                self.virar_em = self._agora + CFG.atraso_virar_ms
        elif self._agora >= self.virar_em and self.pode_virar:
            self.virar_em = None
            if lado_jogador != self.animador.lado:
                self.set_sprite_direction(dx)
