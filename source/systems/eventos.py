"""Barramento de eventos de jogo, síncrono e mínimo (roteiro B4).

Por que existe: a memória dos bosses (F3) quer "dano por habilidade", o áudio (G4) quer gatilhos e
a pontuação poderia ser somada durante a partida. Sem o barramento, cada um se acoplaria ao
`CollisionManager`. `emitir` chama os assinantes na hora, na ordem em que assinaram; a exceção de
um assinante sobe (é bug nosso, não pode sumir). As assinaturas valem por partida: o
`Game._resetar_estado_jogo` chama `limpar()`.

Uso:  from source.systems.eventos import eventos, INIMIGO_MORREU
      eventos.assinar(INIMIGO_MORREU, lambda inimigo: ...)
"""

# nome -> dados enviados (por palavra-chave)
INIMIGO_MORREU = 'inimigo_morreu'   # inimigo: morreu em combate e saiu do mundo (CollisionManager)
DANO_CAUSADO = 'dano_causado'       # alvo, dano (Dano), valor final: o golpe entrou (receber_dano, E1)
BOSS_DERROTADO = 'boss_derrotado'   # boss, fase: o boss da fase caiu (Game.boss_derrotado)
FASE_TROCADA = 'fase_trocada'       # fase: a fase nova, no meio do fade (StageManager)

EVENTOS = frozenset({INIMIGO_MORREU, DANO_CAUSADO, BOSS_DERROTADO, FASE_TROCADA})


class BarramentoEventos:
    def __init__(self):
        self._assinantes = {nome: [] for nome in EVENTOS}

    def _lista(self, nome):
        try:
            return self._assinantes[nome]
        except KeyError:
            raise ValueError(f'evento desconhecido: {nome!r} (conhecidos: {sorted(EVENTOS)})') from None

    def assinar(self, nome, funcao):
        if not callable(funcao):
            raise TypeError(f'assinante de {nome!r} precisa ser chamável, veio {funcao!r}')
        self._lista(nome).append(funcao)

    def emitir(self, nome, **dados):
        # Cópia: quem assinar durante a emissão só recebe a partir da próxima.
        for funcao in tuple(self._lista(nome)):
            funcao(**dados)

    def limpar(self):
        for lista in self._assinantes.values():
            lista.clear()


eventos = BarramentoEventos()
