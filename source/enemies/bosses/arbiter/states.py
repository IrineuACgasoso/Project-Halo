import random

from .config import CFG

# nomes de estado (mantém os 3 que o código original usava)
ESTADOS = {
    'carabina': 'shooting', 'invocacao': 'summoning', 'furtivo': 'stealth',
    'lamina': 'blade', 'granada': 'grenade',
    'antistuck': 'antistuck_combat', 'transicao': 'phase_shift',
}


class ArbiterAI:
    """Decisão do Arbiter. O ciclo (rotinas, cooldowns, fases, anti-stuck) é da BossBase."""

    def preparar_frame(self, delta_time):
        # a camuflagem é uma máquina da classe base: avança sempre, em qualquer estado
        if self.invis_phase is not None:
            self.atualizar_invisibilidade(delta_time * 1000)
        self._resetar_movimento()

    def escolher_habilidade(self, agora):
        dist = self.contexto.dist
        self._podar_elites()

        # Invocar reforços tem prioridade absoluta (como no original), respeitando o teto de Elites
        if self.pronto('invocacao') and len(self.elites_invocados) < self.fase_cfg.max_elites:
            return 'invocacao'

        pesos = {}
        if self.pronto('lamina') and dist <= self._raio_lamina() * 0.95:
            pesos['lamina'] = 6
        if self.pronto('granada') and CFG.granada_dist_min <= dist <= CFG.granada_dist_max:
            pesos['granada'] = 4
        if self.pronto('carabina') and dist <= CFG.carabina_alcance:
            pesos['carabina'] = 4
        if self.pronto('furtivo'):
            pesos['furtivo'] = 2 + self.fase

        if not pesos:
            return None
        if self.ultima_habilidade in pesos:         # evita repetir a mesma habilidade em sequência
            pesos[self.ultima_habilidade] *= 0.3
        return random.choices(list(pesos), weights=list(pesos.values()))[0]

    def _esperar(self, ms, strafe=0.0):
        """Sub-rotina: passa `ms` de tempo de jogo parado (ou circulando se strafe > 0)."""
        fim = self._agora + ms
        while self._agora < fim:
            if strafe > 0:
                self._strafe(strafe)
            else:
                self._parar()
            yield

