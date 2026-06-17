import pygame
from source.systems.entitymanager import entity_manager
from source.feats.skills.artilharia.core import ArtilhariaAviso

class FloodWarning(ArtilhariaAviso):
    """Aviso de onde um ProtoGravemind (Minion) vai nascer. Reaproveita a ArtilhariaAviso."""
    def __init__(self, posicao, game, spawn_minion=False, grupos=None):
        if grupos is None: grupos = (entity_manager.all_sprites,)
        
        # Inicia a artilharia com o preset do Flood
        super().__init__(posicao, grupos, game, dono='BOSS', preset='flood_warning')
        self.is_boss = False

        self.spawn_minion = spawn_minion
        self.spawn_realizado = False

    def update(self, delta_time, paredes=None):
        # A classe pai cuida da animação, tempo e dano (que será 0)
        super().update(delta_time, paredes)
        
        # Assim que explodir (duracao acabou), spawna o minion uma única vez
        if self.explodiu and not self.spawn_realizado:
            from .core import ProtoGravemind
            proto = ProtoGravemind(posicao=self.posicao, game=self.game, is_minion=self.spawn_minion)
            
            # Só passa o bastão se o Proto NÃO for um lacaio qualquer
            if not self.spawn_minion:
                self.game.boss_atual = proto

            self.spawn_realizado = True
            # A classe pai já vai lidar com o self.kill() logo em seguida!

class GravePit(ArtilhariaAviso):
    """Artilharia massiva que invoca o Gravemind Final."""
    def __init__(self, posicao, game, grupos=None):
        if grupos is None: grupos = (entity_manager.all_sprites,)

        self.is_boss = False
        
        # Inicia a artilharia com o preset do Pit
        super().__init__(posicao, grupos, game, dono='BOSS', preset='grave_pit')
        self.spawn_realizado = False

    def update(self, delta_time, paredes=None):
        super().update(delta_time, paredes)
        
        if self.explodiu and not self.spawn_realizado:
            from .core import FinalGravemind
            final_boss = FinalGravemind(posicao=self.posicao, game=self.game)
            self.game.boss_atual = final_boss
            self.spawn_realizado = True


class MiasmaGas(pygame.sprite.Sprite):
    def __init__(self, posicao_boss, raio_seguro, game, grupos, boss):
        super().__init__(grupos)
        self.game = game
        self.boss = boss
        self.posicao_boss = pygame.math.Vector2(posicao_boss)
        self.raio_seguro = raio_seguro
        self.dano_por_segundo = 300
        tamanho = 2500
        
        self.image = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
        self.image.fill((50, 120, 50, 150)) 
        pygame.draw.circle(self.image, (0, 0, 0, 0), (tamanho//2, tamanho//2), self.raio_seguro)
        self.rect = self.image.get_rect(center=self.posicao_boss)
        self.ultimo_dano_tick = pygame.time.get_ticks()

    def update(self, delta_time):
        if not self.boss.alive(): 
            self.kill()
            return
        
        agora = pygame.time.get_ticks()
        if self.game.player.posicao.distance_to(self.posicao_boss) > self.raio_seguro:
            if agora - self.ultimo_dano_tick >= 1000:
                self.game.player.vida_atual -= self.dano_por_segundo
                self.ultimo_dano_tick = agora