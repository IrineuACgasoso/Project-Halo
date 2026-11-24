"""Fases e decisão do Guilty. Ele passeia o tempo todo; só os feixes o fazem parar.

As invocações (chuva, armadilha, super sentinelas, flood) correm por fora, cada uma no seu tempo
(`invocacoes.py`). O ciclo (rotinas, cooldowns, anti-stuck) é da BossBase."""
import random

from .config import CFG


class GuiltyAI:
    def preparar_frame(self, delta_time):
        # Padrão de todo frame: azul, parado. A ronda e as rotinas sobrescrevem.
        self._parar()
        self._cor('azul')
        self.atualizar_invocacoes()

    def _cor(self, cor):
        self.animador.tocar(f'{cor}_destruido' if self.fase == 3 else cor)

    # ------------------------------------------------------------ fases
    def checar_fase(self):
        anterior = self.fase
        super().checar_fase()
        if self.fase != anterior:
            self.entrar_na_fase()

    def entrar_na_fase(self):
        """Corta o que estiver fazendo. Fase 2: barreira de volta. Fase 3: barreira no chão."""
        self.transicao_pendente = False
        self.interromper_rotina()
        self.encerrar_invocacoes()
        self.permitir_spawns_normais = False
        self.wait = 0
        self.ronda_ate = 0
        # Os tempos de espera recomeçam (só os da fase nova são lidos)
        self.cd = {nome: self._agora + ms for nome, ms in CFG.cooldown_inicial.items()}
        self.proxima_invocacao = {nome: self._agora + ms for nome, ms in CFG.intervalo_inicial.items()}
        if self.fase == 2:
            self.erguer_barreira()
        else:
            self.derrubar_barreira()

    # ------------------------------------------------------------ decisão
    def movimento_ocioso(self, agora):
        if self.fase < 3:
            self.rondar(agora, self._dt)

    def escolher_habilidade(self, agora):
        if self.fase == 1:
            return self._escolher_fase1()
        if self.fase == 2:
            return self._escolher_fase2()
        return 'teleporte'

    def _escolher_fase1(self):
        perto = self.contexto.dist_sq <= CFG.proximidade_dist ** 2
        return 'proximidade' if perto and self.pronto('proximidade') else None

    def _escolher_fase2(self):
        prontos = {'passear': True, 'laser': self.pronto('laser'), 'luz': self.invocacao_pronta('luz')}
        pesos = {nome: peso for nome, peso in CFG.pesos_fase2.items() if prontos[nome]}
        escolha = random.choices(list(pesos), weights=list(pesos.values()))[0]
        if escolha == 'laser':
            return 'laser'
        if escolha == 'luz':
            self.invocar_luz()      # sem parar a ronda: é contra ele mesmo que ela serve
        self.wait = random.randint(*CFG.passear_ms)
        return None
