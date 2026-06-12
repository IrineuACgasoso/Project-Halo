import pygame
import random
from .vfx import GuiltyTeleport
from source.enemies.base import BaseEnemy
from source.enemies.standard.sentinel import Sentinel
from source.systems.entitymanager import entity_manager


class ForerunnerTerminal(BaseEnemy):
    def __init__(self, posicao, game, monitor_pai):
        super().__init__(posicao, vida_base=1, dano_base=30, velocidade_base=0, game=game, sprite_key='terminal', flip_sprite=False)
        self.titulo = "TERMINAL FORERUNNER"
        self.monitor_pai = monitor_pai
        
        # Spawner autônomo de Sentinelas
        self.cooldown_invocacao = 3000 
        self.ultima_invocacao = pygame.time.get_ticks() + random.randint(-2000, 0) # Desincroniza os spawns

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()
        
        # LÓGICA DE SPAWN: Só spawna se o Monitor ainda estiver em manutenção
        if self.monitor_pai.estado_fase == 'TRANSICAO':
            if agora - self.ultima_invocacao >= self.cooldown_invocacao:
                self.ultima_invocacao = agora
                self.invocar_sentinela_defensiva()
                
        super().update(delta_time, paredes)

    def draw(self, superficie, deslocamento):
        """Desenha o terminal com um efeito de Glow Azul Neon"""
        # Centraliza a posição com base na câmera
        pos_tela_centro = pygame.math.Vector2(self.posicao.x - deslocamento.x, self.posicao.y - deslocamento.y)
        # Cria um pulso sutil baseado no tempo do jogo para o glow "respirar"
        pulso = abs(pygame.time.get_ticks() % 1000 - 500) / 500 * 4
        
        for raio_glow in range(32, 50, 3):
            # Quanto mais distante do centro, mais transparente fica
            alpha = max(0, 90 - (raio_glow - 32) * 5)
            # Superfície temporária dedicada para aceitar transparência por pixel
            glow_surf = pygame.Surface((raio_glow * 2, raio_glow * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (0, 180, 255, alpha), (raio_glow, raio_glow), raio_glow + int(pulso), 2)
            # Blita centralizado
            superficie.blit(glow_surf, pos_tela_centro - pygame.math.Vector2(raio_glow, raio_glow))
            
        pygame.draw.circle(superficie, (100, 220, 255), pos_tela_centro, 31, 3)
        
        pos_tela_topleft = pygame.math.Vector2(self.rect.topleft) - deslocamento
        superficie.blit(self.image, pos_tela_topleft)

    def invocar_sentinela_defensiva(self):
        offset = pygame.math.Vector2(random.choice([-60, 60]), random.choice([-60, 60]))
        pos_spawn = self.posicao + offset
        
        if self.game.mapa.posicao_e_valida(pos_spawn):
            GuiltyTeleport((round(pos_spawn.x), round(pos_spawn.y)))
            nova_sentinela = Sentinel(pos_spawn, self.game)
            entity_manager.all_sprites.add(nova_sentinela)
            entity_manager.inimigos_grupo.add(nova_sentinela)

    def morrer(self, grupos=None):
        self.kill()