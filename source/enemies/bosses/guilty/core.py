import pygame
from source.feats.items import Items
from source.enemies.base.enemy_base import BaseEnemy

from .setup import GuiltySetup
from .states import GuiltyAI
from .attacks import GuiltyAttacks

class GuiltySpark(BaseEnemy, GuiltySetup, GuiltyAI, GuiltyAttacks):
    def __init__(self, posicao, game, grupos=None):
        super().__init__(posicao, vida_base=1500, dano_base=80, velocidade_base=100, 
                        game=game, sprite_key='guilty', flip_sprite=True)
                         
        self.titulo = "343 GUILTY SPARK, Monitor da Instalação 04"
        self.is_boss = True

        self.setup_animation(estado_inicial='left', velocidade_animacao=300)
        self.mask = pygame.mask.from_surface(self.image)
        
        self.inicializar_habilidades()

    def receber_dano(self, quantidade):
        self.sentinelas_majors = [s for s in self.sentinelas_majors if s.alive()]

        # INTERCEPTAÇÃO: DEFESA DAS SENTINELAS MAJORS (Fase 2)
        if self.estado_fase == 'RAGE_F2' and len(self.sentinelas_majors) > 0:
            quantidade *= 0.05

        # Se estiver na transição, ele ignora completamente o dano (Terminais ativos)
        if self.estado_fase == 'TRANSICAO':
            return

        if not self.imune:
            super().receber_dano(quantidade)

    def tomar_dano_direto(self, quantidade):
        self.receber_dano(quantidade)

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()

        self.executar_estados(agora, delta_time)

        if self.estado_habilidade != 'manutencao':
            direcao_x = self.jogador.posicao.x - self.posicao.x 
            self.set_sprite_direction(direcao_x)
        
        super().update(delta_time, paredes)
        self.animar()

    def animar(self):
        if self.estado_habilidade in ['laser_charge', 'laser_firing']:
            self.image = self.sprites[self.estado_animacao][1] 
        elif self.estado_habilidade == 'sentinel':
            self.image = self.sprites[self.estado_animacao][2] 
        elif self.estado_habilidade == 'manutencao':
            self.image = self.sprites[self.estado_animacao][0] 
        else:
            self.image = self.sprites[self.estado_animacao][0]

        self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))
        self.mask = pygame.mask.from_surface(self.image)

    def draw_laser(self, superficie, deslocamento):
        """Atualiza a origem com offset dinâmico antes de renderizar"""
        if self.estado_habilidade == 'laser_firing':
            # AJUSTE DO OLHO: Desloca o início do laser dependendo para onde ele olha
            offset_x = 50 if self.estado_animacao == 'right' else -50
            self.beam_principal.posicao = self.posicao + pygame.math.Vector2(offset_x, -5)
            
            self.beam_principal.draw(superficie, deslocamento)

    def morrer(self, grupos=None):
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 4, 100)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 50)
        Items.spawn_drop(self.posicao, grupos, 'cafe', 1, 1)
        self.kill()