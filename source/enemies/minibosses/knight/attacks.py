import pygame
import random
import math
from source.feats.projetil import LaserBeam
from source.feats.skills.cone_strike import ConeStrikeAviso
from source.feats.skills.promethean_tp import PrometheanTeleport
from source.enemies.standard.watcher import SuperWatcher
from source.systems.entitymanager import entity_manager

class KnightAttacks:
    def executar_laser(self):
        agora = pygame.time.get_ticks()
        
        # Fica totalmente parado (telegraph) carregando o ataque
        self.velocidade = 0  
        
        if agora - self.start_laser >= self.wait_laser:
            direcao_tiro = self.calcular_direcao_tiro(0.1)
            LaserBeam(
                posicao_inicial=self.posicao,
                grupos=(entity_manager.all_sprites,),
                jogador=self.jogador,
                game=self.game,
                dono='INIMIGO',
                tamanho=(128, 24),
                dano=self.dano_base * 2.5,
                velocidade=1500,
                direcao_spread=direcao_tiro,
                vai_rotacionar=True,
                color='red'
            )

            # Restaura cooldown e aplica trava
            self.cooldown_laser = self.novo_cooldown(8000, 14000)
            self.ultimo_laser = agora
            self.wait = agora + 1000
            self.estado_habilidade = 'idle'

    def executar_run(self):
        agora = pygame.time.get_ticks()
                
        if not self.running:
            self.velocidade_animacao = 120
            self.running = True
            self.velocidade = self.velocidade_base * 6.0
            self.inicio_run = agora
        else:
            if agora - self.inicio_run >= self.duracao_run:
                
                # Restaura cooldown e aplica trava
                self.cooldown_run = self.novo_cooldown(10000, 18000)
                self.ultima_run = agora
                
                self.velocidade = self.velocidade_base
                self.velocidade_animacao = 300
                self.running = False
                
                self.wait = agora + 1000
                self.estado_habilidade = 'idle'
    
    def executar_tp(self):
        agora = pygame.time.get_ticks()
        raio_min = 250
        raio_max = 300
        tentativas = 40
        pos_valida_encontrada = False
        
        # Loop de varredura idêntico ao do Zealot
        for _ in range(tentativas):
            angulo = random.uniform(0, 2 * math.pi)
            distancia = random.uniform(raio_min, raio_max)
            
            dest_x = self.jogador.posicao.x + math.cos(angulo) * distancia
            dest_y = self.jogador.posicao.y + math.sin(angulo) * distancia
            pos_candidata = pygame.math.Vector2(dest_x, dest_y)

            # Utiliza o método de verificação presente na estrutura do seu BaseEnemy
            if self.verificar_posicao_valida(pos_candidata):
                self.tp_destino = pos_candidata
                pos_valida_encontrada = True
                break # Ponto limpo encontrado! Sai do loop de checagem.

        if pos_valida_encontrada:
            # Só inicia o teleporte e fica invisível se o destino for seguro
            self.tp_orb = PrometheanTeleport(
                start_pos   = self.posicao, 
                target_pos  = self.tp_destino, 
                pixel_size  = (4, 12),
                offset_xy   = 120,
                num_quad    = (20, 30),
                grupos      = [entity_manager.all_sprites], 
                game        = self.game,
                velocidade  = 650
            )

            self.alpha_atual = 0
            self.estado_habilidade = 'tp_traveling'
        else:
            self.cooldown_tp = self.novo_cooldown(1500, 3000)
            self.ultimo_tp = agora
            self.estado_habilidade = 'idle'

    def update_tp(self):
        # Monitora a partícula: se morreu/chegou, finaliza o TP
        if self.tp_orb and not self.tp_orb.alive():
            self.finalizar_tp()

    def finalizar_tp(self):
        self.posicao = pygame.math.Vector2(self.tp_orb.posicao)
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        self.alpha_atual = 255 
        
        # Restaura cooldown e aplica trava
        agora = pygame.time.get_ticks()
        self.cooldown_tp = self.novo_cooldown(4000, 7000)
        self.ultimo_tp = agora
        
        self.tp_orb = None
        self.wait = agora + 1000
        self.estado_habilidade = 'idle'

    def executar_summon(self):
        agora = pygame.time.get_ticks()
        
        # Só permite invocar se não houver um Watcher ativo vivo
        if self.watcher_ativo is None or not self.watcher_ativo.alive():
            
            self.velocidade = 0  # Boss para completamente para abrir a carapaça
            self.inicio_summon = agora
            self.estado_habilidade = 'summoning'

            # Dispara dados das costas dele para cima
            posicao_costas = self.posicao + pygame.math.Vector2(0, -20)
            alvo_visual = self.posicao + pygame.math.Vector2(0, -200) # Onde o drone vai se materializar
            
            PrometheanTeleport(
                start_pos=posicao_costas, 
                target_pos=alvo_visual, 
                pixel_size=(3, 8),
                offset_xy=80,
                num_quad=(3, 6),
                grupos=[entity_manager.all_sprites], 
                game=self.game,
                velocidade=250 # Sobe bem devagar simulando a "impressão 3D" do drone
            )
        else:
            # Se o Watcher ainda está vivo mas o Boss tentou usar a skill, aborta e tenta de novo rápido
            self.estado_habilidade = 'idle'
            self.ultimo_summon = agora
            self.cooldown_summon = 10000 

    def update_summon(self):
        agora = pygame.time.get_ticks()
        tempo_preparacao = 1000 # O Knight fica vulnerável por 1.5s construindo o Watcher
        
        if agora - self.inicio_summon >= tempo_preparacao:
            # Calcula a posição de spawn acima da cabeça do Knight
            posicao_spawn = self.posicao + pygame.math.Vector2(0, -160)
            
            self.watcher_ativo = SuperWatcher(posicao_spawn, self.game)
            
            # Restaura cooldown e devolve o Boss ao loop de combate
            self.cooldown_summon = self.novo_cooldown(15000, 19000)
            self.ultimo_summon = agora
            self.wait = agora + 1000
            self.estado_habilidade = 'idle'

    def executar_cleave(self):
        agora = pygame.time.get_ticks()
        # Fica totalmente parado (telegraph) focado no jogador
        self.velocidade = 0  

        # Calcula a direção exata apontando para o jogador
        if getattr(self, 'direcao_cleave_travada', None) is None:
            self.direcao_cleave_travada = self.jogador.posicao - self.posicao
        
        if agora - self.start_cleave >= self.wait_cleave:
            
            # Invoca o objeto do ConeStrike
            ConeStrikeAviso(
                posicao=self.posicao,
                direcao=self.direcao_cleave_travada,
                grupos=[entity_manager.all_sprites],
                game=self.game,
                dono='INIMIGO',
                preset='cleave_knight' 
            )

            # Restaura cooldown e aplica a trava global para ele não atacar imediatamente
            self.cooldown_cleave = self.novo_cooldown(6000, 10000)
            self.ultimo_cleave = agora
            self.wait = agora + 800
            self.estado_habilidade = 'idle'

            # Limpa a memória da mira para que o próximo Cleave recalcule a posição
            self.direcao_cleave_travada = None