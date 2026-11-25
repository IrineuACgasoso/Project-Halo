import random

from source.systems.gameclock import relogio
from .config import CFG


class ArbiterSetup:
    def inicializar_habilidades(self):
        """Estado só do Arbiter (o do motor, fases, cooldowns e anti-stuck, é da BossBase)."""
        agora = relogio.agora()

        # --- escudo de energia (na mesma escala de dificuldade da vida) ---
        self.adicionar_escudo(CFG.escudo * self.vida_maxima / CFG.vida)
        self.sem_escudo = False            # quebrou e ainda não encheu de novo: a postura entra em jogo
        self._escudo_quebrou = False       # pede o combo na próxima decisão livre
        self._ultimo_dano = agora
        self._dano_recente = 0.0           # média que esquece (esquiva tática)

        # --- postura: 'neutra' (com escudo), 'avanco' ou 'recuo' (sem escudo) ---
        self.postura = 'neutra'
        self._furia_ate = None             # Fúria Honorável: fim do buff de velocidade

        # --- golpes ---
        self.is_inofensivo = False
        self._olhar_x = None               # lado forçado no frame (dash); None = olha para o jogador
        self._costas = None                # (eixo das costas, fim em ms): atordoado e exposto
        self._grito_ate = 0                # vfx do grito
        self._salto = None                 # salto em curso (desenha a sombra)

        # --- fora da rotina (bombardeio, invocação): quando pode de novo ---
        self.cd_fora = {nome: agora + ms for nome, ms in CFG.cooldown_fora_inicial.items()}
        self.elites_invocados = []

        # --- movimento ---
        self._lado_strafe = random.choice((-1, 1))
        self._troca_lado_em = agora + random.randint(*CFG.strafe_troca_ms)
        self._flip_valido_em = 0
