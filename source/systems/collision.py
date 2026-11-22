import pygame
from source.systems.entitymanager import entity_manager
from source.systems.eventos import eventos, INIMIGO_MORREU
from source.systems.dano import Dano, CONTATO, AURA

# Inimigo com colisão circular (Scarab) é candidato de toda consulta: o círculo do
# collide_circle passa da borda do rect, e esses inimigos são raros (bosses).
_RECT_SEMPRE_CANDIDATO = pygame.Rect(-10 ** 6, -10 ** 6, 2 * 10 ** 6, 2 * 10 ** 6)


def rect_de_colisao(sprite):
    """O retângulo que `custom_collision` compara (collision_rect > hitbox > rect)."""
    return getattr(sprite, 'collision_rect', getattr(sprite, 'hitbox', sprite.rect))


class BroadphaseInimigos:
    """Broadphase (roteiro C2): os retângulos de colisão dos inimigos são lidos 1× por frame,
    e cada consulta filtra os candidatos com `Rect.collidelistall` (laço em C). Os candidatos
    voltam na ordem do grupo, e a decisão final continua sendo de `custom_collision`.

    Limite: um inimigo que surge ou se move DURANTE a passada de colisão (ex.: teleporte ao
    tomar dano) só é visto pelos projéteis no frame seguinte."""

    def __init__(self):
        self.inimigos = []
        self.rects = []

    def reconstruir(self, grupo):
        self.inimigos = grupo.sprites()
        self.rects = [_RECT_SEMPRE_CANDIDATO if getattr(inimigo, 'usar_circulo', False)
                      else rect_de_colisao(inimigo)
                      for inimigo in self.inimigos]

    def candidatos(self, rect, grupo):
        """Inimigos cujo retângulo toca `rect` e que ainda estão em `grupo`, na ordem do grupo."""
        inimigos = self.inimigos
        return [inimigos[i] for i in rect.collidelistall(self.rects) if grupo.has(inimigos[i])]


class CollisionManager:
    def __init__(self, game):
        self.game = game
        self.broadphase = BroadphaseInimigos()

    def colidindo_com_inimigos(self, sprite):
        """Mesmo resultado de `spritecollide(sprite, inimigos_grupo, False, custom_collision)`,
        testando só os candidatos do broadphase."""
        grupo = entity_manager.inimigos_grupo
        return [inimigo for inimigo in self.broadphase.candidatos(rect_de_colisao(sprite), grupo)
                if self.custom_collision(sprite, inimigo)]

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
        rect1 = rect_de_colisao(sprite1)
        rect2 = rect_de_colisao(sprite2)

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

    @staticmethod
    def colisao_hitbox_jogador(jogador, projetil):
        """Projétil inimigo x jogador usando a HITBOX do jogador (menor que o sprite).
        Antes usava collide_rect no sprite inteiro: tiros acertavam "no ar" ao lado do personagem."""
        hitbox = getattr(jogador, 'hitbox', jogador.rect)
        return hitbox.colliderect(getattr(projetil, 'collision_rect', projetil.rect))

    @classmethod
    def aura_collision(cls, sprite_inimigo, sprite_aura):
        """Colisão customizada para auras não detectarem inimigos invisíveis."""
        if getattr(sprite_inimigo, 'invulneravel', False):
            return False
        return pygame.sprite.collide_circle(sprite_inimigo, sprite_aura)

    def update(self, delta_time):
        player = self.game.player
        if not player: return
        self.broadphase.reconstruir(entity_manager.inimigos_grupo)

        # 1. Projéteis do Jogador -> Inimigos
        for projetil in entity_manager.projeteis_jogador_grupo:
            atingidos = self.colidindo_com_inimigos(projetil)
            if not atingidos:
                continue
            # Alvo mais próximo primeiro (ordem do grupo era arbitrária)
            if len(atingidos) > 1:
                px, py = projetil.rect.center
                atingidos.sort(key=lambda e: (e.rect.centerx - px) ** 2 + (e.rect.centery - py) ** 2)

            perfuracao_finita = getattr(projetil, 'piercing', float('inf')) != float('inf')
            for inimigo in atingidos:
                # 1) Projétil já consumido neste frame não pode acertar mais ninguém
                if not projetil.alive():
                    break
                # 2) Perfuração finita: no máximo 1 acerto por alvo (antes gastava toda a
                #    perfuração no MESMO inimigo em frames seguidos, multiplicando o dano)
                if perfuracao_finita:
                    ja_atingidos = projetil.__dict__.setdefault('_alvos_atingidos', set())
                    if inimigo in ja_atingidos:
                        continue
                    ja_atingidos.add(inimigo)
                projetil.ao_atingir_alvo(inimigo)

        # 2. Projéteis dos Inimigos -> Jogador
        colisoes_proj_inimigos = pygame.sprite.spritecollide(
            player,
            entity_manager.projeteis_inimigos_grupo,
            False, 
            self.colisao_hitbox_jogador
        )
        for projetil in colisoes_proj_inimigos:
            projetil.ao_atingir_alvo(player)

        # 3. Colisão de Contato: Jogador -> Inimigos (Ignora se estiver oculto)
        inimigos_contato = self.colidindo_com_inimigos(player)
        for inimigo in inimigos_contato:
            # Se o inimigo estiver inofensivo (ex: no ar), ignora o dano
            if getattr(inimigo, 'inofensivo', False):
                continue
            if not getattr(inimigo, 'invulneravel', False):
                player.receber_dano(Dano(inimigo.dano, CONTATO, inimigo))
                player.contra_atacar_com_espinhos(inimigo)

        # 4. Coleta de itens
        itens_coletados = pygame.sprite.spritecollide(player, entity_manager.items_grupo, True)
        for item in itens_coletados:
           item.coletar(player)

        # 5. Dano de Área (Auras) -> CORRIGIDO para usar aura_collision!
        # As auras deste grupo são do jogador (MK2): atordoado, ele não ataca
        if entity_manager.auras_grupo and not player.status.atordoado:
            colisoes_aura = pygame.sprite.groupcollide(
                entity_manager.inimigos_grupo,
                entity_manager.auras_grupo,
                False, False,
                self.aura_collision # <- Mudado aqui! Agora respeita a invisibilidade
            )
            for inimigo, auras in colisoes_aura.items():
                if not getattr(inimigo, 'invulneravel', False):
                    total_dano = sum(aura.dano_por_segundo for aura in auras if aura.ativa)
                    inimigo.receber_dano(Dano(total_dano * delta_time, AURA, player))

        # 6. Check de Morte
        for inimigo in entity_manager.inimigos_grupo:
            if inimigo.vida <= 0:
                inimigo.morrer((entity_manager.all_sprites, entity_manager.items_grupo))
                # morrer() pode adiar a morte (Warden: a consciência espera os corpos)
                if not inimigo.alive():
                    eventos.emitir(INIMIGO_MORREU, inimigo=inimigo)