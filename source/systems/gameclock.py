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
        self._ms = float(_OFFSET_INICIAL_MS)

    def avancar(self, delta_time):
        """Chamado UMA vez por frame simulado, com dt em segundos."""
        self._ms += delta_time * 1000.0

    def agora(self):
        return int(self._ms)


relogio = GameClock()
