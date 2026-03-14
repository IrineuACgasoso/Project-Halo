import pygame
from systems.entitymanager import entity_manager
from feats.weapon import Projetil_PingPong

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

        # OTIMIZAÇÃO: Não recriamos o Grupo. Iteramos sobre o grupo existente 
        # e filtramos logicamente para evitar overhead de memória.
        inimigos = entity_manager.inimigos_grupo.sprites()
        projeteis_player = entity_manager.projeteis_jogador_grupo.sprites()

        # 1. Projéteis do Jogador -> Inimigos
        for projetil in projeteis_player:
            # Pegamos apenas inimigos próximos ou na tela se quiser otimizar mais, 
            # mas o spritecollide já faz um bom trabalho com Rects.
            atingidos = pygame.sprite.spritecollide(
                projetil, 
                entity_manager.inimigos_grupo, 
                False, 
                self.custom_collision
            )

            for inimigo in atingidos:
                if getattr(inimigo, 'invulneravel', False): continue
                
                if isinstance(projetil, Projetil_PingPong):
                    if inimigo not in projetil.inimigos_ja_atingidos:
                        inimigo.receber_dano(projetil.dano)
                        projetil.inimigos_ja_atingidos.add(inimigo)
                else:
                    inimigo.receber_dano(projetil.dano)
                    projetil.kill()
                    break # Projétil comum morre no primeiro impacto

        # 2. Projéteis dos Inimigos -> Jogador (Usa Rect para ser justo e rápido)
        colisoes_proj_inimigos = pygame.sprite.spritecollide(
            player,
            entity_manager.projeteis_inimigos_grupo,
            True,
            pygame.sprite.collide_rect
        )
        for projetil in colisoes_proj_inimigos:
            player.tomar_dano_direto(projetil.dano)

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
        itens_coletados = pygame.sprite.spritecollide(player, entity_manager.item_group, True)
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
        for inimigo in inimigos:
            if inimigo.vida <= 0:
                inimigo.morrer((entity_manager.all_sprites, entity_manager.item_group))