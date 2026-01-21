import pygame
from entitymanager import entity_manager
from feats.weapon import Projetil_PingPong

class CollisionManager:
    def __init__(self, game):
        self.game = game

    def update(self, delta_time):
        player = self.game.player
        if not player: return

        # Filtro de Inimigos Alvejáveis (Exclui quem está invulneravel)
        # Usamos getattr para evitar erro caso o inimigo não tenha o atributo
        inimigos_vivos = [i for i in entity_manager.inimigos_grupo if not getattr(i, 'invulneravel', False)]
        inimigos_grupo_fisico = pygame.sprite.Group(inimigos_vivos)

        # Projéteis do Jogador -> Inimigos
        for projetil in list(entity_manager.projeteis_jogador_grupo):
            inimigos_atingidos = pygame.sprite.spritecollide(
                projetil, 
                inimigos_grupo_fisico, 
                False,
                pygame.sprite.collide_mask
            )

            if inimigos_atingidos:
                if isinstance(projetil, Projetil_PingPong):
                    for inimigo in inimigos_atingidos:
                        if inimigo not in projetil.inimigos_ja_atingidos:
                            inimigo.vida -= projetil.dano
                            projetil.inimigos_ja_atingidos.add(inimigo)
                else:
                    for inimigo in inimigos_atingidos:
                        inimigo.vida -= projetil.dano
                    projetil.kill()
        
        # Projéteis dos Inimigos -> Jogador
        colisoes_proj_inimigos = pygame.sprite.spritecollide(
            player,
            entity_manager.projeteis_inimigos_grupo,
            True, # Remove o projétil
            pygame.sprite.collide_rect
        )
        for projetil in colisoes_proj_inimigos:
            player.tomar_dano_direto(projetil.dano)

        # Colisão Direta: Jogador -> Inimigos (Corpo a corpo/Dano de contato)
        for inimigo in inimigos_vivos:
            if pygame.sprite.collide_mask(player, inimigo):
                player.tomar_dano(inimigo)

        # Coleta de itens
        itens_coletados = pygame.sprite.spritecollide(player, entity_manager.item_group, dokill=True)
        for item in itens_coletados:
            player.coletar_item(item)

        # Dano de Área (Auras/DOT)
        if entity_manager.auras_grupo:
            colisoes_aura = pygame.sprite.groupcollide(
                entity_manager.inimigos_grupo, # Auras podem atingir quem está em TP ou não? Ajuste aqui.
                entity_manager.auras_grupo,
                False, False,
                pygame.sprite.collide_circle
            )
            for inimigo, auras in colisoes_aura.items():
                for aura in auras:
                    inimigo.vida -= aura.dano_por_segundo * delta_time
        
        # Check de Morte (Limpeza)
        for inimigo in list(entity_manager.inimigos_grupo):
            if inimigo.vida <= 0:
                inimigo.morrer((entity_manager.all_sprites, entity_manager.item_group))