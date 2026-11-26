
class TartarusSetup:
    def inicializar_habilidades(self):
        """Estado só do Tartarus (o do motor, fases, cooldowns e anti-stuck, é da BossBase)."""
        # --- golpes ---
        self.is_inofensivo = False
        self._olhar_x = None               # lado forçado no frame (dash, golpe); None = olha para o jogador
        self._salto = None                 # salto em curso
        self._acertou = False              # o golpe em curso acertou o jogador (`_lembrar_dano`)

        # --- Barreira do Punho de Rukt (ativa quando agora >= _sem_barreira_ate) ---
        self._sem_barreira_ate = 0
        self._barreira_estava = True
        self._quebra = None                # (início, fim) da queda longa (barra cheia)
        self.esquivas = 0                  # golpes pesados que erraram o jogador (a barra do HUD)
        self._rampage_pendente = False
        self._ofegante_ate = 0

        # --- Fúria e invocação ---
        self._furia = False
        self.cd_brutes = float('inf')      # só na Fúria (a transição agenda a primeira)
        self.brutes_invocados = []
