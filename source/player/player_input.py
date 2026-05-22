import pygame

from source.systems.entitymanager import entity_manager

class PlayerInput:
    def input(self):
        # Muda os vetores se eles estão sendo pressionados ou não
        # Direita = 1, Esquerda = -1, Cima = 1, Baixo = -1
        # Se a tecla está sendo pressionada, ela é True
        keys = pygame.key.get_pressed()
        self.direcao.x = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
        self.direcao.y = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
        # Caso a direção não for parado, normaliza o vetor para que ao se mover na diagonal, não se mova mais rápido
        if self.direcao != (0,0):
            self.direcao = self.direcao.normalize()

    # --- ÁREA DOS HACKS ---
    def debug_hacks(self):
        hack = pygame.key.get_pressed()
        
        # Hack L: Level Up
        if hack[pygame.K_l]:
            falta = self.experiencia_level_up - self.experiencia_atual
            self.ganhar_xp(falta)
        
        # Hack P: Spawnar Portal (Instant Exit)
        elif hack[pygame.K_p]:
            # Verifica se o jogo já tem um portal ativo. 
            if self.game.portal_atual is None:
                # Importação local para evitar erro circular (Player importar Portal e Portal importar Player)
                from source.feats.effects import Portal 
                
                offset = 50 if self.estado_animacao == 'right' else -50
                pos_portal = self.posicao + pygame.math.Vector2(offset, 0)
                
                novo_portal = Portal(pos_portal, entity_manager.all_sprites)
                self.game.portal_atual = novo_portal

        elif hack[pygame.K_b]:
            if self.game.boss_atual is None:
                if hasattr(self.game, 'spawner'):
                    self.game.spawner.forcar_proximo_boss()