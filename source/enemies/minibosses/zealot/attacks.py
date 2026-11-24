"""Rotinas do Zealot (geradores: `yield` = 1 frame; todo `while` tem `yield`)."""
import random

from source.feats.skills.cone_strike import ConeStrikeAviso
from source.feats.skills.invisibilidade import FADE_OUT, OCULTO
from source.feats.skills.rect_strike import RectStrikeAviso
from source.systems.entitymanager import entity_manager
from source.systems.status import Escudo, aplicar

from .config import CFG
from .vfx import impacto_da_estocada, impacto_do_cone


class ZealotAttacks:
    # ------------------------------------------------------------ golpes (no vetor do dash)
    def _estocada(self, direcao):
        """Retângulo fino à frente. Devolve a duração do aviso (ms)."""
        aviso = RectStrikeAviso(self.posicao.copy(), direcao, (entity_manager.all_sprites,), self.game,
                                dono='BOSS', preset=CFG.combo_estocada_preset, fonte=self,
                                ao_explodir=impacto_da_estocada)
        return aviso.cfg.duracao

    def _cone(self, direcao, preset):
        """Cone azul fosforescente à frente. Devolve a duração do aviso (ms)."""
        cone = ConeStrikeAviso(self.posicao.copy(), direcao, (entity_manager.all_sprites,), self.game,
                               dono='BOSS', preset=preset, fonte=self, ao_explodir=impacto_do_cone)
        return cone.cfg.duracao

    # ------------------------------------------------------------ combo de 3 dashes
    def rotina_combo(self):
        """Dash puro → dash + estocada → dash + varredura, com `combo_pausa_ms` entre um dash e o próximo.
        Parado entre eles, não dá dano de contato (ele para em cima de onde o jogador estava)."""
        try:
            yield from self._esperar(CFG.combo_preparo_ms)
            yield from self._dash_do_combo()
            yield from self._esperar(random.randint(*CFG.combo_pausa_ms))

            direcao = yield from self._dash_do_combo()
            aviso = self._estocada(direcao)
            pausa = max(aviso, random.randint(*CFG.combo_pausa_ms))   # a pausa conta do fim do dash
            yield from self._esperar(aviso, direcao.x)
            yield from self._esperar(pausa - aviso)

            direcao = yield from self._dash_do_combo()
            yield from self._esperar(self._cone(direcao, CFG.combo_cone_preset), direcao.x)
            yield from self._esperar(CFG.combo_recuperacao_ms)
        finally:
            self.is_inofensivo = False
        self.agendar('combo')

    def _dash_do_combo(self):
        self.is_inofensivo = False
        direcao = yield from self._dash(CFG.combo_dash_preset)
        self.is_inofensivo = True
        return direcao

    # ------------------------------------------------------------ invisibilidade ofensiva
    def rotina_furtivo(self):
        """Some e corre atrás do jogador; chegando perto, dá um bote que passa reto. Se o jogador
        mantiver a distância até o fim, reaparece sem bote."""
        self.iniciar_invisibilidade(CFG.furtivo_preset)
        self._pos_perseguicao.update(self.posicao)
        bote = False
        try:
            while self.invisibilidade is not None and self.invisibilidade.oculta:
                self._buffar(CFG.furtivo_buff)
                self.perseguir()
                if self.fase_invisibilidade == OCULTO and self.dist_jogador() <= CFG.furtivo_dist_bote:
                    bote = True
                    break
                yield
        finally:
            self._tirar_buff()
            self.encerrar_invisibilidade()
        if bote:
            yield from self._esperar(CFG.furtivo_preparo_ms)
            direcao = yield from self._dash(CFG.furtivo_bote_preset)
            yield from self._esperar(CFG.furtivo_recuperacao_ms, direcao.x)
        else:
            yield from self._reaparecer()
        self.agendar('furtivo')

    # ------------------------------------------------------------ invisibilidade defensiva
    def rotina_defensiva(self):
        """Sem escudo: some, foge despistando e regenera. Acaba com o escudo cheio ou com o jogador
        chegando perto: nesse caso, dash + cone fino, e volta ao ataque com o escudo que tiver."""
        inicio = self._agora
        self._troca_fuga_em = inicio       # sorteia um rumo já neste frame
        cacado = False
        self.iniciar_invisibilidade(CFG.fuga_preset)
        try:
            while True:
                fugindo_ha = self._agora - inicio
                if fugindo_ha >= CFG.fuga_min_ms:
                    cacado = self.dist_jogador() <= CFG.fuga_dist_limite
                    if cacado or self.escudo_atual >= self.escudo_maximo:
                        break
                self._buffar(CFG.fuga_sprint_buff if fugindo_ha < CFG.fuga_sprint_ms else CFG.fuga_buff)
                self.fugir()
                self._regenerar_escudo()
                yield
        finally:
            self._tirar_buff()
            self.encerrar_invisibilidade()
        if cacado:
            direcao = yield from self._dash(CFG.contra_dash_preset)
            self.is_inofensivo = True
            try:
                yield from self._esperar(self._cone(direcao, CFG.contra_cone_preset), direcao.x)
                yield from self._esperar(CFG.contra_recuperacao_ms)
            finally:
                self.is_inofensivo = False
        else:
            yield from self._reaparecer()

    def _regenerar_escudo(self):
        ganho = self.escudo_maximo * self._dt * 1000 / CFG.regen_ms
        if ganho > 0:
            aplicar(self, Escudo(ganho))

    # ------------------------------------------------------------ anti-stuck
    def rotina_antistuck(self):
        """Preso longe do jogador: some, reaparece perto e segue a luta."""
        self.iniciar_invisibilidade(CFG.antistuck_preset)
        try:
            while self.fase_invisibilidade == FADE_OUT:
                self._parar()
                yield
            self.realizar_teleporte()
            while self.invisibilidade is not None:
                self._parar()
                yield
        finally:
            self.encerrar_invisibilidade()
