"""
Relógio de jogo (em milissegundos) que SÓ avança enquanto a simulação roda.

Por que existe: o projeto usava pygame.time.get_ticks() (relógio de parede)
para cooldowns, duração de projéteis, i-frames, timers de boss etc. Esse
relógio continua correndo durante pausa, tela de level-up e fade; ao voltar
ao jogo, projéteis já tinham expirado, bosses disparavam ataques acumulados e
o jogador perdia/ganhava invencibilidade. Com este relógio, "agora()" fica
congelado fora do estado 'jogando'.

Uso:  from source.systems.gameclock import relogio
      agora = relogio.agora()
"""

# Começa alto de propósito: o código legado inicializa "ultimo_x = 0" esperando
# que get_ticks() já seja grande (cooldowns "prontos" no início da partida).
_OFFSET_INICIAL_MS = 60_000


class GameClock:
    def __init__(self):
        self.reiniciar()

    def avancar(self, delta_time):
        """Chamado UMA vez por frame simulado, com dt em segundos."""
        self._ms += delta_time * 1000.0

    def agora(self):
        return int(self._ms)

    def reiniciar(self):
        """Volta ao início. Chamado a cada partida nova (Game._resetar_estado_jogo)."""
        self._ms = float(_OFFSET_INICIAL_MS)


relogio = GameClock()


PASSO_FIXO = 1 / 60          # s: o mesmo dt que os testes usam
MAX_PASSOS_POR_FRAME = 5


class AcumuladorPassoFixo:
    """Converte o tempo real de cada frame em N passos de simulação de tamanho fixo.

    Por que existe: com dt variável a física (empurrão de parede, cooldowns, velocidade)
    dependia do FPS. Com passo fixo o jogo roda igual em qualquer máquina e igual aos testes.
    Frame lento demais gera no máximo `max_passos` e o atraso restante é descartado: sem isso,
    cada frame lento pediria mais passos, que deixariam o próximo frame mais lento (espiral).
    """

    def __init__(self, passo=PASSO_FIXO, max_passos=MAX_PASSOS_POR_FRAME):
        if passo <= 0 or max_passos < 1:
            raise ValueError('passo deve ser > 0 e max_passos >= 1')
        self.passo = passo
        self.max_passos = max_passos
        self.acumulado = 0.0

    def passos(self, dt_real):
        """Quantos `update(passo)` cabem depois de somar `dt_real` (s) ao acumulado."""
        self.acumulado += max(0.0, dt_real)
        # A folga de 1e-9 evita perder um passo por arredondamento (ex.: 3 × 1/60).
        n = int((self.acumulado + 1e-9) / self.passo)
        if n >= self.max_passos:
            self.acumulado = 0.0   # descarta o atraso: o jogo desacelera em vez de travar
            return self.max_passos
        self.acumulado = max(0.0, self.acumulado - n * self.passo)
        return n
