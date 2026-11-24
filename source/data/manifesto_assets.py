"""Manifesto de assets (roteiro D1): toda imagem que o jogo carrega, com escala e flags.

`MANIFESTO` tem o mesmo formato de `ASSETS` (dicts e listas), com uma `Imagem` em cada folha.
`feats/assets.py::carregar_assets` percorre esta árvore e monta `ASSETS` com as superfícies.
Módulo só de dados: não importa pygame nem carrega nada.
"""
from dataclasses import dataclass

from source.windows.settings.settings_constants import largura_tela, altura_tela

TELA = (largura_tela, altura_tela)


@dataclass(frozen=True)
class Imagem:
    arquivo: str                          # relativo a assets/img, separado por '/'
    escala: tuple[int, int] | None = None # None = tamanho original
    alpha: bool = True                    # convert_alpha(); False = convert() (fundo opaco)
    espelhar: bool = False                # flip horizontal, depois da escala


def quadros(pasta, nomes, escala, espelhar=False):
    """Uma Imagem por arquivo de `pasta`, todas na mesma escala."""
    return [Imagem(f'{pasta}/{nome}', escala, espelhar=espelhar) for nome in nomes]


def numerados(prefixo, fim, inicio=1):
    """['<prefixo><inicio>.png', ..., '<prefixo><fim>.png']"""
    return [f'{prefixo}{i}.png' for i in range(inicio, fim + 1)]


COV = 'enemies/covenant'
BOSS = 'enemies/bosses'
PROM = 'enemies/prometheans'
FLOOD = 'enemies/flood'

# Recortes do Scarab (casco, canhão e patas), por pose; as posições ficam em minibosses/scarab/recortes.py
_PATAS_SCARAB = ('frente', 'centro', 'tras')
PARTES_SCARAB = (
    'em_pe_corpo', 'em_pe_torreta', 'em_pe_torreta_b', 'em_pe_oculta', 'em_pe_oculta_alta',
    *(f'em_pe_{p}{s}' for p in _PATAS_SCARAB for s in ('', '_alta', '_dan', '_alta_dan')),
    *(f'{pose}_{parte}' for pose in ('caido', 'sentado')
      for parte in ('corpo', *(f'{p}{s}' for p in _PATAS_SCARAB for s in ('', '_dan')))),
)

