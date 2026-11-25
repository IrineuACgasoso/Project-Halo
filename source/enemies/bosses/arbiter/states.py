"""Decisão do Arbiter: um guerreiro completo que avança e recua por tática.

- Com escudo: postura neutra. A distância escolhe o golpe (granada e carabina de média/longa,
  investida e salto de média/curta, lâmina colado, emboscada de longe) e a vida do jogador o puxa
  para cima (quanto menos vida o jogador tem, mais perto ele luta e mais valem os golpes de espada).
- Quebrou o escudo: grito + combo de 5 dashes (reação, `pensar`). Depois, até o escudo voltar a
  encher, as vontades brigam a cada frame: a vida dele, o jogador longe e a escolta de Elites viva
  pedem recuo; o jogador fraco pede avanço (`_avaliar_postura`).
- Muito dano em pouco tempo: esquiva lateral (reação), às vezes com spray camuflado.
- Fora da rotina, sem parar o que está fazendo: bombardeio do Phantom e invocação de Elites.
O ciclo (rotinas, cooldowns, anti-stuck, nota da IA) é da BossBase."""
import math

from source.systems.status import Escudo, aplicar
from source.utils.vetores import no_cone

from .config import CFG, COS_COSTAS


class ArbiterAI:
    def preparar_frame(self, delta_time):
        # a camuflagem é uma máquina da classe base: avança sempre, em qualquer estado
        self.atualizar_invisibilidade(delta_time)
        self._resetar_movimento()

    # ------------------------------------------------------------ percepção
    def perceber(self, agora, delta_time):
        super().perceber(agora, delta_time)
        self._trocar_lado_strafe(agora)
        self._dano_recente *= math.exp(-delta_time * 1000 / CFG.esquiva_memoria_ms)
        self._regenerar_escudo(agora, delta_time)
        self._atualizar_furia(agora)
        self._avaliar_postura(agora)
        if self._costas is not None and agora >= self._costas[1]:
            self._costas = None
        self._fora_da_rotina()

    @property
    def vida_jogador(self):
        j = self.jogador
        return j.vida_atual / j.vida_maxima if j.vida_maxima > 0 else 1.0

    @property
    def agressividade(self):
        """0 com o jogador de vida cheia, 1 com ele sem vida."""
        return max(0.0, min(1.0, 1.0 - self.vida_jogador))

    def _avaliar_postura(self, agora):
        if not self.sem_escudo:
            self.postura = 'neutra'
            return
        if self._furia_ate is not None:          # Fúria Honorável: espada antes de pensar em recuar
            self.postura = 'avanco'
            return
        perto, longe = CFG.dist_afastou
        afastou = max(0.0, min(1.0, (self.contexto.dist - perto) / (longe - perto)))
        escolta = min(1.0, len(self.escoltas_vivas) / CFG.escolta_cheia)
        nota = ((CFG.peso_vida_propria * (1.0 - self.contexto.razao_vida) + CFG.peso_distancia * afastou
                 + CFG.peso_escolta * escolta)
                * self.fase_cfg.mult_recuo - CFG.peso_vida_jogador * self.agressividade)
        if nota >= CFG.limiar_recuo:
            self.postura = 'recuo'
        elif nota <= CFG.limiar_avanco or self.postura == 'neutra':
            self.postura = 'avanco'
        # entre os limiares mantém a postura (sem tremer de um lado para o outro)

    # ------------------------------------------------------------ escudo
    def _regenerar_escudo(self, agora, delta_time):
        """Volta sozinho depois de `escudo_atraso_ms` sem tomar dano (qualquer dano recomeça a conta)."""
        if self.escudo_atual >= self.escudo_maximo:
            if self.sem_escudo:
                self.sem_escudo = False
            if self._recarregando:
                self._recarregando = False
                self.escudo_cheio_vfx()
            return
        if agora - self._ultimo_dano >= CFG.escudo_atraso_ms:
            if not self._recarregando:
                self._recarregando = True
                self.recarga_vfx()
            ganho = self.escudo_maximo * delta_time * 1000 / CFG.escudo_regen_ms
            if ganho > 0:
                aplicar(self, Escudo(ganho))
        else:
            self._recarregando = False

    def absorver_dano(self, valor):
        super().absorver_dano(valor)
        if valor > 0:
            self._ultimo_dano = self._agora
            self._dano_recente += valor

    def ao_quebrar_escudo(self):
        super().ao_quebrar_escudo()
        self.sem_escudo = True
        self._escudo_quebrou = True

    def ajustar_dano_recebido(self, valor, dano):
        """Atordoado depois da investida: pelas costas, o dano multiplica (como o Hunter)."""
        if self.costas_expostas and no_cone(self.posicao, self._costas[0], self.jogador.posicao, COS_COSTAS):
            return valor * CFG.costas_mult
        return valor

    @property
    def costas_expostas(self):
        return self._costas is not None and self._agora < self._costas[1]

    # ------------------------------------------------------------ decisão
    def pensar(self, agora, delta_time):
        """Reações antes da exaustão (`wait`): a troca de fase, o combo da quebra de escudo e a esquiva."""
        if self.transicao_pendente:
            self.wait = 0
        elif self._escudo_quebrou:
            self._escudo_quebrou = False
            if self.pronto('combo'):
                self.wait = 0
                self.iniciar('combo')
                return
        elif self._quer_esquivar():
            self.wait = 0
            self._dano_recente = 0.0
            self.iniciar('esquiva')
            return
        super().pensar(agora, delta_time)

    def _quer_esquivar(self):
        return (self.pronto('esquiva')
                and self._dano_recente >= CFG.esquiva_limiar * (self.vida_maxima + self.escudo_maximo))

    def _postura(self, nome):
        return CFG.mult_postura.get(self.postura, {}).get(nome, 1.0)

    def _espada(self, nome):
        """Golpes de espada: a postura e a vontade de acabar com um jogador fraco."""
        return self._postura(nome) * (1.0 + CFG.agressividade_melee * self.agressividade)

    # notas (a conta é do Decisor, F3)
    def pontuar_lamina(self, ctx):
        return self._espada('lamina') if ctx.dist <= self._raio_lamina() * 0.95 else 0.0

    def pontuar_investida(self, ctx):
        return self._espada('investida')

    def pontuar_salto(self, ctx):
        return self._espada('salto')

    def pontuar_granada(self, ctx):
        return self._postura('granada') * (CFG.bonus_parado if ctx.parado_ms >= CFG.parado_ms else 1.0)

    def pontuar_carabina(self, ctx):
        if not self.fase_cfg.carabina:
            return 0.0
        return self._postura('carabina') * (CFG.bonus_fuga if ctx.afastamento >= CFG.fuga_vel else 1.0)

    def pontuar_emboscada(self, ctx):
        """Caça quem foge."""
        return self._postura('emboscada') * (CFG.bonus_fuga if ctx.afastamento >= CFG.fuga_vel else 1.0)

    # ------------------------------------------------------------ sub-rotina
    def _esperar(self, ms, strafe=0.0, olhar_x=None):
        """Sub-rotina: passa `ms` de tempo de jogo parado (ou circulando se strafe > 0)."""
        fim = self._agora + ms
        while self._agora < fim:
            if strafe > 0:
                self._strafe(strafe)
            else:
                self._parar(olhar_x)
            yield
