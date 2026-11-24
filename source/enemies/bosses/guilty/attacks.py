"""Rotinas do Guilty (geradores: `yield` = 1 frame; todo `while` tem `yield`): os feixes e o teleporte."""
import pygame

from .config import CFG

OLHO = (21, -4)     # do centro do sprite ao olho, olhando para a direita


class GuiltyAttacks:
    @property
    def olho(self):
        """De onde saem os feixes, em relação a `posicao`."""
        x, y = OLHO
        return pygame.math.Vector2(x if self.animador.lado == 'right' else -x, y + self.flutuacao)

    def _disparar(self, feixe, cfg):
        """Sub-rotina: parado e vermelho, o feixe segue o jogador por `cfg.duracao_ms`."""
        feixe.mira_atual = self.posicao + self.olho
        self.feixe_ativo = feixe
        fim = self._agora + cfg.duracao_ms
        try:
            while self._agora < fim:
                self._parar()
                self._cor('vermelho')
                feixe.update(self._dt, self.jogador.posicao)
                self.game.camera.shake(intensidade=cfg.shake, duracao=100)
                yield
        finally:
            self.feixe_ativo = None

    # ------------------------------------------------------------ fase 1
    def rotina_proximidade(self):
        yield from self._disparar(self.feixe_proximidade, CFG.proximidade)
        self.agendar('proximidade')

    # ------------------------------------------------------------ fase 2
    def rotina_laser(self):
        fim = self._agora + CFG.laser_carga_ms
        while self._agora < fim:
            self._parar()
            self._cor('vermelho')
            self.game.camera.shake(intensidade=CFG.laser_shake_carga, duracao=100)
            yield
        yield from self._disparar(self.feixe_laser, CFG.laser)
        self.agendar('laser')

    # ------------------------------------------------------------ fase 3
    def rotina_teleporte(self):
        yield from self._teleportar()
        yield from self._esperar(CFG.tp_pausa_ms)
        yield from self._disparar(self.feixe_fase3, CFG.laser_fase3)
        self.wait = CFG.fase3_respiro_ms

    # ------------------------------------------------------------ anti-stuck
    def rotina_antistuck(self):
        yield from self._teleportar()

    # ------------------------------------------------------------ desenho
    def draw_laser(self, superficie, deslocamento):
        if self.feixe_ativo is not None:
            self.feixe_ativo.draw(superficie, deslocamento, self.olho)
