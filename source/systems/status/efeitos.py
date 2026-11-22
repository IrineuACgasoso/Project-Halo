"""Efeitos de status (buffs e debuffs): só dados, validados na criação.

Parâmetro inválido é bug de quem cria o efeito e vira `ValueError` na hora.
- Porcentagens são frações: 0.3 = 30%.
- Durações em ms de jogo. `None` = sem fim, só nos buffs (quem aplica remove com `remover`).
"""
import math
from dataclasses import dataclass

# 1000%: ninguém dá esse bônus de propósito; pega quem passa 30 querendo dizer 30%.
TETO_PORCENTAGEM = 10.0


def _exigir_duracao(efeito, ilimitada_permitida):
    duracao = efeito.duracao_ms
    if duracao is None:
        if ilimitada_permitida:
            return
        raise ValueError(f'{type(efeito).__name__}: duracao_ms é obrigatória')
    if not (math.isfinite(duracao) and duracao > 0):
        raise ValueError(f'{type(efeito).__name__}: duracao_ms precisa ser > 0 (veio {duracao!r})')


def _exigir_porcentagem(efeito, maximo, aceita_maximo=True):
    p = efeito.porcentagem
    dentro = 0 < p <= maximo if aceita_maximo else 0 < p < maximo
    if not (math.isfinite(p) and dentro):
        limite = f'<= {maximo}' if aceita_maximo else f'< {maximo}'
        raise ValueError(f'{type(efeito).__name__}: porcentagem precisa ser > 0 e {limite} '
                         f'(fração: 0.3 = 30%; veio {p!r})')


def _exigir_positivo(efeito, campo):
    valor = getattr(efeito, campo)
    if not (math.isfinite(valor) and valor > 0):
        raise ValueError(f'{type(efeito).__name__}: {campo} precisa ser > 0 (veio {valor!r})')


# ── Debuffs ──────────────────────────────────────────────────────────────────
@dataclass(frozen=True, slots=True)
class Lentidao:
    """Reduz a velocidade de movimento. Entre fontes diferentes, vale a mais forte."""
    porcentagem: float          # 1.0 = parado
    duracao_ms: float

    def __post_init__(self):
        _exigir_porcentagem(self, 1.0)
        _exigir_duracao(self, False)


@dataclass(frozen=True, slots=True)
class Atordoamento:
    """Sem mover, atacar nem causar dano de contato."""
    duracao_ms: float

    def __post_init__(self):
        _exigir_duracao(self, False)


@dataclass(frozen=True, slots=True)
class Queimadura:
    """`dps` de dano por segundo durante o efeito, e corta `reducao_cura` de toda cura de vida recebida.
    Entre fontes diferentes, o DPS soma e o corte de cura é o maior."""
    dps: float
    duracao_ms: float
    reducao_cura: float = 0.0   # 1.0 = nenhuma cura

    def __post_init__(self):
        _exigir_positivo(self, 'dps')
        _exigir_duracao(self, False)
        if not (math.isfinite(self.reducao_cura) and 0 <= self.reducao_cura <= 1):
            raise ValueError(f'Queimadura: reducao_cura precisa estar entre 0 e 1 (veio {self.reducao_cura!r})')


@dataclass(frozen=True, slots=True)
class Fraqueza:
    """O alvo recebe +porcentagem de dano de todas as fontes. Entre fontes diferentes, soma."""
    porcentagem: float
    duracao_ms: float

    def __post_init__(self):
        _exigir_porcentagem(self, TETO_PORCENTAGEM)
        _exigir_duracao(self, False)


@dataclass(frozen=True, slots=True)
class Cegueira:
    """Só no jogador: a tela fica preta fora de um círculo de `raio` px em volta dele.
    Entre fontes diferentes, vale o menor raio."""
    raio: float
    duracao_ms: float

    def __post_init__(self):
        _exigir_positivo(self, 'raio')
        _exigir_duracao(self, False)


# ── Buffs com duração (ou sem fim) ───────────────────────────────────────────
@dataclass(frozen=True, slots=True)
class BuffDano:
    """+porcentagem no dano causado (vale em todo `Dano` cuja fonte é o alvo do buff). Soma."""
    porcentagem: float
    duracao_ms: float | None = None

    def __post_init__(self):
        _exigir_porcentagem(self, TETO_PORCENTAGEM)
        _exigir_duracao(self, True)


@dataclass(frozen=True, slots=True)
class BuffVelocidade:
    """+porcentagem na velocidade de movimento. Soma."""
    porcentagem: float
    duracao_ms: float | None = None

    def __post_init__(self):
        _exigir_porcentagem(self, TETO_PORCENTAGEM)
        _exigir_duracao(self, True)


@dataclass(frozen=True, slots=True)
class BuffCadencia:
    """Só no jogador: os cooldowns das armas encolhem `porcentagem`. Entre fontes diferentes,
    multiplica (2 × 50% = 75%), então o cooldown nunca chega a zero."""
    porcentagem: float          # < 1
    duracao_ms: float | None = None

    def __post_init__(self):
        _exigir_porcentagem(self, 1.0, aceita_maximo=False)
        _exigir_duracao(self, True)


# ── Instantâneos ─────────────────────────────────────────────────────────────
@dataclass(frozen=True, slots=True)
class Escudo:
    """Soma `valor` ao escudo, até o escudo máximo do alvo (sem máximo, não faz nada)."""
    valor: float

    def __post_init__(self):
        _exigir_positivo(self, 'valor')


@dataclass(frozen=True, slots=True)
class Cura:
    """Soma `valor` à vida, até a vida máxima, menos o corte da queimadura."""
    valor: float

    def __post_init__(self):
        _exigir_positivo(self, 'valor')


TEMPORARIOS = frozenset({Lentidao, Atordoamento, Queimadura, Fraqueza, Cegueira,
                         BuffDano, BuffVelocidade, BuffCadencia})
INSTANTANEOS = frozenset({Escudo, Cura})
SO_NO_JOGADOR = frozenset({Cegueira, BuffCadencia})

# Bosses e minibosses: o stun deles é mecânica própria (roteiro §8, item 8).
IMUNIDADES_CHEFE = frozenset({Atordoamento, Lentidao})
