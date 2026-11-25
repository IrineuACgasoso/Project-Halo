"""IA de utilidade e memória adaptativa dos bosses (roteiro F3).

Cada habilidade pronta recebe uma nota:  peso × distância × `pontuar_<nome>(ctx)` × repetição × memória.
Com uma claramente melhor, é ela; entre as que estão perto da melhor (`MARGEM`), sorteio pela nota.
Se nem a melhor serve bem (`EXIGENCIA`), o boss espera a situação mudar, até a paciência acabar.
A memória vale só para esta luta: compara o dano por uso de cada habilidade com o da média.
"""
import math
import random
from dataclasses import dataclass

MARGEM = 0.75               # concorre quem tem pelo menos esta fração da melhor nota
REPETICAO = 0.3             # a última habilidade usada vale menos
EXIGENCIA = 0.3             # nota mínima para agir logo...
PACIENCIA_MS = 2000         # ...que cai até zero em tanto tempo com algo pronto
NOTA_NA_BORDA = 0.35        # no limite do alcance; sobe até 1 na faixa ideal

ESQUECIMENTO = 0.8          # a cada uso, o passado da habilidade pesa menos (ela pode se recuperar)
USOS_DE_CONFIANCA = 2.0     # usos "na média" somados a cada conta: um golpe de sorte não decide
FATOR_MEMORIA = (0.6, 1.5)  # até onde a memória mexe na nota


@dataclass(frozen=True)
class Habilidade:
    """O que a IA sabe de uma habilidade (`HABILIDADES` do boss)."""
    peso: float
    alcance: tuple = (0, math.inf)      # fora disto não é usada
    ideal: tuple | None = None          # nota cheia; None = todo o alcance
    memoria: bool = True                # False = não fere com algo criado por ela (invocação, contato)

    def nota_distancia(self, dist):
        minimo, maximo = self.alcance
        if not minimo <= dist <= maximo:
            return 0.0
        perto, longe = self.alcance if self.ideal is None else self.ideal
        if dist < perto:
            fracao = (dist - minimo) / (perto - minimo)
        elif dist > longe:
            # alcance sem fim: a nota cai com a distância, sem chegar à da borda
            fracao = longe / dist if math.isinf(maximo) else (maximo - dist) / (maximo - longe)
        else:
            return 1.0
        return NOTA_NA_BORDA + (1.0 - NOTA_NA_BORDA) * fracao


class MemoriaDeCombate:
    """Dano por uso de cada habilidade nesta luta."""

    def __init__(self, nomes):
        self.usos = {nome: 0.0 for nome in nomes}
        self.dano = {nome: 0.0 for nome in nomes}

    def registrar_uso(self, nome):
        if nome in self.usos:
            self.usos[nome] = self.usos[nome] * ESQUECIMENTO + 1.0
            self.dano[nome] *= ESQUECIMENTO

    def registrar_dano(self, nome, valor):
        if nome in self.dano and math.isfinite(valor):     # golpe letal (infinito) não ensina nada
            self.dano[nome] += valor

    def fator(self, nome):
        """1 = na média (ou sem dados); acima, a habilidade está funcionando contra este jogador."""
        usos = sum(self.usos.values())
        media = sum(self.dano.values()) / usos if usos else 0.0
        if media <= 0 or nome not in self.usos:
            return 1.0
        por_uso = (self.dano[nome] + USOS_DE_CONFIANCA * media) / (self.usos[nome] + USOS_DE_CONFIANCA)
        minimo, maximo = FATOR_MEMORIA
        return max(minimo, min(maximo, por_uso / media))


class Decisor:
    """Escolhe a habilidade de um boss. A memória nasce com ele (uma por luta)."""

    def __init__(self, habilidades):
        self.habilidades = habilidades
        self.memoria = MemoriaDeCombate([n for n, h in habilidades.items() if h.memoria])
        self._esperando_desde = None

    def notas(self, boss):
        """Nome -> nota (> 0) do que dá para usar agora."""
        ctx = boss.contexto
        notas = {}
        for nome, habilidade in self.habilidades.items():
            if not boss.pronto(nome):
                continue
            nota = habilidade.peso * habilidade.nota_distancia(ctx.dist)
            pontuar = getattr(boss, f'pontuar_{nome}', None)
            if nota > 0 and pontuar is not None:
                nota *= pontuar(ctx)
            if nota > 0:
                if nome == boss.ultima_habilidade:
                    nota *= REPETICAO
                notas[nome] = nota * self.memoria.fator(nome)
        return notas

    def escolher(self, boss, agora):
        notas = self.notas(boss)
        if not notas:
            self._esperando_desde = None
            return None
        if self._esperando_desde is None:
            self._esperando_desde = agora
        melhor = max(notas.values())
        pressa = min(1.0, (agora - self._esperando_desde) / PACIENCIA_MS)
        if melhor < EXIGENCIA * (1.0 - pressa):
            return None
        self._esperando_desde = None
        finalistas = {nome: nota for nome, nota in notas.items() if nota >= melhor * MARGEM}
        if len(finalistas) == 1:
            return next(iter(finalistas))
        return random.choices(list(finalistas), weights=list(finalistas.values()))[0]
