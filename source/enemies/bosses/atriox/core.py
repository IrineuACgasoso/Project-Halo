import pygame
from source.enemies.base.enemy_base import BaseEnemy
from source.systems.entitymanager import entity_manager
from source.feats.items import Items

from .setup import TartarusSetup
from .states import TartarusAI
from .attacks import TartarusAttacks
from .vfx import ProtocoloHalo

class Atriox(BaseEnemy, TartarusSetup, TartarusAI, TartarusAttacks):
    """Classe principal do Boss Atriox."""
    def __init__(self, posicao, game, ativar_halo=True, **kwargs):
        super().__init__(posicao, vida_base=4000, dano_base=60, velocidade_base=120, 
                         game=game, sprite_key='atriox', flip_sprite=True)
        
        self.titulo = "ATRIOX, Líder dos Banidos"
        self.is_boss = True 

        self.velocidade_original = 120

        if ativar_halo:
            ProtocoloHalo(game=self.game, boss=self, tempo_limite_ms=120000)
        
        # Executa as preparações dos Mixins
        self.setup_animation(estado_inicial='left', velocidade_animacao=400)
        self.inicializar_habilidades()

    def morrer(self, grupos=None):
        Items.spawn_drop(
            self.posicao, 
            grupos, 
            big_shard=((6, 8, 10), (70, 28, 2), 100), 
            life_orb=(1, 100, 100),              
            upgrade=((1, 2), (99, 1), 100)       
        )
        self.kill()

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()
        
        # 1. Executa a IA (decide o estado)
        self.executar_estados(agora, delta_time)
        
        # Processamento dos estados em movimento
        if self.estado_habilidade == 'leaping_takeoff':
            self.processar_salto(agora, delta_time)
        elif self.estado_habilidade == 'hammer_run':
            self.processar_hammer_run(agora, delta_time, paredes)
        elif self.estado_habilidade == 'energy_smash':
            self.processar_smash_energia(agora)
        elif self.estado_habilidade == 'summon_brutes':
            self.processar_invocacao(agora)
        else:
            super().update(delta_time, paredes)

            direcao_x = self.jogador.posicao.x - self.posicao.x 
            self.set_sprite_direction(direcao_x)
            
        self.animar()