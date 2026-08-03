# enemies/didact/attacks.py
import pygame
import random
from source.feats.projetil import LaserBeam
from source.feats.skills.onda_emp import OndaEMP
from source.feats.skills.artilharia import ArtilhariaAviso
from source.feats.effects import LaserWarning
from source.systems.entitymanager import entity_manager

class GuardianAttacks:
    """Mixin responsável pela execução das habilidades e instanciamento de projéteis."""

    def disparar_emp(self):
        OndaEMP(
            posicao=self.posicao.copy(), 
            grupos=self.game.all_sprites, 
            game=self.game, 
            atacante=self,
            preset='guardian_emp' # Informando o preset profissionalizado
        )

    def disparar_artilharia(self):
        self.cooldown_artilharia = self.novo_cooldown(600, 1200)
        
        offset = pygame.math.Vector2(random.randint(-150, 150), random.randint(-150, 150))
        alvo = self.jogador.posicao + offset

        ArtilhariaAviso(
            posicao=alvo,
            grupos=[entity_manager.all_sprites],
            game=self.game,
            dono='INIMIGO',    
            preset='didact_collapse'
            )