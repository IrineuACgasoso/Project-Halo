import pygame

class WardenSetup:
    def inicializar_habilidades(self):
        """Método principal que orquestra a inicialização de todos os subsistemas."""
        agora = pygame.time.get_ticks()

        self._inicializar_fsm()
        self._inicializar_combatente()       # Estado interno da IA do Combatente
        self._inicializar_chop(agora)
        self._inicializar_heavy_rifle(agora)
        self._inicializar_hardlight_laser(agora)
        self._inicializar_teleporte(agora)
        self._inicializar_stomp(agora)

    def _inicializar_fsm(self):
        self.estado_habilidade = 'idle'
        self.funcao_atual = 'COMBATENTE'
        self.wait = 0

    def _inicializar_combatente(self):
        """Estado interno da IA do Combatente (detecção de flanque)."""
        self._angulo_anterior_player = None
        self._arco_acumulado = 0.0
        self._modo_arco_ativo = False

    def _inicializar_chop(self, agora):
        self.start_chop = 0
        self.wait_chop = 500
        self.cooldown_chop = 8000
        self.ultimo_chop = agora

    def _inicializar_heavy_rifle(self, agora):
        self.start_heavy_rifle = 0
        self.wait_heavy_rifle = 400
        self.cooldown_heavy_rifle = 6000
        self.ultimo_heavy_rifle = agora

    def _inicializar_hardlight_laser(self, agora):
        from source.feats.effects import ContinuousBeam

        self.beam_principal = ContinuousBeam(
            owner=self,
            color=(255, 80, 0),
            largura_base=30,
            dano_por_segundo=240,
            suavizacao=0.10
        )
        self.duracao_laser = 2500
        self.tempo_inicio_laser = 0
        self.cooldown_laser = 8000
        self.ultimo_laser = agora

    def _inicializar_teleporte(self, agora):
        self.ultimo_tp = agora
        self.cooldown_tp = 6000
        self.tp_orb = None
        self.tp_destino = None
        self.alvo_reposicionamento = None

    def _inicializar_stomp(self, agora):
        self.stomp_ativo = False
        self.start_stomp = 0
        self.cooldown_stomp = 6000
        self.ultimo_stomp = agora