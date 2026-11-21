import random
import pygame
from source.systems.gameclock import relogio
from .config import CFG, FASES

V2 = pygame.math.Vector2


class ArbiterSetup:
    def inicializar_habilidades(self):
        agora = relogio.agora()

        # --- fases ---
        self.fase = 1
        self.fase_cfg = FASES[0]
        self.transicao_pendente = False

        # --- maquina de estados (cada habilidade e uma rotina/gerador) ---
        self.estado_habilidade = 'idle'
        self.rotina = None
        self.ultima_habilidade = None
        self.wait = 0                      # exaustao pos-habilidade (ms)
        self._agora = agora
        self._dt = 0.0

        # --- cooldowns: nome -> instante (ms) em que volta a ficar disponivel ---
        self.cd = {nome: agora + ms for nome, ms in CFG.cooldown_inicial.items()}

        # --- invocacao ---
        self.elites_invocados = []

        # --- movimento / percepcao ---
        self._dir_mov = None               # None = perseguir o jogador (comportamento base)
        self._lado_strafe = random.choice((-1, 1))
        self._troca_lado_em = agora + random.randint(*CFG.strafe_troca_ms)
        self._flip_valido_em = 0
        self._pos_jogador_ant = V2(self.jogador.posicao)
        self._vel_jogador = V2(0, 0)

        # --- anti-stuck ---
        self.ultimo_check_posicao = agora
        self._pos_ant_frame = V2(self.posicao)
        self._caminho_livre = 0.0          # px percorridos desde o ultimo check (so conta fora de habilidades)
