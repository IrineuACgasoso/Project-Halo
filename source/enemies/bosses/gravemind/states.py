import pygame
import random
from source.feats.effects import DustParticle
from source.systems.entitymanager import entity_manager

class GravemindAI:
    def executar_estados(self, agora, delta_time):
        # 1. Se estiver animando respawn, paralisa a IA padrão e trata a máscara
        if self.is_animating_respawn:
            self.atualizar_animacao_respawn(delta_time, agora)
            return

        # 2. IA do Miasma Gas (Exclusivo da Forma Final)
        if getattr(self, 'is_final_form', False) and not getattr(self, 'gas_invocado', False):
            from .vfx import MiasmaGas
            MiasmaGas(self.posicao, self.raio_safezone, self.game, (entity_manager.all_sprites,), self)
            self.gas_invocado = True

        # 3. Transições de Habilidades
        if self.estado_habilidade == 'idle':
            # TRAVA GLOBAL: Só escolhe um novo ataque se o tempo de respiro/wait acabou
            if agora < self.wait:
                return
            
            if getattr(self, 'is_final_form', False) and agora - self.ultima_cabeca >= self.cooldown_cabecas:
                self.estado_habilidade = 'heads'
                self.cabecas_restantes = 2
            # Dentro da sua lógica de decisão (ex: quando o boss for escolher a próxima skill no idle)
            if agora - getattr(self, 'ultima_chuva', 0) >= getattr(self, 'cooldown_chuva', 0):
                self.estado_habilidade = 'acid_rain'
                self.morteiros_restantes = 15 # Quantidade de tiros que vão chover
                self.ultimo_morteiro_tick = agora
                
            elif agora - self.ultima_baforada >= self.cooldown_acido:
                self.estado_habilidade = 'acid'
                self.tiros_restantes = self.tiros_burst
            elif agora - self.ultima_infeccao >= self.cooldown_infeccao:
                self.estado_habilidade = 'infection'
                self.spawns_restantes = 5

        # 4. Resolução das Habilidades
        if self.estado_habilidade == 'acid': 
            self.acid_breath_attack(agora)
        elif self.estado_habilidade == 'infection': 
            self.spawn_infection_attack(agora)
        elif self.estado_habilidade == 'heads': 
            self.spawn_heads_attack(agora)
        elif self.estado_habilidade == 'acid_rain': 
            self.acid_rain_attack(agora)

    def atualizar_animacao_respawn(self, delta_time, agora):
        sprite_base = self.sprites['left'][0]
        
        if self.estado_respawn == 'reaparecendo':
            self.altura_atual += 300 * delta_time
            if agora - self.timer_particula > 50:
                self.timer_particula = agora
                for _ in range(3):
                    off_x = random.randint(-self.tamanho_sprite[0]//4, self.tamanho_sprite[0]//4)
                    DustParticle((self.posicao_chao.x + off_x, self.posicao_chao.y), (entity_manager.all_sprites,))
            
            if self.altura_atual >= self.tamanho_sprite[1]:
                self.altura_atual = self.tamanho_sprite[1]
                self.is_animating_respawn = False
                self.estado_respawn = None    

        elif self.estado_respawn == 'desaparecendo':
            self.altura_atual -= 300 * delta_time
            if self.altura_atual <= 0: 
                self.respawn_logic()
                return

        self.game.camera.shake(intensidade=self.intensidade_shake)

        # Falso recuo da Máscara (Subindo do Buraco)
        h = int(max(1, self.altura_atual))
        self.image = pygame.Surface((self.tamanho_sprite[0], h), pygame.SRCALPHA).convert_alpha()
        area_recorte = pygame.Rect(0, self.tamanho_sprite[1] - h, self.tamanho_sprite[0], h)
        self.image.blit(sprite_base, (0, 0), area_recorte)
        
        self.rect = self.image.get_rect(centerx=self.posicao_chao.x, bottom=self.posicao_chao.y)
        self.posicao = pygame.math.Vector2(self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)