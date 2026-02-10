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
        'm50': pygame.image.load(join('assets', 'img', 'projectiles', 'm50.png')).convert_alpha(),
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

        'arbiter': [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'arbiter', 'boss1.png')).convert_alpha(), (250,250)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'arbiter', 'boss2.png')).convert_alpha(), (250,250)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'arbiter', 'boss3.png')).convert_alpha(), (250,250)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'arbiter', 'boss4.png')).convert_alpha(), (250,250))
        ],

        'gravemind': {
            'final': [
                pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'gravemind', 'final', 'proto1.png')).convert_alpha(),
                pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'gravemind', 'final', 'proto2.png')).convert_alpha(),
                pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'gravemind', 'final', 'proto3.png')).convert_alpha()
            ],
            'proto': [
                pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'gravemind', 'proto', 'grave1.png')).convert_alpha(),
                pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'gravemind', 'proto', 'grave2.png')).convert_alpha(),
                pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'gravemind', 'proto', 'grave3.png')).convert_alpha()
            ],
        },

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

        'infection': [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'infection', 'infection1.png')).convert_alpha(), (75, 75)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'infection', 'infection2.png')).convert_alpha(), (75, 75))
        ],

        'brute': [ 
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'brute', 'brute.png')).convert_alpha(),(200,200)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'covenant', 'brute', 'brute2.png')).convert_alpha(),(200,200))
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
        '7' : pygame.image.load(join('assets', 'map', '7', 'map7.jpg')).convert()

    },

    'menu': {
        'logo'      : pygame.transform.scale(pygame.image.load(join('assets', 'img', 'menu', 'logo.png')).convert_alpha(),(576, 384)),
        'menuback'  : pygame.transform.scale(pygame.image.load(join('assets', 'img', 'menu', 'menuback.png')).convert_alpha(), (largura_tela, altura_tela)),
        'menuback2' : pygame.transform.scale(pygame.image.load(join('assets', 'img', 'menu', 'menuback2.png')).convert_alpha(), (largura_tela, altura_tela)),
        'haloring'  : pygame.transform.scale(pygame.image.load(join('assets', 'img', 'menu', 'haloring.png')).convert_alpha(), (largura_tela, altura_tela))
    },


    'effects' : {
        'portal' : pygame.transform.scale(pygame.image.load(join('assets', 'img', 'portal.png')).convert_alpha(), (192, 288))
    }
    
    }