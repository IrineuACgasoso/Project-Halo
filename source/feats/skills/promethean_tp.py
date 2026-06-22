import pygame
import math
from random import randint, uniform

class PrometheanTeleport(pygame.sprite.Sprite):
    # CACHE ESTÁTICO: As superfícies dos estilhaços são geradas UMA ÚNICA VEZ para o jogo inteiro
    _surface_cache = {}

    def __init__(self, start_pos, target_pos, pixel_size, offset_xy, num_quad, grupos, game, velocidade=800):
        super().__init__(grupos)
        self.game = game
        self.all_sprites_group = grupos[0] if isinstance(grupos, (list, tuple)) else grupos
        
        self.posicao = pygame.math.Vector2(start_pos)
        self.target_pos = pygame.math.Vector2(target_pos)
        self.pixel_size = pixel_size
        self.offset_xy = max(offset_xy, 48)
        self.num_quad = num_quad  # Agora define dinamicamente a quantidade de partículas por frame
        self.velocidade = velocidade
        
        # Configuração do Núcleo
        self.image = pygame.Surface((self.offset_xy, self.offset_xy), pygame.SRCALPHA)
        self.cor_promethean = (255, 90, 0)
        self.rect = self.image.get_rect(center=self.posicao)
        
        self.direcao = (self.target_pos - self.posicao)
        if self.direcao.length() > 0:
            self.direcao = self.direcao.normalize()
            
        self.tempo_decorrido = 0.0
        
        # Garante que o cache de partículas exista
        if not PrometheanTeleport._surface_cache:
            self._gerar_cache_particulas()
            
        self.renderizar_nucleo_estatico()

    def _gerar_cache_particulas(cls):
        """Pré-renderiza um cache global de partículas (tamanhos de 1 a 20)."""
        cores = {
            'laranja': (255, 90, 0),
            'claro': (255, 170, 50),
            'branco': (255, 255, 255)
        }
        # Em vez de atrelar ao pixel_size de uma instância específica, 
        # criamos de 1 a 20 pixels para servir QUALQUER habilidade no jogo todo.
        for nome_cor, rgb in cores.items():
            for tam in range(1, 21): 
                surf = pygame.Surface((tam, tam), pygame.SRCALPHA)
                surf.fill(rgb)
                cls._surface_cache[(nome_cor, tam)] = surf

    def renderizar_nucleo_estatico(self):
        """Desenha o núcleo (mesma lógica visual anterior)."""
        self.image.fill((0, 0, 0, 0))
        centro = self.offset_xy // 2
        for i in range(5):
            raio = 16 - i * 2
            if raio > 0:
                alpha = 30 + (i * 35)
                surf_glow = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf_glow, (255, 60, 0, alpha), (raio, raio), raio)
                self.image.blit(surf_glow, (centro - raio, centro - raio))
                
        pontos_extern = [(centro, centro - 10), (centro + 10, centro), (centro, centro + 10), (centro - 10, centro)]
        pontos_intern = [(centro, centro - 4), (centro + 4, centro), (centro, centro + 4), (centro - 4, centro)]
        pygame.draw.polygon(self.image, self.cor_promethean, pontos_extern)
        pygame.draw.polygon(self.image, (255, 255, 255), pontos_intern)

    def update(self, delta_time):
        self.tempo_decorrido += delta_time
        
        move_amount = self.direcao * self.velocidade * delta_time
        distancia_restante = self.posicao.distance_to(self.target_pos)
        
        if move_amount.length() >= distancia_restante:
            self.posicao = self.target_pos
            self.kill()
            return
        else:
            self.posicao += move_amount

        # Movimento Senoidal
        vetor_onda = pygame.math.Vector2(-self.direcao.y, self.direcao.x)
        offset_onda = vetor_onda * math.sin(self.tempo_decorrido * 45.0) * 12.0
        posicao_final = self.posicao + offset_onda
        self.rect.center = (round(posicao_final.x), round(posicao_final.y))

        # INJEÇÃO DE PARTÍCULAS OTIMIZADA:
        # Em vez de criar uma classe Sprite, criamos um objeto fantasma leve direto no grupo de renderização
        for _ in range(randint(self.num_quad[0], self.num_quad[1])):
            tamanho_pixel = randint(self.pixel_size[0], self.pixel_size[1])
            sorteio = randint(0, 10)
            cor_chave = 'branco' if sorteio > 8 else ('claro' if sorteio > 4 else 'laranja')
            
            # Pega a superfície pronta do cache (Custo zero de memória!)
            surf_pronta = PrometheanTeleport._surface_cache[(cor_chave, tamanho_pixel)].copy()
            
            # Cria um "Sprite inline" usando uma instância genérica do Pygame
            particula = pygame.sprite.Sprite(self.all_sprites_group)
            particula.image = surf_pronta
            particula.posicao = posicao_final + pygame.math.Vector2(uniform(-6, 6), uniform(-6, 6))
            particula.rect = particula.image.get_rect(center=particula.posicao)
            particula.alpha = 255
            particula.velocidade_fade = uniform(400, 700)
            particula.deriva = pygame.math.Vector2(uniform(-30, 30), uniform(-30, 30))
            
            # Injeta o comportamento de update diretamente na instância
            def particula_update(dt, self=particula):
                self.posicao += self.deriva * dt
                self.alpha -= self.velocidade_fade * dt
                if self.alpha <= 0:
                    self.kill()
                else:
                    self.image.set_alpha(int(self.alpha))
                    self.rect.center = (round(self.posicao.x), round(self.posicao.y))
                    
            particula.update = particula_update