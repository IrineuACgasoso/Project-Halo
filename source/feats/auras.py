import pygame
from source.feats.particulas import emitir_leque
from source.systems.gameclock import relogio
from source.systems.entitymanager import entity_manager
from source.systems.dano import Dano, AURA

class EnergyAura(pygame.sprite.Sprite):
    def __init__(self, owner, raio, dano_contato, game, cor_base=(0, 150, 255), impenetravel=True,
                 bloqueia_tiros=False, empurrao_max=None):
        """`bloqueia_tiros`: projéteis do jogador morrem na borda (menos os de perfuração infinita e os
        sem velocidade própria: granada, tijolo e lâmina atravessam).
        `empurrao_max`: px por passo. Sem limite, espremer o jogador contra uma parede o joga para o
        outro lado dela assim que a sobreposição passa do raio de colisão dele."""
        super().__init__(entity_manager.all_sprites)
        self.owner = owner
        self.game = game
        self.raio = raio
        self.cor_base = cor_base
        self.impenetravel = impenetravel
        self.bloqueia_tiros = bloqueia_tiros
        self.empurrao_max = empurrao_max

        self.dano_contato = dano_contato
        self.cooldown_dano = 400 
        self.ultimo_dano = 0
        
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.owner.posicao)
        self.desenhar_aura()

    def desenhar_aura(self):
        """Gera o visual dinâmico com base na cor fornecida"""
        self.image.fill((0, 0, 0, 0))
        r, g, b = self.cor_base
        
        for raio_atual in range(self.raio - 20, self.raio + 10, 4):
            alpha = max(0, 60 - abs(self.raio - raio_atual) * 3)
            pygame.draw.circle(self.image, (r, g, b, alpha), (self.raio, self.raio), raio_atual, 3)
            
        # Brilho central (clareia um pouco a cor base)
        r_claro = min(r + 50, 255)
        g_claro = min(g + 50, 255)
        b_claro = min(b + 50, 255)
        pygame.draw.circle(self.image, (r_claro, g_claro, b_claro, 180), (self.raio, self.raio), self.raio, 2)

    def update(self, delta_time):
        # Se o dono morrer, a aura se desfaz
        if not self.owner.alive():
            self.kill()
            return
            
        self.rect.center = (round(self.owner.posicao.x), round(self.owner.posicao.y))

        if self.bloqueia_tiros:
            self._parar_tiros()

        # Dono atordoado (sistema de status) não causa dano de contato
        if self.owner.status.atordoado:
            return

        # === LÓGICA DE DANO E COLISÃO ===
        player = self.game.player
        vetor_distancia = player.posicao - self.owner.posicao
        distancia_atual = vetor_distancia.length()
        raio_colisao = self.raio + 15
        
        if distancia_atual < raio_colisao:
            # SÓ APLICA O EMPURRÃO SE FOR IMPENETRÁVEL
            if self.impenetravel:
                if distancia_atual > 0:
                    direcao_empurrao = vetor_distancia.normalize()
                else:
                    direcao_empurrao = pygame.math.Vector2(1, 0)
                    
                empurrao = raio_colisao - distancia_atual
                if self.empurrao_max is not None and empurrao > self.empurrao_max:
                    player.posicao = player.posicao + direcao_empurrao * self.empurrao_max
                else:
                    player.posicao = self.owner.posicao + direcao_empurrao * raio_colisao
                player.rect.center = (round(player.posicao.x), round(player.posicao.y))
                
            # O TICK DE DANO ACONTECE DE QUALQUER FORMA
            agora = relogio.agora()
            if agora - self.ultimo_dano >= self.cooldown_dano:
                self.ultimo_dano = agora
                player.receber_dano(Dano(self.dano_contato, AURA, self.owner))

    def _parar_tiros(self):
        centro = self.owner.posicao
        for tiro in entity_manager.projeteis_jogador_grupo:
            if tiro.piercing == float('inf') or tiro.velocidade <= 0:
                continue
            if centro.distance_squared_to(tiro.posicao) <= self.raio * self.raio:
                emitir_leque(tiro.posicao, tiro.posicao - centro, 3, (self.cor_base, (255, 255, 255)), (3, 4),
                             abertura_graus=120, velocidade=(80, 200), duracao_ms=(150, 300))
                tiro.kill()


class PlayerAura(pygame.sprite.Sprite):
    sobrevive_troca_de_fase = True   # StageManager (roteiro E5)

    def __init__(self, jogador, raio, dano_por_segundo, grupos):
        super().__init__(grupos)
        self.jogador = jogador
        self.ativa = True
        
        # Atributos exigidos pelo seu CollisionManager (Item 5)
        self.dono = 'PLAYER'
        self.raio = raio
        self.radius = raio # Para collide_circle
        self.dano_por_segundo = dano_por_segundo
        
        # Visual: Criamos a superfície e a máscara de colisão radial
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.jogador.posicao)
        
        # O Pygame usa o atributo 'radius' para o collide_circle
        self.radius = self.raio 
        self.desenhar_aura()

    def desenhar_aura(self):
        """Gera o visual dinâmico em anéis idêntico ao da EnergyAura"""
        self.image.fill((0, 0, 0, 0)) # Limpa a superfície anterior
        r, g, b = (255, 192, 0) 
        
        # Renderiza os anéis concêntricos com fade de opacidade (Alpha) nas bordas
        for raio_atual in range(self.raio - 20, self.raio + 10, 4):
            alpha = max(0, 60 - abs(self.raio - raio_atual) * 3)
            pygame.draw.circle(self.image, (r, g, b, alpha), (self.raio, self.raio), raio_atual, 3)
            
        # Brilho de contenção central (clareia e define a borda principal)
        r_claro = min(r + 50, 255)
        g_claro = min(g + 50, 255)
        b_claro = min(b + 50, 255)
        pygame.draw.circle(self.image, (r_claro, g_claro, b_claro, 180), (self.raio, self.raio), self.raio, 2)

    def atualizar_stats(self, novo_raio, novo_dano):
        """Chamado pelo upgrade da Arma"""
        self.raio = novo_raio
        self.radius = self.raio # Atualiza para o motor de colisão
        self.dano_por_segundo = novo_dano
        
        # Redimensiona a imagem
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.jogador.posicao)
        self.desenhar_aura()

    def update(self, delta_time):
        self.rect.center = self.jogador.posicao

        # Shield quebrado
        if self.jogador.escudo_atual <= 0:

            self.ativa = False
            self.image.set_alpha(0)
            return

        # Shield ativo
        self.ativa = True
        self.image.set_alpha(120)