import pygame
from settings import *
from os.path import join



# Inicialize o pygame para poder usar convert_alpha()
pygame.init()
screen = pygame.display.set_mode((1280, 720)) # Apenas para o contexto do driver de vídeo

ASSETS = {
    'projectiles': {
        'plasma': pygame.image.load(join('assets', 'img', 'projectiles', 'plasmagun.png')).convert_alpha(),
        'carabin': pygame.image.load(join('assets', 'img', 'projectiles', 'carabin.png')).convert_alpha(),
        'bcarabin': pygame.image.load(join('assets', 'img', 'projectiles', 'bcarabin.png')).convert_alpha(),
        'm50': pygame.image.load(join('assets', 'img', 'projectiles', 'm50.png')).convert_alpha(),
        'ar': pygame.image.load(join('assets', 'img', 'projectiles', 'ar.png')).convert_alpha(),
        'lightrifle': pygame.image.load(join('assets', 'img', 'projectiles', 'lightrifle.png')).convert_alpha(),
        'dizimator': pygame.image.load(join('assets', 'img', 'projectiles', 'dizimator.png')).convert_alpha(),
        'acid_breath': pygame.image.load(join('assets', 'img', 'projectiles', 'acid.gif')).convert_alpha(),
        'red_laser': pygame.image.load(join('assets', 'img', 'projectiles', 'redlaser.png')).convert_alpha(),
        'blue_laser': pygame.image.load(join('assets', 'img', 'projectiles', 'bluelaser.png')).convert_alpha(),
        'cannon': [
            pygame.image.load(join('assets', 'img', 'projectiles', 'cannon', 'c1.png')).convert_alpha(),
            pygame.image.load(join('assets', 'img', 'projectiles', 'cannon', 'c2.png')).convert_alpha()
        ]
    },


    'enemies': {
        'hunter': [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'hunter','hunter1.png')).convert_alpha(), (250, 250)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'hunter','hunter2.png')).convert_alpha(), (270, 270))
        ],

        'zealot': [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'zealot', 'zealot1.png')).convert_alpha(), (200,200)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'zealot', 'zealot2.png')).convert_alpha(), (200,200)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'zealot', 'zealot3.png')).convert_alpha(), (200,200)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'zealot', 'zealot4.png')).convert_alpha(), (200,200))
        ],

        'guilty': {
            'normal' : [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'guilty.png')).convert_alpha(), (100, 100)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'guilty2.png')).convert_alpha(), (100, 100)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'guilty3.png')).convert_alpha(), (100, 100))
            ],
            'damaged' : [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'guilty4.png')).convert_alpha(), (100, 100)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'guilty5.png')).convert_alpha(), (100, 100)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'guilty6.png')).convert_alpha(), (100, 100))
            ],
            'teleport' : [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp1.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp2.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp3.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp4.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp5.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp6.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp7.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp8.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp9.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp10.png')).convert_alpha(), (128, 160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'guilty', 'teleport', 'tp11.png')).convert_alpha(), (128, 160))
            ]
        },

        'arbiter': [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'arbiter', 'boss1.png')).convert_alpha(), (250,250)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'arbiter', 'boss2.png')).convert_alpha(), (250,250)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'arbiter', 'boss3.png')).convert_alpha(), (250,250)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'arbiter', 'boss4.png')).convert_alpha(), (250,250))
        ],

        'gravemind': {
            'final': {
                'default': [
                    pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'gravemind', 'final', 'final1.png')).convert_alpha(), (900,600)),
                    pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'gravemind', 'final', 'final2.png')).convert_alpha(), (900,600)), # Assumo que aqui seria proto2.png?
                ],
                'attack': [ 
                    pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'gravemind', 'final', 'final3.png')).convert_alpha(), (900,600)), 
                ]
            },
            
            'proto': {
                'default': [
                    pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'gravemind', 'proto', 'proto1.png')).convert_alpha(), (750,500)),
                    pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'gravemind', 'proto', 'proto2.png')).convert_alpha(), (750,500)),
                ],
                'attack': [
                    pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'gravemind', 'proto', 'proto3.png')).convert_alpha(), (750,500)),
                ]
            },
        },

        'didact' : {
            'default' : [
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'didact', 'did1.png')).convert_alpha(), (250, 375)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'didact', 'did2.png')).convert_alpha(), (250, 375)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'didact', 'did3.png')).convert_alpha(), (250, 375)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'didact', 'did4.png')).convert_alpha(), (250, 375))
                ],
            'attack' : [
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'didact', 'didpull.png')).convert_alpha(), (250, 375)),
                ],
            'cryptum' : [
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'didact', 'cryptum.png')).convert_alpha(), (400, 400))
                ]
        },

        'jega' : [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'jega', 'jega1.png')).convert_alpha(), (256, 256)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'jega', 'jega2.png')).convert_alpha(), (256, 256)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'jega', 'jega3.png')).convert_alpha(), (256, 256)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'jega', 'jega4.png')).convert_alpha(), (256, 256)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'jega', 'jega5.png')).convert_alpha(), (256, 256)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'jega', 'jega6.png')).convert_alpha(), (256, 256)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'jega', 'jega7.png')).convert_alpha(), (256, 256))
        ],

        'grunt': [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'grunt', 'grunt.png')).convert_alpha(), (96, 96)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'grunt', 'grunt2.png')).convert_alpha(), (96, 96))
        ],

        'jackal': {
            'red': [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'red', 'red1.png')).convert_alpha(), (160,160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'red', 'red2.png')).convert_alpha(), (160,160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'red', 'red3.png')).convert_alpha(), (160,160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'red', 'red4.png')).convert_alpha(), (160,160))
            ],

            'red_broken': [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'red', 'red5.png')).convert_alpha(), (160,160)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'red', 'red6.png')).convert_alpha(), (160,160)),            
            ],

            'blue': [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'blue', 'blue1.png')).convert_alpha(), (120,120)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'blue', 'blue2.png')).convert_alpha(), (120,120)),
            ],

            'blue_broken': [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'blue', 'blue3.png')).convert_alpha(), (120,120)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'blue', 'blue4.png')).convert_alpha(), (120,120)),            
            ],

            'sniper': [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'sniper', 'sniper1.png')).convert_alpha(), (100,100)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'sniper', 'sniper2.png')).convert_alpha(), (100,100)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'jackal', 'sniper', 'sniper3.png')).convert_alpha(), (100,100)),
            ]
        },

        'infection': {
            'default' : [
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'flood', 'infection1.png')).convert_alpha(), (75, 75)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'flood', 'infection2.png')).convert_alpha(), (75, 75))
                ],

            'elite' : [
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'flood', 'elite', 'elite1.png')).convert_alpha(), (192, 192)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'flood', 'elite', 'elite2.png')).convert_alpha(), (192, 192)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'flood', 'elite', 'elite3.png')).convert_alpha(), (192, 192)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'flood', 'elite', 'elite4.png')).convert_alpha(), (192, 192))
                ],
            'marine' : [
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'flood', 'marine', 'marine1.png')).convert_alpha(), (128, 128)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'flood', 'marine', 'marine2.png')).convert_alpha(), (128, 128)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'flood', 'marine', 'marine3.png')).convert_alpha(), (128, 128)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'flood', 'marine', 'marine4.png')).convert_alpha(), (128, 128))
                ],

            'carry'  : [
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'flood', 'carry', 'carry1.png')).convert_alpha(), (128, 192)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'flood', 'carry', 'carry2.png')).convert_alpha(), (128, 192)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'flood', 'carry', 'carry3.png')).convert_alpha(), (128, 192)),
                pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'flood', 'carry', 'carry4.png')).convert_alpha(), (128, 192))
                ]
        },

        'elite': [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'elite', 'elite1.png')).convert_alpha(),(120,180)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'elite', 'elite2.png')).convert_alpha(),(120,180)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'elite', 'elite3.png')).convert_alpha(),(120,180)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'elite', 'elite4.png')).convert_alpha(),(120,180))
        ],

        'brute': [ 
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'brute', 'brute.png')).convert_alpha(),(200,200)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'brute', 'brute2.png')).convert_alpha(),(200,200))
           ],
        
        'sentinel': [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'forerunner', 'sentinel', 'sent1.png')).convert_alpha(), (128, 192)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'forerunner', 'sentinel', 'sent2.png')).convert_alpha(), (128, 192)),
        ],

        'crawler' : [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'prometheans', 'crawler', 'craw1.png')).convert_alpha(), (128, 128)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'prometheans', 'crawler', 'craw2.png')).convert_alpha(), (128, 128)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'prometheans', 'crawler', 'craw3.png')).convert_alpha(), (128, 128)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'prometheans', 'crawler', 'craw4.png')).convert_alpha(), (128, 128)),
            ],
        
        'watcher' : [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'prometheans', 'watcher', 'wat1.png')).convert_alpha(), (96, 96)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'prometheans', 'watcher', 'wat2.png')).convert_alpha(), (96, 96)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'prometheans', 'watcher', 'wat3.png')).convert_alpha(), (96, 96)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'prometheans', 'watcher', 'wat4.png')).convert_alpha(), (96, 96)),
        ]
    },


    'maps': {
        '0' : pygame.image.load(join('assets', 'map', '0', 'map0.jpg')).convert(),
        '1' : pygame.image.load(join('assets', 'map', '1', 'map1.jpg')).convert(),
        '2' : pygame.image.load(join('assets', 'map', '2', 'map2.jpg')).convert(),
        '3' : pygame.image.load(join('assets', 'map', '3', 'map3.jpg')).convert(),
        '4' : pygame.image.load(join('assets', 'map', '4', 'map4.jpg')).convert(),
        '5' : pygame.image.load(join('assets', 'map', '5', 'map5.jpg')).convert(),
        '6' : pygame.image.load(join('assets', 'map', '6', 'map6.jpg')).convert(),
        '7' : pygame.image.load(join('assets', 'map', '7', 'map7.jpg')).convert(),
        '8' : pygame.image.load(join('assets', 'map', '8', 'map8.jpg')).convert()

    },

    'menu': {
        'logo'      : pygame.transform.scale(pygame.image.load(join('assets', 'img', 'menu', 'logo.png')).convert_alpha(),(576, 384)),
        'menuback'  : pygame.transform.scale(pygame.image.load(join('assets', 'img', 'menu', 'menuback.png')).convert_alpha(), (largura_tela, altura_tela)),
        'menuback2' : pygame.transform.scale(pygame.image.load(join('assets', 'img', 'menu', 'menuback2.png')).convert_alpha(), (largura_tela, altura_tela)),
        'haloring'  : pygame.transform.scale(pygame.image.load(join('assets', 'img', 'menu', 'haloring.png')).convert_alpha(), (largura_tela, altura_tela))
    },

    'gameover' : {
        '0' : pygame.transform.scale(pygame.image.load(join('assets', 'map', '0', 'over0.png')).convert_alpha(), (largura_tela, altura_tela)),
        '1' : pygame.transform.scale(pygame.image.load(join('assets', 'map', '1', 'over1.png')).convert_alpha(), (largura_tela, altura_tela)),
        '2' : pygame.transform.scale(pygame.image.load(join('assets', 'map', '2', 'over2.png')).convert_alpha(), (largura_tela, altura_tela)),
        '3' : pygame.transform.scale(pygame.image.load(join('assets', 'map', '3', 'over3.png')).convert_alpha(), (largura_tela, altura_tela)),
        '4' : pygame.transform.scale(pygame.image.load(join('assets', 'map', '4', 'over4.png')).convert_alpha(), (largura_tela, altura_tela)),
        '5' : pygame.transform.scale(pygame.image.load(join('assets', 'map', '5', 'over5.png')).convert_alpha(), (largura_tela, altura_tela)),
        '6' : pygame.transform.scale(pygame.image.load(join('assets', 'map', '6', 'over6.png')).convert_alpha(), (largura_tela, altura_tela)),
        '7' : pygame.transform.scale(pygame.image.load(join('assets', 'map', '7', 'over7.png')).convert_alpha(), (largura_tela, altura_tela)),

    },


    'effects' : {
        'portal' : pygame.transform.scale(pygame.image.load(join('assets', 'img', 'portal.png')).convert_alpha(), (192, 288))
    }
    
    }