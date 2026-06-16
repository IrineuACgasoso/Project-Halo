import pygame
import math
from source.feats.projetil import ProjetilUniversal
from source.feats.skills.artilharia import ArtilhariaAviso 
from source.systems.entitymanager import entity_manager


class CanhaoParabolico(ProjetilUniversal):
    """Projétil que faz um arco no ar antes de aterrissar e detonar uma Artilharia."""
    def __init__(self, start_pos, target_pos, game, dono, 
                 sprite_key='green_laser', tamanho=(96, 96), 
                 velocidade=400, altura_maxima=250, 
                 preset_artilharia='padrao'):
        
        dir_vec = target_pos - start_pos
        direcao = dir_vec.normalize() if dir_vec.length() > 0 else pygame.math.Vector2(1, 0)
            
        super().__init__(
            posicao_inicial=start_pos,
            grupos=(entity_manager.all_sprites,),
            game=game,
            dono=dono,
            sprite_key=sprite_key, 
            tamanho=tamanho,
            velocidade=velocidade, 
            dano=0, # O dano acontece na explosão da artilharia, não no voo
            duracao=5000,
            direcao_custom=direcao,
            piercing=float('inf'),    
            rotacionar=True
        )
        self.start_pos = pygame.math.Vector2(start_pos)
        self.target_pos = pygame.math.Vector2(target_pos)
        self.total_dist = self.start_pos.distance_to(self.target_pos)
        
        # Variáveis customizáveis
        self.max_height = altura_maxima 
        self.preset_artilharia = preset_artilharia

    def update(self, delta_time):
        self.posicao += self.direcao * self.velocidade * delta_time
        distancia_percorrida = self.start_pos.distance_to(self.posicao)
        
        if distancia_percorrida >= self.total_dist:
            self.detonar_artilharia()
            return

        progresso = distancia_percorrida / self.total_dist
        altura = math.sin(progresso * math.pi) * self.max_height
        self.rect.center = (round(self.posicao.x), round(self.posicao.y - altura))

    def detonar_artilharia(self):
        aviso = ArtilhariaAviso(
            posicao=self.target_pos, 
            grupos=(entity_manager.all_sprites,), 
            game=self.game,
            dono=self.dono,
            preset=self.preset_artilharia # Agora ele usa o preset que você passar!
        )
        self.kill()