MANIFESTO = {
    'projectiles': {chave: Imagem(f'projectiles/{arquivo}') for chave, arquivo in {
        'plasma': 'plasmagun.png',
        'carabin': 'carabin.png',
        'bcarabin': 'bcarabin.png',
        'needler': 'needler.png',
        'plasma_grenade': 'plasma_grenade.png',
        'm50': 'm50.png',
        'ar': 'ar.png',
        'energy_sword': 'energysword.png',
        'light_bullet': 'lightrifle.png',
        'dizimator': 'dizimator.png',
        'spike': 'spike.png',
        'acid_breath': 'acid.gif',
        'red_laser': 'redlaser.png',
        'blue_laser': 'bluelaser.png',
        'green_laser': 'greenlaser.png',
    }.items()},

    'icons': {chave: Imagem(f'icons/{arquivo}') for chave, arquivo in {
        'assault_rifle': 'ar.png',
        'grenade_launcher': 'plasma_grenade.png',
        'needler': 'needler.png',
        'carabin': 'carabin.png',
        'spartan_laser': 'spartan_laser.png',
        'shotgun': 'shotgun.png',
        'cortana': 'cortana.png',
        'mk2_shield': 'mk2.png',
        'arbiter': 'arbiter.png',
        'marine': 'marine.png',
        'energy_sword': 'energy_sword.png',
        'noble': 'noble.png',
        'light_rifle': 'light_rifle.png',
        'brick': 'brick.png',
        'sniper_rifle': 'sniper.png',
        'sidekick_pistol': 'sidekick.png',
        'machine_gun': 'machine_gun.png',
        'mjolnir_punch': 'mjolnir_punch.png',
        'dizimator': 'dizimator.png',
        'fuel_rod': 'fuel_rod.png',
        'warhog': 'warhog.png',
        'pelican': 'pelican.png',
    }.items()},

    'items': {chave: Imagem(f'items/{arquivo}') for chave, arquivo in {
        'exp_shard': 'expshard.png',
        'big_shard': 'bigshard.png',
        'life_orb': 'lifeorb.png',
        'light_bullet': 'lightbullet.png',
        'cafe': 'cafe.png',
    }.items()},

    'player': {
        'right': quadros('player', numerados('player', 3), (144, 144)),
        'left': quadros('player', numerados('player', 3), (144, 144), espelhar=True),
    },

    'buddies': {
        'cortana': quadros('buddies/cortana', numerados('cortana', 2), (128, 192)),
        'arbiter': quadros('buddies/arbiter', numerados('arbiter', 4), (192, 192)),
        'marine': quadros('buddies/marine', numerados('marine', 4), (96, 144)),
        'noble': quadros('buddies/noble', numerados('noble', 4), (144, 216)),
    },

    'enemies': {
        'hunter': [
            Imagem(f'{COV}/hunter/hunter1.png', (250, 250)),
            Imagem(f'{COV}/hunter/hunter2.png', (270, 270)),
        ],
        'zealot': quadros(f'{COV}/zealot', numerados('zealot', 4), (200, 200)),
        # azul, vermelha (atacando), azul destruída, vermelha destruída: ver CLIPS em guilty/config.py
        'guilty': quadros(f'{BOSS}/guilty', ['guilty.png', 'guilty2.png', 'guilty7.png', 'guilty4.png'], (100, 100)),
        'scarab': [Imagem(f'{COV}/scarab/scarab1.png', (1024, 1024))],   # o rect; quem aparece são as partes
        'scarab_partes': {variante: {nome: Imagem(f'{COV}/scarab/partes/{variante}/{nome}.png') for nome in PARTES_SCARAB}
                          for variante in ('default', 'damaged', 'broken')},
        'arbiter': quadros(f'{BOSS}/arbiter', numerados('boss', 4), (250, 250)),
        'tartarus': quadros(f'{BOSS}/tartarus', numerados('tartarus', 4), (192, 288)),
        'gravemind': {
            'final': quadros(f'{BOSS}/gravemind/final', numerados('final', 3), (900, 600)),
            'proto': quadros(f'{BOSS}/gravemind/proto', numerados('proto', 3), (750, 500)),
        },
        'knight': quadros(f'{PROM}/knight', numerados('command', 4), (250, 250)),
        'didact': {
            'default': quadros(f'{BOSS}/didact', numerados('did', 4), (250, 375)),
            'attack': [Imagem(f'{BOSS}/didact/didpull.png', (250, 375))],
            'cryptum': [Imagem(f'{BOSS}/didact/cryptum.png', (400, 400))],
        },
        'warden': {
            'default': quadros(f'{BOSS}/warden', ['warden.png', 'warden2.png', 'warden3.png'], (550, 550)),
            'clone': quadros(f'{BOSS}/warden', ['clone2.png', 'clone.png', 'clone3.png'], (500, 500)),
        },
        'guardian': [Imagem(f'{BOSS}/guardian/guardian1.png', (1500, 3000))],
        'jega': quadros(f'{BOSS}/jega', numerados('jega', 7), (256, 256)),
        'escharum': quadros(f'{BOSS}/escharum', numerados('escha', 4), (250, 375)),
        'harbinger': {
            'default': quadros(f'{BOSS}/harbinger', numerados('harb', 5), (200, 300)),
            'teleport': quadros(f'{BOSS}/harbinger/teleport', numerados('tp', 8), (100, 100)),
        },
        'atriox': quadros(f'{BOSS}/atriox', numerados('atriox', 4), (300, 450)),
        'grunt': {
            'red': quadros(f'{COV}/grunt/red', numerados('grunt', 4), (80, 120)),
            # blue e space: só o 1º quadro (os outros estavam comentados no assets.py antigo)
            'blue': quadros(f'{COV}/grunt/blue', ['grunt1.png'], (80, 120)),
            'space': quadros(f'{COV}/grunt/space', ['grunt1.png'], (120, 180)),
        },
        'jackal': {
            'red': quadros(f'{COV}/jackal/red', numerados('red', 4), (120, 120)),
            'red_broken': quadros(f'{COV}/jackal/red', numerados('red', 6, inicio=5), (120, 120)),
            'blue': quadros(f'{COV}/jackal/blue', numerados('blue', 4), (132, 120)),
            'blue_broken': quadros(f'{COV}/jackal/blue', numerados('blue', 8, inicio=5), (132, 132)),
            'sniper': quadros(f'{COV}/jackal/sniper', numerados('sniper', 4), (132, 120)),
        },
        'infection': {
            'default': quadros(FLOOD, numerados('infection', 3), (72, 48)),
            'elite': quadros(f'{FLOOD}/elite', numerados('elite', 4), (192, 192)),
            'marine': quadros(f'{FLOOD}/marine', numerados('marine', 4), (128, 128)),
            'carry': quadros(f'{FLOOD}/carry', numerados('carry', 4), (128, 192)),
        },
        'elite': {
            'default': quadros(f'{COV}/elite', numerados('elite', 4), (120, 180)),
            'reach': quadros(f'{COV}/elite/reach', numerados('zealot', 4), (150, 180)),
            'h4': quadros(f'{COV}/elite/h4', numerados('zealot', 4), (120, 180)),
        },
        'brute': quadros(f'{COV}/brute', ['brute.png', 'brute2.png'], (200, 200)),
        'sentinel': {
            'default': quadros('enemies/forerunner/sentinel', numerados('sent', 2), (128, 192)),
            'major': quadros('enemies/forerunner/sentinel', ['super.png', 'super.png'], (192, 288)),
        },
        'crawler': quadros(f'{PROM}/crawler', numerados('craw', 4), (128, 128)),
        'watcher': {
            'default': quadros(f'{PROM}/watcher', numerados('wat', 4), (96, 96)),
            'omega': quadros(f'{PROM}/watcher', numerados('wat', 4), (144, 144)),
        },
        'soldier': {
            'default': quadros(f'{PROM}/soldier', numerados('soldier', 4), (96, 120)),
            'sniper': quadros(f'{PROM}/soldier/sniper', numerados('sniper', 4), (128, 128)),
        },
    },

    # Fundo de cada fase (opaco, tamanho original). A fase existe se tem entrada aqui.
    'maps': {str(n): Imagem(f'map/{n}/map{n}.jpg', alpha=False) for n in range(9)},

    'menu': {
        'logo': Imagem('menu/logo.png', (576, 384)),
        'menuback': Imagem('menu/menuback.png', TELA),
        'menuback2': Imagem('menu/menuback2.png', TELA),
        'haloring': Imagem('menu/haloring.png', TELA),
        'colaboradores': Imagem('colaboradores.png', TELA, alpha=False),
        'ranking': Imagem('ranking.jpg', TELA, alpha=False),
    },

    # A fase 8 não tem imagem: o game over dela usa fundo preto (windows/menu/gameover.py).
    'gameover': {str(n): Imagem(f'map/{n}/over{n}.png', TELA) for n in range(8)},

    'effects': {
        'fuel_rod_area': quadros('effects/fuel_rod', numerados('area', 8), (300, 300)),
        'portal': Imagem('portal.png', (192, 288)),
    },
}


def folhas(no=MANIFESTO):
    """Todas as Imagem do manifesto (com repetições), em ordem."""
    if isinstance(no, Imagem):
        yield no
    elif isinstance(no, list):
        for x in no:
            yield from folhas(x)
    else:
        for x in no.values():
            yield from folhas(x)
