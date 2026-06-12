# enemies/didact/core.py
import pygame
from source.feats.items import Items
from source.enemies.base.enemy_base import BaseEnemy

# Importa as 3 Mixins
from .setup import DidactSetup
from .states import DidactAI
from .attacks import DidactAttacks

# A Classe Didact se torna uma junção de: BaseEnemy + Setup + IA + Ataques
class Didact(BaseEnemy, DidactSetup, DidactAI, DidactAttacks):
    def __init__(self, posicao, game, **kwargs):
        super().__init__(posicao, vida_base=8000, dano_base=60, velocidade_base=50, 
                         game=game, sprite_key='didact', flip_sprite=True)
        
        self.titulo = "DIDACT, O Forerunner Banido"
        self.is_boss = True
        
        # --- Sprites e Animação Base ---
        self.setup_animation(estado_inicial='right', velocidade_animacao=350)

        # Sprites Extras exclusivos do Didact
        self.attack_sprite = self.get_sprites('attack')
        self.cryptum_sprite = self.get_sprites('cryptum')

        # --- Hitbox ---
        self.hitbox = pygame.Rect(0, 0, self.rect.width / 2, self.rect.height)
        self.hitbox.center = self.rect.center

        # --- Atributos de Habilidades ---
        self.inicializar_habilidades()


    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()

        direcao_x = self.jogador.posicao.x - self.posicao.x 
        self.set_sprite_direction(direcao_x)       
        
        # Executa a IA
        self.verificar_fases()
        self.executar_estados(agora, delta_time)

        super().update(delta_time, paredes) 
        self.animar()

        self.hitbox.center = self.rect.center

    def animar(self):
        """Sobrescreve a animação base para usar as sprites de habilidade do Didact."""
        agora = pygame.time.get_ticks()
        
        # 1. Fase do Cryptum (Trava na sprite do Cryptum)
        if self.estado_habilidade == 'crypt':
            self.image = self.cryptum_sprite[self.estado_animacao][0]
            
        # 2. Habilidades de Ataque (Trava na sprite de Ataque)
        elif self.estado_habilidade in ['ataque_pull', 'aviso_laser', 'disparo_laser']:
            self.image = self.attack_sprite[self.estado_animacao][0]
            
        # 3. Movimentação Padrão (Andando/Parado)
        else:
            if agora - self.ultimo_update_animacao > self.velocidade_animacao:
                self.ultimo_update_animacao = agora
                self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]

        # Sincroniza visual sem tremor
        self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))
        self.mask = pygame.mask.from_surface(self.image)

    def morrer(self, grupos=None):
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 8, 100)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 80)
        Items.spawn_drop(self.posicao, grupos, 'cafe', 1, 1)
        self.kill()