import pygame
from source.systems.entitymanager import entity_manager
from source.player.weapons import *
from source.feats.projetil import *

class CollisionManager:
    def __init__(self, game):
        self.game = game

    @staticmethod
    def custom_collision(sprite1, sprite2):
        """
        Lógica de colisão otimizada:
        1. Se o inimigo tiver 'usar_circulo', usa colisão radial (ultra rápida).
        2. Se não, tenta colisão por máscara (precisa), mas apenas se o Rect colidir antes.
        """
        # Se for um boss ou inimigo grande marcado para usar círculo:
        if getattr(sprite2, 'usar_circulo', False):
            return pygame.sprite.collide_circle(sprite1, sprite2)
        
        # Colisão padrão: Rect primeiro (otimização interna do Pygame), depois Mask
        if pygame.sprite.collide_rect(sprite1, sprite2):
            return pygame.sprite.collide_mask(sprite1, sprite2)
        return False

    def update(self, delta_time):
        player = self.game.player
        if not player: return

        # 1. Projéteis do Jogador -> Inimigos
        # Usamos o grupo específico do EntityManager. 
        # Como esse grupo SÓ tem tiros do player, não precisa checar 'if dono == player'
        for projetil in entity_manager.projeteis_jogador_grupo:
            atingidos = pygame.sprite.spritecollide(
                projetil, 
                entity_manager.inimigos_grupo, 
                False, 
                self.custom_collision
            )
            for inimigo in atingidos:
                # A MÁGICA ESTÁ AQUI: Chamamos o método que você já tem na base.
                # Ele vai aplicar o dano, checar piercing e, no caso da Needler, 
                # vai contar as agulhas. Tudo sem o Manager saber os detalhes.
                projetil.ao_atingir_alvo(inimigo)

        # 2. Projéteis dos Inimigos -> Jogador
        # Mudamos de 'True' para 'False' no kill, para deixar o PROJÉTIL decidir se morre
        colisoes_proj_inimigos = pygame.sprite.spritecollide(
            player,
            entity_manager.projeteis_inimigos_grupo,
            False, 
            pygame.sprite.collide_rect
        )
        for projetil in colisoes_proj_inimigos:
            # O projétil do inimigo também usa o ao_atingir_alvo!
            # Assim, se um inimigo tiver um tiro com piercing, funciona no player também.
            projetil.ao_atingir_alvo(player)

        # 3. Colisão de Contato: Jogador -> Inimigos
        # Aqui o custom_collision ajuda muito com o Scarab
        inimigos_contato = pygame.sprite.spritecollide(
            player,
            entity_manager.inimigos_grupo,
            False,
            self.custom_collision
        )
        for inimigo in inimigos_contato:
            if not getattr(inimigo, 'invulneravel', False):
                player.tomar_dano(inimigo)

        # 4. Coleta de itens (Rect é suficiente)
        itens_coletados = pygame.sprite.spritecollide(player, entity_manager.items_grupo, True)
        for item in itens_coletados:
            player.coletar_item(item)

        # 5. Dano de Área (Auras)
        if entity_manager.auras_grupo:
            # groupcollide é eficiente para muitos-para-muitos
            colisoes_aura = pygame.sprite.groupcollide(
                entity_manager.inimigos_grupo,
                entity_manager.auras_grupo,
                False, False,
                pygame.sprite.collide_circle
            )
            for inimigo, auras in colisoes_aura.items():
                if not getattr(inimigo, 'invulneravel', False):
                    total_dano = sum(aura.dano_por_segundo for aura in auras)
                    inimigo.receber_dano(total_dano * delta_time)

        # 6. Check de Morte (Limpeza concentrada)
        for inimigo in entity_manager.inimigos_grupo:
            if inimigo.vida <= 0:
                inimigo.morrer((entity_manager.all_sprites, entity_manager.items_grupo))