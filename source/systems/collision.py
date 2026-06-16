import pygame
from source.systems.entitymanager import entity_manager
from source.player.weapons import *
from source.feats.projetil import *

class CollisionManager:
    def __init__(self, game):
        self.game = game

    @classmethod
    def custom_collision(cls, sprite1, sprite2):
        """Lógica de colisão otimizada com suporte inteligente a Hitboxes Customizadas."""
        
        # 1. Blindagem Total (Furtividade, Cutscenes, Dash)
        if getattr(sprite2, 'invulneravel', False):
            return False

        # 2. Colisão Radial (Ultra rápida, excelente para auras/explosões)
        if getattr(sprite2, 'usar_circulo', False):
            return pygame.sprite.collide_circle(sprite1, sprite2)
        
        # Ele tenta pegar a 'collision_rect' (estilo Jega).
        # Se não achar, tenta a 'hitbox' (estilo Zealot).
        # Se o objeto não for um boss/inimigo complexo, usa o 'rect' normal.
        rect1 = getattr(sprite1, 'collision_rect', getattr(sprite1, 'hitbox', sprite1.rect))
        rect2 = getattr(sprite2, 'collision_rect', getattr(sprite2, 'hitbox', sprite2.rect))

        # 3. Checa colisão entre as hitboxes (Matemática pura, quase zero custo de CPU)
        if rect1.colliderect(rect2):
            
            # 4. Colisão Perfeita (Máscara de Pixel)
            # A máscara só será calculada se os tiros já estiverem tocando a hitbox customizada!
            if hasattr(sprite1, 'mask') and hasattr(sprite2, 'mask'):
                # O collide_mask nativo exige que os sprites tenham .rect baseados na imagem
                return pygame.sprite.collide_mask(sprite1, sprite2)
            
            # Se não tiver mask, a hitbox fina já validou o hit.
            return True

        return False

    @classmethod
    def aura_collision(cls, sprite_inimigo, sprite_aura):
        """Colisão customizada para auras não detectarem inimigos invisíveis."""
        if getattr(sprite_inimigo, 'invulneravel', False):
            return False
        return pygame.sprite.collide_circle(sprite_inimigo, sprite_aura)

    def update(self, delta_time):
        player = self.game.player
        if not player: return

        # 1. Projéteis do Jogador -> Inimigos
        for projetil in entity_manager.projeteis_jogador_grupo:
            atingidos = pygame.sprite.spritecollide(
                projetil, 
                entity_manager.inimigos_grupo, 
                False, 
                self.custom_collision
            )
            for inimigo in atingidos:
                projetil.ao_atingir_alvo(inimigo)

        # 2. Projéteis dos Inimigos -> Jogador
        colisoes_proj_inimigos = pygame.sprite.spritecollide(
            player,
            entity_manager.projeteis_inimigos_grupo,
            False, 
            pygame.sprite.collide_rect
        )
        for projetil in colisoes_proj_inimigos:
            projetil.ao_atingir_alvo(player)

        # 3. Colisão de Contato: Jogador -> Inimigos (Ignora se estiver oculto)
        inimigos_contato = pygame.sprite.spritecollide(
            player,
            entity_manager.inimigos_grupo,
            False,
            self.custom_collision
        )
        for inimigo in inimigos_contato:
            if not getattr(inimigo, 'invulneravel', False):
                player.tomar_dano(inimigo)

        # 4. Coleta de itens
        itens_coletados = pygame.sprite.spritecollide(player, entity_manager.items_grupo, True)
        for item in itens_coletados:
            player.coletar_item(item)

        # 5. Dano de Área (Auras) -> CORRIGIDO para usar aura_collision!
        if entity_manager.auras_grupo:
            colisoes_aura = pygame.sprite.groupcollide(
                entity_manager.inimigos_grupo,
                entity_manager.auras_grupo,
                False, False,
                self.aura_collision # <- Mudado aqui! Agora respeita a invisibilidade
            )
            for inimigo, auras in colisoes_aura.items():
                if not getattr(inimigo, 'invulneravel', False):
                    total_dano = sum(aura.dano_por_segundo for aura in auras if aura.ativa)
                    inimigo.receber_dano(total_dano * delta_time)

        # 6. Check de Morte
        for inimigo in entity_manager.inimigos_grupo:
            if inimigo.vida <= 0:
                inimigo.morrer((entity_manager.all_sprites, entity_manager.items_grupo))