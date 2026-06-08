# enemies/guilty/core.py
import pygame
from source.feats.items import Items
from source.enemies.base.enemy_base import BaseEnemy

from .setup import GuiltySetup
from .states import GuiltyAI
from .attacks import GuiltyAttacks

class GuiltySpark(BaseEnemy, GuiltySetup, GuiltyAI, GuiltyAttacks):
    def __init__(self, posicao, game, grupos=None):
        valor_vida = 5000
        super().__init__(posicao, vida_base=valor_vida, dano_base=80, velocidade_base=100, 
                         game=game, sprite_key='guilty', flip_sprite=True)
                         
        self.titulo = "GUILTY SPARK, O Monitor da Instalação 04"
        
        self.setup_animation(estado_inicial='left', velocidade_animacao=300)
        self.mask = pygame.mask.from_surface(self.image)
        
        self.inicializar_habilidades()


    def animar(self):
        """Sobrescreve a animação para travar em frames específicos durante as skills."""
        agora = pygame.time.get_ticks()
        
        if self.estado_habilidade == 'laser':
            self.image = self.sprites[self.estado_animacao][1] # Trava no frame do laser
        elif self.estado_habilidade == 'sentinel':
            self.image = self.sprites[self.estado_animacao][2] # Trava no frame de invocação
        else:
            self.image = self.sprites[self.estado_animacao][0]

        self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))
        self.mask = pygame.mask.from_surface(self.image)


    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()

        self.verificar_fases()
        self.executar_estados(agora)

        direcao_x = self.jogador.posicao.x - self.posicao.x 
        self.set_sprite_direction(direcao_x)
        
        super().update(delta_time, paredes)

        self.animar()

    def morrer(self, grupos=None):
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 4, 100)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 50)
        Items.spawn_drop(self.posicao, grupos, 'cafe', 1, 1)
        self.kill()