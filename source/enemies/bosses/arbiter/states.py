from .config import CFG

# nomes de estado (mantém os 3 que o código original usava)
ESTADOS = {
    'carabina': 'shooting', 'invocacao': 'summoning', 'furtivo': 'stealth',
    'lamina': 'blade', 'granada': 'grenade',
    'antistuck': 'antistuck_combat', 'transicao': 'phase_shift',
}


class ArbiterAI:
    """O que pesa na decisão do Arbiter. O ciclo e a escolha (`HABILIDADES`) são da BossBase."""

    def preparar_frame(self, delta_time):
        # a camuflagem é uma máquina da classe base: avança sempre, em qualquer estado
        self.atualizar_invisibilidade(delta_time)
        self._resetar_movimento()

    # ------------------------------------------------ notas (a conta é do Decisor, F3)
    def pontuar_lamina(self, ctx):
        return 1.0 if ctx.dist <= self._raio_lamina() * 0.95 else 0.0

    def pontuar_granada(self, ctx):
        return CFG.bonus_parado if ctx.parado_ms >= CFG.parado_ms else 1.0

    def pontuar_carabina(self, ctx):
        return CFG.bonus_fuga if ctx.afastamento >= CFG.fuga_vel else 1.0

    def pontuar_furtivo(self, ctx):
        """Cresce com a fase; caça quem foge."""
        return (2 + self.fase) / 6 * (CFG.bonus_fuga if ctx.afastamento >= CFG.fuga_vel else 1.0)

    def pontuar_invocacao(self, ctx):
        """Sem Elites é a prioridade; com a escolta quase cheia, só mais uma opção."""
        self._podar_elites()
        return max(0.0, 1.0 - len(self.elites_invocados) / self.fase_cfg.max_elites)

    def _esperar(self, ms, strafe=0.0):
        """Sub-rotina: passa `ms` de tempo de jogo parado (ou circulando se strafe > 0)."""
        fim = self._agora + ms
        while self._agora < fim:
            if strafe > 0:
                self._strafe(strafe)
            else:
                self._parar()
            yield
