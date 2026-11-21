import math
import random
import pygame
from .config import CFG, FASES

V2 = pygame.math.Vector2

# nomes de estado (mantem os 3 que o codigo original usava)
ESTADOS = {
    'carabina': 'shooting', 'invocacao': 'summoning', 'furtivo': 'stealth',
    'lamina': 'blade', 'granada': 'grenade',
    'antistuck': 'antistuck_combat', 'transicao': 'phase_shift',
}


class ArbiterAI:
    """Cada habilidade e uma ROTINA (gerador): `yield` = 1 frame. A IA so decide quando nao ha rotina ativa."""

    # --------------------------------------------------------------- loop
    def executar_estados(self, agora, delta_time, dist_sq):
        # a camuflagem e uma maquina da classe base: avanca sempre, em qualquer estado
        if self.invis_phase is not None:
            self.atualizar_invisibilidade(delta_time * 1000)

        self._resetar_movimento()

        if self.rotina is None:
            self._pensar(agora, delta_time, dist_sq)

        if self.rotina is not None:
            try:
                next(self.rotina)
            except StopIteration:
                self._finalizar_rotina(agora)

    # ------------------------------------------------------------- pensar
    def _pensar(self, agora, delta_time, dist_sq):
        self.estado_habilidade = 'idle'
        dist = math.sqrt(dist_sq)
        self._mov_idle(dist, agora)

        if self.checar_se_travou(agora, dist_sq):
            self._iniciar('antistuck', self.rotina_antistuck(), agora)
            return

        if self.wait > 0:
            self.wait -= delta_time * 1000
            return

        if self.transicao_pendente:
            self.transicao_pendente = False
            self._iniciar('transicao', self.rotina_transicao(), agora)
            return

        escolha = self._escolher_habilidade(agora, dist)
        if escolha is not None:
            rotina = {
                'carabina': self.rotina_carabina, 'lamina': self.rotina_lamina,
                'granada': self.rotina_granada, 'furtivo': self.rotina_furtivo,
                'invocacao': self.rotina_invocacao,
            }[escolha]()
            self._iniciar(escolha, rotina, agora)

    def _escolher_habilidade(self, agora, dist):
        pronto = lambda nome: agora >= self.cd[nome]
        self._podar_elites()

        # Invocar reforcos tem prioridade absoluta (como no original), respeitando o teto de Elites
        if pronto('invocacao') and len(self.elites_invocados) < self.fase_cfg.max_elites:
            return 'invocacao'

        pesos = {}
        if pronto('lamina') and dist <= self._raio_lamina() * 0.95:
            pesos['lamina'] = 6
        if pronto('granada') and CFG.granada_dist_min <= dist <= CFG.granada_dist_max:
            pesos['granada'] = 4
        if pronto('carabina') and dist <= CFG.carabina_alcance:
            pesos['carabina'] = 4
        if pronto('furtivo'):
            pesos['furtivo'] = 2 + self.fase

        if not pesos:
            return None
        if self.ultima_habilidade in pesos:         # evita repetir a mesma habilidade em sequencia
            pesos[self.ultima_habilidade] *= 0.3
        return random.choices(list(pesos), weights=list(pesos.values()))[0]

    # ------------------------------------------------------ ciclo de rotina
    def _iniciar(self, nome, rotina, agora):
        self.estado_habilidade = ESTADOS[nome]
        self.ultima_habilidade = nome
        self.rotina = rotina

    def _finalizar_rotina(self, agora):
        self.rotina = None
        self.estado_habilidade = 'idle'
        self._resetar_antistuck(agora)

    def _agendar(self, nome):
        """Reagenda o cooldown (sorteado e escalado pela fase) a partir de AGORA (fim da habilidade)."""
        lo, hi = CFG.cooldown[nome]
        self.cd[nome] = self._agora + int(self.novo_cooldown(lo, hi) * self.fase_cfg.mult_cooldown)

    def _esperar(self, ms, strafe=0.0):
        """Sub-rotina: passa `ms` de tempo de jogo parado (ou circulando se strafe > 0)."""
        fim = self._agora + ms
        while self._agora < fim:
            if strafe > 0:
                self._strafe(strafe)
            else:
                self._parar()
            yield

    # -------------------------------------------------------------- fases
    def _checar_fase(self):
        if self.vida_maxima <= 0:
            return
        razao = self.vida / self.vida_maxima
        nova = self.fase
        for i, f in enumerate(FASES, start=1):
            if i > nova and razao <= f.limiar_vida:
                nova = i
        if nova > self.fase:
            self.fase = nova
            self.fase_cfg = FASES[nova - 1]
            self.transicao_pendente = True

    # ----------------------------------------------------------- anti-stuck
    def _resetar_antistuck(self, agora):
        self.ultimo_check_posicao = agora
        self._caminho_livre = 0.0

    def checar_se_travou(self, agora, dist_sq):
        """Travado = quase nao andou (CAMINHO, nao deslocamento liquido) numa janela em que estava livre
        e longe do jogador. Deslocamento liquido dava falso positivo quando o strafe invertia de lado."""
        if agora - self.ultimo_check_posicao <= CFG.antistuck_janela:
            return False
        caminho = self._caminho_livre
        self._resetar_antistuck(agora)
        return caminho < CFG.antistuck_caminho_min and dist_sq > CFG.antistuck_dist_min_sq
