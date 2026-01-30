import pygame
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
        'arbiter': {
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'arbiter', 'boss1.png')).convert_alpha(), (250,250)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'arbiter', 'boss2.png')).convert_alpha(), (250,250)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'arbiter', 'boss3.png')).convert_alpha(), (250,250)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'arbiter', 'boss4.png')).convert_alpha(), (250,250))
        },

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

        'infection': [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'infection', 'infection1.png')).convert_alpha(), (75, 75)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'infection', 'infection2.png')).convert_alpha(), (75, 75))
        ]
    }
}