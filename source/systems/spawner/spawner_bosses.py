# Bosses
from source.enemies.bosses.guilty import GuiltySpark
from source.enemies.bosses.arbiter import BossArbiter
from source.enemies.bosses.tartarus import Tartarus
from source.enemies.bosses.gravemind import FloodWarning
from source.enemies.bosses.didact import Didact
from source.enemies.bosses.warden import DomainConsciousness
from source.enemies.bosses.harbinger import Harbinger
from source.enemies.bosses.jega import Jega

# Minibosses
from source.enemies.minibosses.hunter import Hunter
from source.enemies.minibosses.zealot import Zealot
from source.enemies.minibosses.scarab import Scarab
from source.enemies.minibosses.knight import Knight

# Bosses respectivos de cada fase
PHASE_BOSSES = {
    1: ['hunter'],
    0: ['warden'],
    1: ['zealot'],
    2: ['guilty'], 
    3: ['scarab'],           
    4: ['arbiter'],
    5: ['tartarus'],
    6: ['gravemind'],
    7: ['knight'],
    8: ['didact'],
    9: ['jega'],
}


# Mapeamento de classes para facilitar o código
BOSS_CLASSES = {
    'hunter': Hunter, 
    'zealot': Zealot, 
    'guilty': GuiltySpark, 
    'scarab': Scarab, 
    'arbiter': BossArbiter,
    'tartarus': Tartarus,
    'gravemind': FloodWarning, 
    'knight' : Knight, 
    'didact': Didact, 
    'warden': DomainConsciousness,
    'harbinger': Harbinger, 
    'jega': Jega
}

# Hardcode do momento de spawn de cada boss
CRONOGRAMA_BOSSES = {
    'hunter': 60,
    'zealot': 120,
    'guilty': 180,
    'scarab': 240,
    'arbiter': 300,
    'tartarus': 360,
    'gravemind': 500,
    'knight': 600,
    'didact': 700,
    'warden': 840,
    'jega': 1080,
    'harbinger': 1200
}