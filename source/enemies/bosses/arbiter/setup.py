import random
from source.systems.gameclock import relogio
from .config import CFG


class ArbiterSetup:
    def inicializar_habilidades(self):
        """Estado só do Arbiter (o do motor, fases, cooldowns e anti-stuck, é da BossBase)."""
        agora = relogio.agora()

        # --- invocação ---
        self.elites_invocados = []

        # --- movimento ---
        self._lado_strafe = random.choice((-1, 1))
        self._troca_lado_em = agora + random.randint(*CFG.strafe_troca_ms)
        self._flip_valido_em = 0
