# source/enemies/bosses/harbinger/core.py
import pygame
from source.enemies.base.enemy_base import BaseEnemy
from source.feats.items import Items
from source.systems.entitymanager import entity_manager

# Importações locais do pacote
from .setup import HarbingerSetup
from .ia import HarbingerIA
from .attacks import HarbingerAttacks

class Harbinger(BaseEnemy, HarbingerSetup, HarbingerIA, HarbingerAttacks):
    """A Rainha Endless. Boss ágil focado em zoneamento dimensional e rajadas de carabina."""
    def __init__(self, posicao, game, jogador=None, **kwargs):
        super().__init__(
            posicao=posicao, 
            vida_base=3500, 
            dano_base=40, 
            velocidade_base=50, 
            game=game, 
            sprite_key='harbinger'
        )
        self.jogador = jogador if jogador else entity_manager.player
        self.titulo = "HARBINGER, A Rainha Endless"
        self.is_boss = True

        # Injeta as variáveis de estado e timers das Mixins
        self.inicializar_harbinger()

        # Configuração do Motor de Animação Core
        self.setup_animation(estado_inicial='right', velocidade_animacao=200)

        # Ajuste de Hitbox fina para o modelo vertical esguio da Harbinger
        nova_largura = self.rect.width / 2
        self.hitbox = pygame.Rect(0, 0, nova_largura, self.rect.height)
        self.hitbox.center = self.rect.center

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()
        
        # Delega todo o processamento lógico para a Mixin de IA
        self.executar_ia_harbinger(agora, delta_time, paredes)
        
        # A animação fica congelada enquanto ela estiver em recarga
        if self.estado_boss != 'recharging':
            self.animar()

    def morrer(self, grupos=None):
        Items.spawn_drop(
            self.posicao, 
            grupos, 
            big_shard=((8, 10, 12), (70, 28, 2), 100), 
            life_orb=(1, 100, 100),              
            upgrade=((1, 2), (99, 1), 100)       
        )
        self.kill()