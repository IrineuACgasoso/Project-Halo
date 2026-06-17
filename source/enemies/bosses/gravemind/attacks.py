import pygame
import random
import math
from source.feats.projetil import AcidBreath
from source.feats.skills.mortar import CanhaoParabolico
from source.enemies.standard.infection import Infection, FloodElite, FloodMarine, FloodCarry
from source.systems.entitymanager import entity_manager
from .vfx import FloodWarning

class GravemindAttacks:
    def acid_breath_attack(self, agora):
        direcao_tiro = self.calcular_direcao_tiro(0.3)
        if self.tiros_restantes > 0:
            if agora - self.ultimo_tiro_burst >= 150:
                self.tiros_restantes -= 1
                self.ultimo_tiro_burst = agora
                AcidBreath(
                    posicao_inicial=self.posicao, 
                    grupos=(entity_manager.all_sprites,), 
                    jogador=self.jogador, 
                    game=self.game,
                    dono='INIMIGO',
                    tamanho=(48, 48),
                    dano=20,
                    velocidade=self.velocidade_baforada,
                    direcao_spread=direcao_tiro
                )
        else:
            self.ultima_baforada = agora
            self.cooldown_acido = self.novo_cooldown(*self.cd_acido_base)
            self.wait = agora + 1000
            self.estado_habilidade = 'idle'

    def spawn_infection_attack(self, agora):
        if self.spawns_restantes > 0:
            if agora - self.ultimo_spawn_tick >= 200:
                for _ in range(10):
                    pos_spawn = self.posicao + pygame.math.Vector2(random.randint(-300, 300), random.randint(-300, 300))
                    if self.verificar_posicao_valida(pos_spawn):
                        Infection(posicao=pos_spawn, game=self.game)
                        self.spawns_restantes -= 1  
                        self.ultimo_spawn_tick = agora # Reseta o timer de cadência
                        break
        else:
            self.ultima_infeccao = agora
            self.cooldown_infeccao = self.novo_cooldown(*self.cd_infeccao_base)
            self.estado_habilidade = 'idle'
            self.wait = agora + 500

    def spawn_heads_attack(self, agora):
        if self.cabecas_restantes > 0:
            if agora - self.intervalo_cabeca_tick >= 2000:
                for _ in range(20):
                    angulo = random.uniform(0, 2 * math.pi)
                    distancia = random.uniform(200, self.raio_safezone - 150)
                    pos_spawn = self.posicao + pygame.math.Vector2(math.cos(angulo) * distancia, math.sin(angulo) * distancia)

                    if self.verificar_posicao_valida(pos_spawn):
                        FloodWarning(posicao=pos_spawn, game=self.game, spawn_minion=True)
                        self.cabecas_restantes -= 1       # Só gasta se der certo!
                        self.intervalo_cabeca_tick = agora
                        break
        else:
            self.ultima_cabeca = agora
            self.cooldown_cabecas = self.novo_cooldown(*self.cd_cabecas_base)
            self.estado_habilidade = 'idle'
            self.wait = agora + 1500

    def tentacles_attack(self, agora):
        """
        Invoca o ecossistema PurgeGrid focado na perseguição direcionada por vetor
        do Gravemind até a posição atual do Player.
        """
        from source.feats.skills.purge_grid.orchestrator import PurgeGrid

        # Instancia o Orquestrador passando o preset de perseguição do Flood
        ataque_tentaculo = PurgeGrid(self.game, self, preset='tentaculos_perseguidores')
        
        ataque_tentaculo.iniciar(agora)
        
        # (O PurgeGrid continuará executando de forma independente no loop principal)
        self.ultimos_tentaculos = agora
        self.cooldown_tentaculos = self.novo_cooldown(*self.cd_tentaculos_base)
        
        self.wait = agora + 1200  
        self.estado_habilidade = 'idle'

    def spawn_infection_forms_attack(self, agora):
        """
        Ataque de Fase 2 do Gravemind Final.
        Invoca de forma cadenciada Formas de Combate Flood sorteadas via random.choice.
        """
        if self.forms_restantes > 0:
            # Cadência entre o nascimento de cada Flood (evita que nasçam todos no mesmo frame)
            if agora - getattr(self, 'ultimo_spawn_tick', 0) >= 400:
                for _ in range(15):  # Tentativas de encontrar um ponto válido na arena
                    angulo = random.uniform(0, 2 * math.pi)
                    distancia = random.uniform(200, 500)
                    pos_spawn = self.posicao + pygame.math.Vector2(math.cos(angulo) * distancia, math.sin(angulo) * distancia)

                    if self.verificar_posicao_valida(pos_spawn):
                        # === POOL DE CLASSES DISPONÍVEIS ===
                        # Passamos as classes diretamente como objetos!
                        classes_flood = [FloodElite, FloodCarry, FloodMarine]
                        classe_sorteada = random.choice(classes_flood)

                        # Instancia dinamicamente a classe sorteada
                        classe_sorteada(posicao=pos_spawn, game=self.game)

                        # Atualiza os controladores de fluxo
                        self.forms_restantes -= 1
                        self.ultimo_spawn_tick = agora
                        break
        else:
            # Trata o encerramento do ataque e define os tempos de recarga
            self.ultima_infeccao_forms = agora
            self.cooldown_infeccao_forms = self.novo_cooldown(7000, 9000) # 6 a 9 segundos de CD
            
            self.wait = agora + 1000  # 1 segundo de respiro para o Gravemind antes do próximo ataque
            self.estado_habilidade = 'idle'


    def acid_rain_attack(self, agora):
        # Apenas um exemplo de fluxo. Adapte com os seus cooldowns e tiros_restantes!
        if self.morteiros_restantes > 0:
            if agora - self.ultimo_morteiro_tick >= 250: # Dispara rápido como uma metralhadora
                self.morteiros_restantes -= 1
                self.ultimo_morteiro_tick = agora
                
                # Sorteia um alvo perto do jogador ou espalhado pela arena
                offset = pygame.math.Vector2(random.randint(-700, 700), random.randint(-700, 700))
                alvo = self.jogador.posicao + offset
                
                CanhaoParabolico(
                    start_pos=self.posicao.copy(),
                    target_pos=alvo,
                    game=self.game,
                    dono='INIMIGO',
                    sprite_key='green_laser',
                    tamanho=(64, 64),
                    velocidade=250,
                    altura_maxima=1000, # Vai mais alto pra parecer que está "chovendo"
                    preset_artilharia='acid_rain' # Usa a explosão do Gravemind!
                )
        else:
            self.ultima_chuva = agora
            self.cooldown_chuva = self.novo_cooldown(*self.cd_chuva_base)
            self.wait = agora + 1500  # 1.5 segundos de folga para o jogador respirar
            self.estado_habilidade = 'idle'