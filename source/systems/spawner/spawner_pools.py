# Inimigos Base
from source.enemies.standard.grunt import GruntRed, GruntBlue, SpaceGrunt
from source.enemies.standard.jackal import Jackal, JackalSniper
from source.enemies.standard.elite import Elite, ReachElite, Halo4Elite
from source.enemies.standard.brute import Brute
from source.enemies.standard.infection import Infection, FloodElite, FloodMarine, FloodCarry
from source.enemies.standard.sentinel import Sentinel
from source.enemies.standard.crawler import Crawler
from source.enemies.standard.watcher import Watcher
from source.enemies.standard.soldier import Soldier


# OTIMIZAÇÃO COM PESOS: { fase: { "classes": [], "pesos": [] } }
PHASE_POOLS = {
    0: {
        "classes": [GruntBlue, GruntRed, Jackal, JackalSniper, Elite],
        "pesos": [40, 45, 9, 1, 5]  # 85% Grunt, 10% Jackal, 5% Elite
    },
    1: {
        "classes": [Infection, GruntRed, GruntBlue, Jackal, JackalSniper, Elite],
        "pesos": [40, 20, 10, 19, 1, 10]
    },
    2: {
        "classes": [Infection, FloodElite, FloodMarine, FloodCarry, GruntRed, Jackal, JackalSniper, Elite, Sentinel],
        "pesos": [20, 8, 8, 4, 20, 19, 1, 10, 10]
    },
    3: {
        "classes": [GruntRed, Jackal, Elite, Brute],
        "pesos": [40, 20, 20, 20]
    },
    4: {
        "classes": [Infection, FloodElite, FloodMarine, FloodCarry, GruntRed, Jackal, Elite, Brute],
        "pesos": [20, 10, 10, 5, 20, 15, 10, 10]
    },
    5: {
        "classes": [GruntRed, Jackal, Elite, Brute],
        "pesos": [20, 20, 10, 50]
    },
    6: {
        "classes": [Infection, FloodElite, FloodMarine, FloodCarry, GruntRed, Jackal, Elite, Brute, Sentinel],
        "pesos": [5, 5, 5, 5, 10, 10, 20, 20, 20]
    },
    7: {
        "classes": [GruntRed, Jackal, Brute, Sentinel],
        "pesos": [20, 20, 40, 20]
    },
    8: {
        "classes": [Infection, FloodElite, FloodMarine, FloodCarry, Sentinel],
        "pesos": [40, 20, 20, 10, 10]
    },
    9: {
        "classes": [SpaceGrunt, Jackal, Halo4Elite, Soldier, Crawler, Watcher],
        "pesos": [10, 10, 10, 40, 20, 10]
    }
    # Adicione as outras fases seguindo o padrão
}

DEFAULT_POOL = {
    "classes": [GruntRed],
    "pesos": [100]
}

