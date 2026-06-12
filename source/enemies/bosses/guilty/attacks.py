import pygame
import random
import math
from source.systems.entitymanager import entity_manager
from source.feats.skills.purge_grid import PurgeGrid
from .vfx import GuiltyTeleport

class GuiltyAttacks:
    def logica_laser_rastreavel(self, agora, delta_time):
        if self.estado_habilidade == 'laser_charge':
            self.game.camera.shake(intensidade=2)
            if agora - self.tempo_inicio_laser > 1000:
                self.estado_habilidade = 'laser_firing'
                self.tempo_inicio_laser = agora
                
                offset_x = 25 if self.estado_animacao == 'right' else -25
                self.beam_principal.mira_atual = self.posicao + pygame.math.Vector2(offset_x, -5)

        elif self.estado_habilidade == 'laser_firing':
            offset_x = 50 if self.estado_animacao == 'right' else -50
            self.beam_principal.posicao = self.posicao + pygame.math.Vector2(offset_x, -5)
            
            self.beam_principal.update(delta_time, self.jogador.posicao)
            
            if agora - self.tempo_inicio_laser > self.duracao_laser_rastreavel:
                self.estado_habilidade = 'idle'
                self.ultimo_laser = agora
                self.cooldown_laser = self.novo_cooldown(3000, 7000) if not self.enrage else self.novo_cooldown(1500, 4000)
                self.wait = pygame.time.get_ticks() + 1000


    def invocar_sentinelas(self, de_elite=False):
        agora = pygame.time.get_ticks()
        if agora - self.start_sentinel >= 1000:
            eixos = [(0, -self.offset_invocacao), (0, self.offset_invocacao), 
                     (-self.offset_invocacao, 0), (self.offset_invocacao, 0)]
            
            from source.enemies.standard.sentinel import Sentinel, SentinelMajor

            for off_x, off_y in eixos:
                pos_spawn = pygame.math.Vector2(self.posicao.x + off_x, self.posicao.y + off_y)
                if self.game.mapa.posicao_e_valida(pos_spawn):
                    GuiltyTeleport((round(pos_spawn.x), round(pos_spawn.y)))

                    # Escolhe a Sentinela correspondente à fase
                    if de_elite:
                        nova_sentinela = SentinelMajor(pos_spawn, self.game)
                        self.sentinelas_majors.append(nova_sentinela)
                    else:
                        nova_sentinela = Sentinel(pos_spawn, self.game)
                        
                    entity_manager.all_sprites.add(nova_sentinela)
                    entity_manager.inimigos_grupo.add(nova_sentinela)

            self.ultima_invocacao = agora
            self.cooldown_invocacao = self.novo_cooldown(6000, 9000) if not self.enrage else self.novo_cooldown(3000, 6000)
            self.wait = pygame.time.get_ticks() + 1000
            self.estado_habilidade = 'idle'


    def teleporte(self):
        posicao_valida = False
        tentativas = 0
        nova_pos = pygame.math.Vector2(0, 0)

        while not posicao_valida and tentativas < 30:
            tentativas += 1
            angulo = random.uniform(0, 2 * math.pi)
            distancia = random.uniform(200, 450)
            target_x = self.jogador.posicao.x + distancia * math.cos(angulo)
            target_y = self.jogador.posicao.y + distancia * math.sin(angulo)
            nova_pos.update(target_x, target_y)
            
            if self.game.mapa.posicao_e_valida(nova_pos):
                posicao_valida = True

        if posicao_valida:
            GuiltyTeleport(self.rect.center)
            self.posicao = pygame.math.Vector2(nova_pos)
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))
            GuiltyTeleport(self.rect.center)
            self.ultimo_tp = pygame.time.get_ticks()
            self.wait = pygame.time.get_ticks() + 500
            
        self.estado_habilidade = 'idle'

    def rage(self, agora):
        self.enrage = True
        self.estado_fase = 'RAGE_F2'
        
        # Devolve a agressividade
        self.estado_habilidade = 'idle'
        self.imune = False
        self.velocidade_anterior *= 1.8
        self.velocidade = self.velocidade_anterior
        
        # Evita que ele faça 5 coisas ao mesmo tempo.
        self.ultimo_laser = agora
        self.ultima_invocacao = agora
        self.ultimo_tp = agora
        
        # Atrasa o Purge inicial para não ser imediato
        self.ultimo_purge = agora - (self.purge_cooldown - 2000) 
        
        try:
            self.trocar_variante('damaged')
        except Exception:
            pass

    def purge(self, agora):
        """Dispara a Purga usando o sistema otimizado de Presets"""
        if agora - self.ultimo_purge >= self.purge_cooldown:
            # Sorteia diretamente o nome do preset configurado no config.py
            preset_escolhido = random.choice(['guilty_hell_x', 'guilty_hell_y'])
            
            # Criamos o worker e iniciamos a fila cronometrada de forma limpa!
            self.ataque_purga = PurgeGrid(game=self.game, caster=self, preset=preset_escolhido)
            self.ataque_purga.iniciar(agora)

            self.ultimo_purge = agora