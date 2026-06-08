import pygame
import random
import math
from source.feats.projetil import LaserBeam
from source.enemies.standard.sentinel import Sentinel
from source.systems.entitymanager import entity_manager
from .vfx import GuiltyTeleport

class GuiltyAttacks:
    def invocar_sentinelas(self):
        agora = pygame.time.get_ticks()

        # O Guilty precisa "carregar" o ataque por um tempo (self.wait)
        if agora - self.start_sentinel >= self.wait:
            eixos = [
                (0, -self.offset_invocacao), # Norte
                (0, self.offset_invocacao),  # Sul
                (-self.offset_invocacao, 0), # Oeste
                (self.offset_invocacao, 0)   # Leste
            ]

            for off_x, off_y in eixos:
                pos_spawn = pygame.math.Vector2(self.posicao.x + off_x, self.posicao.y + off_y)
                
                if self.game.mapa.posicao_e_valida(pos_spawn):
                    GuiltyTeleport((round(pos_spawn.x), round(pos_spawn.y)))
                    nova_sentinela = Sentinel(pos_spawn, self.game)
                    entity_manager.all_sprites.add(nova_sentinela)
                    entity_manager.inimigos_grupo.add(nova_sentinela)

            self.ultima_invocacao = agora
            self.cooldown_invocacao = self.novo_cooldown(6000, 9000)
            self.estado_habilidade = 'idle' 

    def laser_attack(self):
        agora = pygame.time.get_ticks()
        direcao_beam = self.calcular_direcao_tiro()

        if agora - self.start_laser >= self.wait:
            if self.laser_restantes > 0:
                if agora - self.ultimo_laser >= self.intervalo_burst:
                    self.laser_restantes -= 1
                    self.ultimo_laser = agora

                    LaserBeam(
                        posicao_inicial = self.posicao.copy(),
                        grupos          = (entity_manager.all_sprites,),
                        jogador         = self.jogador,
                        game            = self.game,
                        dono            ='INIMIGO',
                        tamanho         = (150, 25),
                        dano            = self.dano_base * 2,
                        velocidade      = 1500,  
                        direcao_spread  = direcao_beam,
                        vai_rotacionar  = True,
                        color           ='blue'
                    )
            else:
                self.ultimo_laser = agora
                self.cooldown_laser = self.novo_cooldown(3000, 7000)
                self.estado_habilidade = 'idle' 

    def teleporte(self):
        posicao_valida = False
        tentativas = 0
        max_tentativas = 30
        nova_pos = pygame.math.Vector2(0, 0)

        while not posicao_valida and tentativas < max_tentativas:
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
            
        self.estado_habilidade = 'idle'

    def rage(self):
        if not self.enrage:
            self.enrage = True
            # Transição visual feita no animar() com self.sprites
            self.trocar_variante('damaged')            
            self.cooldown_invocacao = self.novo_cooldown(500, 4000)
            self.cooldown_laser = self.novo_cooldown(500, 4000)
            self.num_laser += 2
            self.velocidade_anterior *= 2.5