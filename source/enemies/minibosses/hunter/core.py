import pygame
from source.enemies.base.enemy_base import BaseEnemy
from source.feats.items import Items

# Imports locais do pacote
from .setup import HunterSetup
from .states import HunterAI
from .attacks import HunterAttacks, HunterMortarProjectile

class Hunter(BaseEnemy, HunterSetup, HunterAI, HunterAttacks):
    def __init__(self, posicao, game, **kwargs):
        super().__init__(posicao, vida_base=1000, dano_base=40, velocidade_base=40, game=game, sprite_key='hunter', flip_sprite=True)
        self.titulo = "HUNTER, O Guerreiro Mgalekgolo"
        self.is_boss = True

        self.setup_animation(
            estado_inicial='left',
            velocidade_animacao=900
        )        
        
        self.mask = pygame.mask.from_surface(self.image)
        self.inicializar_habilidades()

    def animar(self):
        agora = pygame.time.get_ticks()
        
        # TRAVA DA ANIMAÇÃO: Se ele estiver atordoado, não avança o frame (Fica congelado)
        if self.estado_habilidade == 'stun':
            return 
            
        if agora - getattr(self, 'ultimo_update_animacao', 0) > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            
            self.mask = pygame.mask.from_surface(self.image)
            self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))

    def receber_dano(self, quantidade):
        dano_final = quantidade
        
        if self.estado_habilidade == 'stun':
            player_x = self.jogador.posicao.x
            hunter_x = self.posicao.x
            
            # Multiplicador de Dano nas costas (Armadura Exposta)
            if self.estado_animacao == 'right' and player_x < hunter_x:
                dano_final *= 4  
            elif self.estado_animacao == 'left' and player_x > hunter_x:
                dano_final *= 4  
                
        super().receber_dano(dano_final)

    def tomar_dano_direto(self, quantidade):
        self.receber_dano(quantidade)

    def morrer(self, grupos=None):
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 2, 100)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 50)
        Items.spawn_drop(self.posicao, grupos, 'cafe', 1, 1)
        self.kill()

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()
        dist_sq = self.posicao.distance_squared_to(self.jogador.posicao)

        self.executar_estados(agora, delta_time, dist_sq)

        if self.estado_habilidade == 'run':
            self.processar_run(agora, delta_time, paredes)

        elif self.estado_habilidade == 'stun':
            # Fica completamente parado, sem calcular rota
            pass
            
        else:
            super().update(delta_time, paredes)

        if self.estado_habilidade not in ['run', 'stun']:
            direcao_x = self.jogador.posicao.x - self.posicao.x 
            self.set_sprite_direction(direcao_x)
            
        self.animar()