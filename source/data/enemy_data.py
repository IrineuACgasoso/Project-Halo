"""Perfis dos inimigos comuns (roteiro D4): o balanceamento fica aqui, não nas classes.

Cada classe de `enemies/standard/` lê o seu `PerfilInimigo` de `INIMIGOS`. Os valores são os
de nível 0: `EnemyScaling.aplicar_dificuldade` escala vida, dano e velocidade pelo nível do
jogador. O que não é balanceamento (sprite, variante, velocidade de animação, projéteis e IA)
continua na classe. Módulo só de dados (sem pygame).
"""
from dataclasses import dataclass
from types import MappingProxyType


def _fixo(dicionario):
    """Dict só de leitura: o perfil é frozen e as tabelas dele também."""
    return MappingProxyType(dict(dicionario))


# Tabelas de drop, no formato dos kwargs de `Items.spawn_drop`: item -> (quantidade, chance %, escala).
# A ordem importa: spawn_drop sorteia item por item.
DROP_PADRAO = _fixo({   # bosses e minibosses sem morrer() próprio também usam esta
    'exp_shard': (1, 100, 100),
    'big_shard': (1, 1, 100),
    'life_orb': (1, 1, 100),
    'upgrade': (1, 0.1, 100),
})
DROP_COVENANT_FORTE = _fixo({   # Elite e Brute
    'exp_shard': (3, 100, 100),
    'big_shard': (1, 2, 100),
    'life_orb': (1, 1, 100),
    'upgrade': (1, 0.5, 100),
})
_SEM_COOLDOWNS = _fixo({})


@dataclass(frozen=True)
class PerfilInimigo:
    vida: float
    dano: float            # dano de contato
    velocidade: float      # px/s
    # nome -> (mín, máx) em ms, sorteado por `novo_cooldown`
    cooldowns: MappingProxyType = _SEM_COOLDOWNS
    drops: MappingProxyType = DROP_PADRAO


def _perfil(vida, dano, velocidade, cooldowns=None, drops=DROP_PADRAO):
    return PerfilInimigo(vida, dano, velocidade, _fixo(cooldowns or {}), drops)


INIMIGOS = _fixo({
    # Covenant
    'grunt_red': _perfil(2, 10, 50, {'plasma': (8000, 12000)}),
    'grunt_blue': _perfil(2, 5, 65, {'plasma': (8000, 12000)}),
    'space_grunt': _perfil(5, 10, 35, {'plasma': (8000, 12000)}),
    'jackal': _perfil(15, 10, 50, {'tiro_inicial': (4500, 6000), 'tiro': (6000, 11000)}),
    'elite': _perfil(20, 20, 40, {'carabina': (3000, 7000)}, DROP_COVENANT_FORTE),
    'reach_elite': _perfil(45, 35, 80, {'carabina': (3000, 7000)}, DROP_COVENANT_FORTE),
    'halo4_elite': _perfil(30, 15, 60, {'carabina': (3000, 7000)}, DROP_COVENANT_FORTE),
    'brute': _perfil(30, 20, 75, {'dizimadora': (5000, 8000)}, DROP_COVENANT_FORTE),
})
