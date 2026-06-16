import pygame
import random
import math
from source.feats.projetil import Carabin
from source.systems.entitymanager import entity_manager
from source.enemies.standard.elite import Elite

class ArbiterAttacks:
    def realizar_teleporte(self):
        raio_min, raio_max = 250, 450
        tentativas, padding = 40, 10 
        
        for _ in range(tentativas):
            angulo = random.uniform(0, 2 * math.pi)
            distancia = random.uniform(raio_min, raio_max)
            
            nova_x = self.jogador.posicao.x + math.cos(angulo) * distancia
            nova_y = self.jogador.posicao.y + math.sin(angulo) * distancia
            pos_candidata = pygame.math.Vector2(nova_x, nova_y)

            if (self.verificar_posicao_valida(pos_candidata) and
                self.verificar_posicao_valida(pos_candidata + pygame.math.Vector2(padding, 0)) and
                self.verificar_posicao_valida(pos_candidata + pygame.math.Vector2(-padding, 0)) and
                self.verificar_posicao_valida(pos_candidata + pygame.math.Vector2(0, -padding)) and
                self.verificar_posicao_valida(pos_candidata + pygame.math.Vector2(0, padding))):
                self.posicao = pos_candidata
                return True 
        return False 

    def checar_se_travou(self, agora, dist_sq):
        """Verifica se o boss está preso. Se sim, intercepta o fluxo e ativa o Anti-Stuck de Combate."""
        if agora - getattr(self, 'ultimo_check_posicao', 0) > 1500:
            pos_anterior = getattr(self, 'posicao_anterior', self.posicao)
            dist_movida_sq = self.posicao.distance_squared_to(pos_anterior)
            
            if dist_movida_sq < 900 and dist_sq > 40000 and self.estado_habilidade == 'idle':
                self.estado_habilidade = 'antistuck_combat'
                self.ja_teleportou_stuck = False
                self.spray_iniciado = False
                self.spray_restante = 0
                
                # Ativa o sistema de camuflagem oficial (Duração estendida para caber todo o spray estático)
                self.iniciar_invisibilidade(alpha_alvo=0, fade_out=800, fade_in=600, duracao=2500, flashing=False)
                return True
            
            self.ultimo_check_posicao = agora
            self.posicao_anterior = pygame.math.Vector2(self.posicao.x, self.posicao.y)
        return False

    def processar_antistuck_combat(self, agora, delta_time, fase_invis):
        """Garante imobilidade completa, realiza teleporte em hold e descarrega spray gigante oculto."""
        self.velocidade = 0  
        self.velocidade_animacao = 0

        # 1. Teleporta assim que sumir por completo do mapa
        if fase_invis == 'hold' and not self.ja_teleportou_stuck:
            self.realizar_teleporte()
            self.ja_teleportou_stuck = True
            self.tempo_teleporte_stuck = agora

        # 2. Pequena janela de delay após surgir na nova posição para iniciar a tempestade de tiros
        if self.ja_teleportou_stuck and not self.spray_iniciado:
            if agora - self.tempo_teleporte_stuck > 500:
                self.spray_restante = 20  # 20 tiros colossais
                self.spray_iniciado = True
                self.cronometro_spray = 0

        # 3. Executa a rajada contínua veloz enquanto o hold/fade_in atuam em segundo plano
        if getattr(self, 'spray_iniciado', False) and self.spray_restante > 0:
            self.cronometro_spray += delta_time * 1000
            if self.cronometro_spray >= self.intervalo_spray:
                self.cronometro_spray = 0
                self.spray_restante -= 1
                self.atirar_carabina(spread=0.1, dano=15) # Spread maior para varredura de área

        # 4. Quando a invisibilidade expirar por completo, reseta o ciclo para o IDLE
        if fase_invis is None and self.ja_teleportou_stuck:
            self.estado_habilidade = 'idle'
            self.wait = 1200
            self.ultimo_check_posicao = agora
            self.posicao_anterior = pygame.math.Vector2(self.posicao.x, self.posicao.y)

    def processar_inicio_stealth(self, agora):
        self.adicionar_escudo(250)
        self.ja_teleportou = False  
        self.iniciar_invisibilidade(alpha_alvo=0, fade_out=1000, fade_in=600, duracao=self.duracao_invisibilidade, flashing=False)
        self.cooldown_invisibilidade = self.novo_cooldown(14000, 18000)
        self.ultima_invisibi = agora

    def checar_colisao_stealth(self):
        fase = getattr(self, 'invis_phase', None)
        if fase in ['fade_out', 'hold'] and self.hitbox.colliderect(self.jogador.hitbox):
            self.trigger_flash(duracao=400, bonus_alpha=120)

    def processar_tiro_carabina(self, agora, delta_time):
        if self.carabina_restante > 0:
            self.cronometro_carabina += delta_time * 1000
            if self.cronometro_carabina >= self.intervalo_carabina:
                self.cronometro_carabina = 0
                self.carabina_restante -= 1
                self.atirar_carabina(spread=0.03, dano=15)
        else:
            self.cooldown_carabin = self.novo_cooldown(4500, 7000)
            self.estado_habilidade = 'idle'
            self.wait = 800

    def atirar_carabina(self, spread, dano):
        direcao_tiro = self.calcular_direcao_tiro(spread)
        self.trigger_flash(duracao=35, bonus_alpha=60)  # Trigger flash obrigatório ao disparar!
        Carabin(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites,),
            jogador=self.jogador,
            game=self.game,
            dono='INIMIGO',
            tamanho=(20, 20),
            dano=dano,
            velocidade=550,
            direcao_spread=direcao_tiro
        )

    def processar_invocacao(self, agora):
        """Canaliza por 1 segundo e invoca Elites normais nas laterais em posições válidas."""
        if agora - self.tempo_inicio_summon >= self.duracao_summon:
             offsets = [pygame.math.Vector2(30, 0), pygame.math.Vector2(-30, 0)]
             
             for offset in offsets:
                 pos_spawn = self.posicao + offset
                 if self.verificar_posicao_valida(pos_spawn):
                    novo_elite = Elite(pos_spawn, game=self.game)

                    entity_manager.all_sprites.add(novo_elite)
                    entity_manager.inimigos_grupo.add(novo_elite)
                         
             self.ultima_invocacao = agora
             self.cooldown_invocacao = self.novo_cooldown(12000, 18000)
             self.estado_habilidade = 'idle'
             self.wait = 1500