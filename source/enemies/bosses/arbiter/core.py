import pygame
from source.enemies.base.enemy_base import BaseEnemy
from source.feats.items import Items

from .setup import ArbiterSetup
from .states import ArbiterAI
from .attacks import ArbiterAttacks

class BossArbiter(BaseEnemy, ArbiterSetup, ArbiterAI, ArbiterAttacks):
    def __init__(self, posicao, game, **kwargs):
        super().__init__(posicao, vida_base=2500, dano_base=80, velocidade_base=90, game=game, sprite_key='arbiter', flip_sprite=True)
        
        self.titulo = "THEL 'VADAM, O Comandante da Frota Covenant"
        self.is_boss = True
        
        self.setup_animation(estado_inicial='right', velocidade_animacao=200)

        # Hitbox Personalizada
        nova_largura = self.rect.width / 3
        nova_altura = self.rect.height / 1.5
        self.hitbox = pygame.Rect(0, 0, nova_largura, nova_altura)
        self.hitbox.center = self.rect.center

        self.inicializar_habilidades()

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()
        dist_sq = self.posicao.distance_squared_to(self.jogador.posicao)
        
        # Máquina de Estados / Inteligência
        self.executar_estados(agora, delta_time, dist_sq)

        # Mira sempre pro jogador independente da habilidade
        direcao_x = self.jogador.posicao.x - self.posicao.x 
        self.set_sprite_direction(direcao_x)
        
        # Movimento e Física (A velocidade processada no states reage aqui)
        super().update(delta_time, paredes)
        
        self.animar()
        self.hitbox.center = self.rect.center

    def morrer(self, grupos=None):
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 6, 100)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 75)
        Items.spawn_drop(self.posicao, grupos, 'cafe', 1, 1)
        self.kill()