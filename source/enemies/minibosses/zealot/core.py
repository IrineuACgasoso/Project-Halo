import pygame
from source.feats.items import Items
from source.enemies.base.enemy_base import BaseEnemy

from .setup import ZealotSetup
from .states import ZealotAI
from .attacks import ZealotAttacks

class Zealot(BaseEnemy, ZealotSetup, ZealotAI, ZealotAttacks):
    def __init__(self, posicao, game, **kwargs):
        super().__init__(posicao, vida_base=750, dano_base=80, velocidade_base=100, game=game, sprite_key='zealot')
        self.titulo = "ZEALOT, Soldado de Elite Covenant"
        self.is_boss = True

        self.setup_animation(estado_inicial='right', velocidade_animacao=200)
        
        self.inicializar_habilidades()

        # Hitbox Customizada
        self.hitbox = pygame.Rect(0, 0, self.rect.width / 2, self.rect.height)
        self.hitbox.center = self.rect.center

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()
        dist_sq = self.posicao.distance_squared_to(self.jogador.posicao)

        # Inteligência e Estados
        self.verificar_fases()
        self.executar_estados(agora, delta_time, dist_sq)

        # Direção da Sprite
        # Trava a direção da sprite APENAS se não estiver em dash 
        if self.estado_habilidade not in ['dash_prep', 'dashing']:
            direcao_x = self.jogador.posicao.x - self.posicao.x
            self.set_sprite_direction(direcao_x)

        # Movimento Base e Animação
        super().update(delta_time, paredes)
        self.animar()
        
        self.hitbox.center = self.rect.center


    def morrer(self, grupos=None):
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 3, 100)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 50)
        Items.spawn_drop(self.posicao, grupos, 'cafe', 1, 1)
        self.kill()