import pygame
from source.windows.settings import *
import sys
import os


def path(*args):
    """ 
    Junta os caminhos e ajusta para o PyInstaller.
    Aceita múltiplos argumentos: path('pasta', 'sub', 'arquivo.png')
    """
    relative_path = os.path.join(*args)
    if hasattr(sys, '_MEIPASS'):
        # Caminho dentro do executável
        return os.path.join(sys._MEIPASS, relative_path)
    # Caminho rodando o script .py
    return os.path.join(os.path.abspath("."), relative_path)

# Inicialização segura para o Executável
pygame.init()

# Criar uma tela oculta evita que o convert_alpha() dê erro 
# e resolve o erro de "Embedded Interpreter" em alguns sistemas
try:
    screen = pygame.display.set_mode((1280, 720), pygame.HIDDEN)
except pygame.error:
    # Caso o driver de vídeo não suporte modo oculto
    screen = pygame.display.set_mode((1280, 720))

# Sou preguiçoso e nao quero escrever função
player_right_frames = [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'player', 'player1.png')).convert_alpha(), (144, 144)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'player', 'player2.png')).convert_alpha(), (144, 144)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'player', 'player3.png')).convert_alpha(), (144, 144)),
            ]

ASSETS = {
    'projectiles': {
        'plasma': pygame.image.load(path('assets', 'img', 'projectiles', 'plasmagun.png')).convert_alpha(),
        'carabin': pygame.image.load(path('assets', 'img', 'projectiles', 'carabin.png')).convert_alpha(),
        'bcarabin': pygame.image.load(path('assets', 'img', 'projectiles', 'bcarabin.png')).convert_alpha(),
        'm50': pygame.image.load(path('assets', 'img', 'projectiles', 'm50.png')).convert_alpha(),
        'ar': pygame.image.load(path('assets', 'img', 'projectiles', 'ar.png')).convert_alpha(),
        'pingpong' : pygame.image.load(path('assets', 'img', 'projectiles', 'bola_pingpong.png')),
        'lista' : pygame.image.load(path('assets', 'img', 'projectiles','listas.png')).convert_alpha(),
        'lightrifle': pygame.image.load(path('assets', 'img', 'projectiles', 'lightrifle.png')).convert_alpha(),
        'dizimator': pygame.image.load(path('assets', 'img', 'projectiles', 'dizimator.png')).convert_alpha(),
        'acid_breath': pygame.image.load(path('assets', 'img', 'projectiles', 'acid.gif')).convert_alpha(),
        'red_laser': pygame.image.load(path('assets', 'img', 'projectiles', 'redlaser.png')).convert_alpha(),
        'blue_laser': pygame.image.load(path('assets', 'img', 'projectiles', 'bluelaser.png')).convert_alpha(),
        'green_laser': pygame.image.load(path('assets', 'img', 'projectiles', 'greenlaser.png')).convert_alpha()
        
    },

    'items': {
        'exp_shard': pygame.image.load(path('assets', 'img', 'items', 'expshard.png')).convert_alpha(),
        'big_shard': pygame.image.load(path('assets', 'img', 'items', 'bigshard.png')).convert_alpha(),
        'life_orb': pygame.image.load(path('assets', 'img', 'items', 'lifeorb.png')).convert_alpha(),
        'light_bullet': pygame.image.load(path('assets', 'img', 'items', 'lightbullet.png')).convert_alpha(),
        'cafe': pygame.image.load(path('assets', 'img', 'items', 'cafe.png')).convert_alpha(),
    },

    'player': {
        'right': player_right_frames,
        'left': [pygame.transform.flip(sprite, True, False) for sprite in player_right_frames]
    },

    'buddies' : {
        'cortana' : [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'buddies', 'cortana', 'cortana1.png')).convert_alpha(), (128, 192)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'buddies', 'cortana', 'cortana2.png')).convert_alpha(), (128, 192)),
        ],
        'arbiter' : [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'buddies', 'arbiter', 'arbiter1.png')).convert_alpha(), (192, 192)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'buddies', 'arbiter', 'arbiter2.png')).convert_alpha(), (192, 192)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'buddies', 'arbiter', 'arbiter3.png')).convert_alpha(), (192, 192)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'buddies', 'arbiter', 'arbiter4.png')).convert_alpha(), (192, 192)),
        ]
    },


    'enemies': {
        'hunter': [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'hunter','hunter1.png')).convert_alpha(), (250, 250)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'hunter','hunter2.png')).convert_alpha(), (270, 270))
        ],

        'zealot': [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'zealot', 'zealot1.png')).convert_alpha(), (200,200)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'zealot', 'zealot2.png')).convert_alpha(), (200,200)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'zealot', 'zealot3.png')).convert_alpha(), (200,200)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'zealot', 'zealot4.png')).convert_alpha(), (200,200))
        ],

        'guilty': {
            'normal' : [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'guilty', 'guilty.png')).convert_alpha(), (100, 100)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'guilty', 'guilty2.png')).convert_alpha(), (100, 100)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'guilty', 'guilty3.png')).convert_alpha(), (100, 100))
            ],
            'damaged' : [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'guilty', 'guilty4.png')).convert_alpha(), (100, 100)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'guilty', 'guilty5.png')).convert_alpha(), (100, 100)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'guilty', 'guilty6.png')).convert_alpha(), (100, 100))
            ],
            'teleport' : [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp1.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp2.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp3.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp4.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp5.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp6.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp7.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp8.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp9.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp10.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp11.png')).convert_alpha(), (128, 160))
            ]
        },

        'scarab' : {
            'default' : [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'scarab', 'scarab1.png')).convert_alpha(),(1024, 1024)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'scarab', 'scarab2.png')).convert_alpha(),(1024, 1024)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'scarab', 'scarab3.png')).convert_alpha(),(1024, 1024)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'scarab', 'scarab4.png')).convert_alpha(),(1024, 1024))
            ],
            'damaged' : [
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'scarab', 'damaged', 'damaged1.png')).convert_alpha(),(1024, 1024)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'scarab', 'damaged', 'damaged2.png')).convert_alpha(),(1024, 1024)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'scarab', 'damaged', 'damaged3.png')).convert_alpha(),(1024, 1024)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'scarab', 'damaged', 'damaged4.png')).convert_alpha(),(1024, 1024))
             ],
            'broken' : [
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'scarab', 'broken', 'broken1.png')).convert_alpha(),(1024, 1024)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'scarab', 'broken', 'broken2.png')).convert_alpha(),(1024, 1024)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'scarab', 'broken', 'broken3.png')).convert_alpha(),(1024, 1024)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'scarab', 'broken', 'broken4.png')).convert_alpha(),(1024, 1024))
            ]
        },

        'arbiter': [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'arbiter', 'boss1.png')).convert_alpha(), (250,250)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'arbiter', 'boss2.png')).convert_alpha(), (250,250)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'arbiter', 'boss3.png')).convert_alpha(), (250,250)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'arbiter', 'boss4.png')).convert_alpha(), (250,250))
        ],

        'gravemind': {
            'final': {
                'default': [
                    pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'gravemind', 'final', 'final1.png')).convert_alpha(), (900,600)),
                    pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'gravemind', 'final', 'final2.png')).convert_alpha(), (900,600)), # Assumo que aqui seria proto2.png?
                ],
                'attack': [ 
                    pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'gravemind', 'final', 'final3.png')).convert_alpha(), (900,600)), 
                ]
            },
            
            'proto': {
                'default': [
                    pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'gravemind', 'proto', 'proto1.png')).convert_alpha(), (750,500)),
                    pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'gravemind', 'proto', 'proto2.png')).convert_alpha(), (750,500)),
                ],
                'attack': [
                    pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'gravemind', 'proto', 'proto3.png')).convert_alpha(), (750,500)),
                ]
            },
        },

        'knight' : [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'prometheans', 'knight', 'command1.png')).convert_alpha(), (250, 250)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'prometheans', 'knight', 'command2.png')).convert_alpha(), (250, 250)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'prometheans', 'knight', 'command3.png')).convert_alpha(), (250, 250)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'prometheans', 'knight', 'command4.png')).convert_alpha(), (250, 250)),
        ],

        'didact' : {
            'default' : [
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'didact', 'did1.png')).convert_alpha(), (250, 375)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'didact', 'did2.png')).convert_alpha(), (250, 375)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'didact', 'did3.png')).convert_alpha(), (250, 375)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'didact', 'did4.png')).convert_alpha(), (250, 375))
                ],
            'attack' : [
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'didact', 'didpull.png')).convert_alpha(), (250, 375)),
                ],
            'cryptum' : [
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'didact', 'cryptum.png')).convert_alpha(), (400, 400))
                ]
        },

        'warden' : {
            'default' : [
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'warden', 'warden.png')).convert_alpha(), (550,550)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'warden', 'warden2.png')).convert_alpha(), (550,550)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'warden', 'warden3.png')).convert_alpha(), (550,550))
            ],
            'clone' : [
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'warden', 'clone2.png')).convert_alpha(), (500,500)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'warden', 'clone.png')).convert_alpha(), (500,500)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'warden', 'clone3.png')).convert_alpha(), (500,500))
            ]
        },

        'jega' : [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'jega', 'jega1.png')).convert_alpha(), (256, 256)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'jega', 'jega2.png')).convert_alpha(), (256, 256)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'jega', 'jega3.png')).convert_alpha(), (256, 256)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'jega', 'jega4.png')).convert_alpha(), (256, 256)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'jega', 'jega5.png')).convert_alpha(), (256, 256)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'jega', 'jega6.png')).convert_alpha(), (256, 256)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'bosses', 'jega', 'jega7.png')).convert_alpha(), (256, 256))
        ],

        'harbinger' : [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'harbinger', 'harb1.png')).convert_alpha(), (200,300)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'harbinger', 'harb2.png')).convert_alpha(), (200,300)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'harbinger', 'harb3.png')).convert_alpha(), (200,300)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'harbinger', 'harb4.png')).convert_alpha(), (200,300)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'harbinger', 'harb5.png')).convert_alpha(), (200,300))
        ],

        'grunt': [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'grunt', 'grunt.png')).convert_alpha(), (96, 96)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'grunt', 'grunt2.png')).convert_alpha(), (96, 96))
        ],

        'jackal': {
            'red': [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'jackal', 'red', 'red1.png')).convert_alpha(), (160,160)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'jackal', 'red', 'red2.png')).convert_alpha(), (160,160)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'jackal', 'red', 'red3.png')).convert_alpha(), (160,160)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'jackal', 'red', 'red4.png')).convert_alpha(), (160,160))
            ],

            'red_broken': [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'jackal', 'red', 'red5.png')).convert_alpha(), (160,160)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'jackal', 'red', 'red6.png')).convert_alpha(), (160,160)),            
            ],

            'blue': [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'jackal', 'blue', 'blue1.png')).convert_alpha(), (120,120)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'jackal', 'blue', 'blue2.png')).convert_alpha(), (120,120)),
            ],

            'blue_broken': [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'jackal', 'blue', 'blue3.png')).convert_alpha(), (120,120)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'jackal', 'blue', 'blue4.png')).convert_alpha(), (120,120)),            
            ],

            'sniper': [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'jackal', 'sniper', 'sniper1.png')).convert_alpha(), (100,100)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'jackal', 'sniper', 'sniper2.png')).convert_alpha(), (100,100)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'jackal', 'sniper', 'sniper3.png')).convert_alpha(), (100,100)),
            ]
        },

        'infection': {
            'default' : [
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'flood', 'infection1.png')).convert_alpha(), (75, 75)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'flood', 'infection2.png')).convert_alpha(), (75, 75))
                ],

            'elite' : [
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'flood', 'elite', 'elite1.png')).convert_alpha(), (192, 192)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'flood', 'elite', 'elite2.png')).convert_alpha(), (192, 192)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'flood', 'elite', 'elite3.png')).convert_alpha(), (192, 192)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'flood', 'elite', 'elite4.png')).convert_alpha(), (192, 192))
                ],
            'marine' : [
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'flood', 'marine', 'marine1.png')).convert_alpha(), (128, 128)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'flood', 'marine', 'marine2.png')).convert_alpha(), (128, 128)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'flood', 'marine', 'marine3.png')).convert_alpha(), (128, 128)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'flood', 'marine', 'marine4.png')).convert_alpha(), (128, 128))
                ],

            'carry'  : [
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'flood', 'carry', 'carry1.png')).convert_alpha(), (128, 192)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'flood', 'carry', 'carry2.png')).convert_alpha(), (128, 192)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'flood', 'carry', 'carry3.png')).convert_alpha(), (128, 192)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'flood', 'carry', 'carry4.png')).convert_alpha(), (128, 192))
                ]
        },

        'elite': [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'elite', 'elite1.png')).convert_alpha(),(120,180)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'elite', 'elite2.png')).convert_alpha(),(120,180)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'elite', 'elite3.png')).convert_alpha(),(120,180)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'elite', 'elite4.png')).convert_alpha(),(120,180))
        ],

        'brute': [ 
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'brute', 'brute.png')).convert_alpha(),(200,200)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'covenant', 'brute', 'brute2.png')).convert_alpha(),(200,200))
           ],
        
        'sentinel': [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'forerunner', 'sentinel', 'sent1.png')).convert_alpha(), (128, 192)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'forerunner', 'sentinel', 'sent2.png')).convert_alpha(), (128, 192)),
        ],

        'crawler' : [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'prometheans', 'crawler', 'craw1.png')).convert_alpha(), (128, 128)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'prometheans', 'crawler', 'craw2.png')).convert_alpha(), (128, 128)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'prometheans', 'crawler', 'craw3.png')).convert_alpha(), (128, 128)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'prometheans', 'crawler', 'craw4.png')).convert_alpha(), (128, 128)),
            ],
        
        'watcher' : [
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'prometheans', 'watcher', 'wat1.png')).convert_alpha(), (96, 96)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'prometheans', 'watcher', 'wat2.png')).convert_alpha(), (96, 96)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'prometheans', 'watcher', 'wat3.png')).convert_alpha(), (96, 96)),
            pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'prometheans', 'watcher', 'wat4.png')).convert_alpha(), (96, 96)),
        ],

        'soldier' : {
            'default' : [
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'prometheans', 'soldier', 'soldier1.png')).convert_alpha(), (96, 120)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'prometheans', 'soldier', 'soldier2.png')).convert_alpha(), (96, 120)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'prometheans', 'soldier', 'soldier3.png')).convert_alpha(), (96, 120)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'prometheans', 'soldier', 'soldier4.png')).convert_alpha(), (96, 120)),
                ],

            'sniper' : [ 
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'prometheans', 'soldier', 'sniper', 'sniper1.png')).convert_alpha(), (128, 128)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'prometheans', 'soldier', 'sniper', 'sniper2.png')).convert_alpha(), (128, 128)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'prometheans', 'soldier', 'sniper', 'sniper3.png')).convert_alpha(), (128, 128)),
                pygame.transform.scale(pygame.image.load(path('assets', 'img', 'enemies', 'prometheans', 'soldier', 'sniper', 'sniper4.png')).convert_alpha(), (128, 128)),
                ]
            }
                
        },


    'maps': {
        '0' : pygame.image.load(path('assets', 'img', 'map', '0', 'map0.jpg')).convert(),
        '1' : pygame.image.load(path('assets', 'img', 'map', '1', 'map1.jpg')).convert(),
        '2' : pygame.image.load(path('assets', 'img', 'map', '2', 'map2.jpg')).convert(),
        '3' : pygame.image.load(path('assets', 'img', 'map', '3', 'map3.jpg')).convert(),
        '4' : pygame.image.load(path('assets', 'img', 'map', '4', 'map4.jpg')).convert(),
        '5' : pygame.image.load(path('assets', 'img', 'map', '5', 'map5.jpg')).convert(),
        '6' : pygame.image.load(path('assets', 'img', 'map', '6', 'map6.jpg')).convert(),
        '7' : pygame.image.load(path('assets', 'img', 'map', '7', 'map7.jpg')).convert(),
        '8' : pygame.image.load(path('assets', 'img', 'map', '8', 'map8.jpg')).convert()

    },

    'menu': {
        'logo'          : pygame.transform.scale(pygame.image.load(path('assets', 'img', 'menu', 'logo.png')).convert_alpha(),(576, 384)),
        'menuback'      : pygame.transform.scale(pygame.image.load(path('assets', 'img', 'menu', 'menuback.png')).convert_alpha(), (largura_tela, altura_tela)),
        'menuback2'     : pygame.transform.scale(pygame.image.load(path('assets', 'img', 'menu', 'menuback2.png')).convert_alpha(), (largura_tela, altura_tela)),
        'haloring'      : pygame.transform.scale(pygame.image.load(path('assets', 'img', 'menu', 'haloring.png')).convert_alpha(), (largura_tela, altura_tela)),
        'colaboradores' : pygame.transform.scale(pygame.image.load(path('assets', 'img', 'colaboradores.png')).convert(), (largura_tela, altura_tela)),
        'ranking'       : pygame.transform.scale(pygame.image.load(path('assets', 'img', 'ranking.jpg')).convert(), (largura_tela, altura_tela))
    },

    'gameover' : {
        '0' : pygame.transform.scale(pygame.image.load(path('assets', 'img', 'map', '0', 'over0.png')).convert_alpha(), (largura_tela, altura_tela)),
        '1' : pygame.transform.scale(pygame.image.load(path('assets', 'img', 'map', '1', 'over1.png')).convert_alpha(), (largura_tela, altura_tela)),
        '2' : pygame.transform.scale(pygame.image.load(path('assets', 'img', 'map', '2', 'over2.png')).convert_alpha(), (largura_tela, altura_tela)),
        '3' : pygame.transform.scale(pygame.image.load(path('assets', 'img', 'map', '3', 'over3.png')).convert_alpha(), (largura_tela, altura_tela)),
        '4' : pygame.transform.scale(pygame.image.load(path('assets', 'img', 'map', '4', 'over4.png')).convert_alpha(), (largura_tela, altura_tela)),
        '5' : pygame.transform.scale(pygame.image.load(path('assets', 'img', 'map', '5', 'over5.png')).convert_alpha(), (largura_tela, altura_tela)),
        '6' : pygame.transform.scale(pygame.image.load(path('assets', 'img', 'map', '6', 'over6.png')).convert_alpha(), (largura_tela, altura_tela)),
        '7' : pygame.transform.scale(pygame.image.load(path('assets', 'img', 'map', '7', 'over7.png')).convert_alpha(), (largura_tela, altura_tela)),

    },


    'effects' : {
        'portal' : pygame.transform.scale(pygame.image.load(path('assets', 'img', 'portal.png')).convert_alpha(), (192, 288))
    }
    
    }