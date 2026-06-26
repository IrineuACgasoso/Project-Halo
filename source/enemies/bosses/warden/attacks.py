import pygame
import math
import random
from source.systems.entitymanager import entity_manager
from source.feats.skills.cone_strike import ConeStrikeAviso
from source.feats.skills.artilharia import ArtilhariaAviso
from source.feats.projetil import LightRifle
from source.feats.effects import LaserWarning
from source.feats.skills.promethean_tp import PrometheanTeleport # Importe o TP!


class WardenAttacks:
    
    # ==================================================
    # SISTEMA DE TELEPORTE (Copiado/Adaptado do Knight)
    # ==================================================

    def executar_tp(self):
        agora = pygame.time.get_ticks()
        
        # LÊ AS VARIÁVEIS DINÂMICAS (Se não existirem, usa o padrão de fuga)
        raio_min = getattr(self, 'tp_raio_min', 350)
        raio_max = getattr(self, 'tp_raio_max', 450)
        
        pos_valida_encontrada = False
        
        for _ in range(40):
            angulo = random.uniform(0, 2 * math.pi)
            distancia = random.uniform(raio_min, raio_max)
            dest_x = self.jogador.posicao.x + math.cos(angulo) * distancia
            dest_y = self.jogador.posicao.y + math.sin(angulo) * distancia
            pos_candidata = pygame.math.Vector2(dest_x, dest_y)

            if self.verificar_posicao_valida(pos_candidata):
                self.tp_destino = pos_candidata
                pos_valida_encontrada = True
                break

        if pos_valida_encontrada:
            self.tp_orb = PrometheanTeleport(
                start_pos=self.posicao, 
                target_pos=self.tp_destino, 
                pixel_size=(12, 24), offset_xy=180, num_quad=(40, 60),
                grupos=[entity_manager.all_sprites], game=self.game, velocidade=750
            )
            self.alpha_atual = 0
            self.estado_habilidade = 'tp_traveling'
            self.hitbox.width = 0 
        else:
            self.cooldown_tp = self.novo_cooldown(1500, 3000)
            self.ultimo_tp = agora
            self.estado_habilidade = 'idle'

    def update_tp(self):
        """Monitora o projétil do teleporte. Quando ele sumir/chegar, o Warden reaparece."""
        # Se a orb sumiu do mapa (morreu/chegou ao destino), finaliza o TP
        if self.tp_orb is None or not self.tp_orb.alive():
            self.finalizar_tp()
            
    def finalizar_tp(self):
        self.posicao = pygame.math.Vector2(self.tp_orb.posicao)
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        self.alpha_atual = 255 
        
        self.hitbox.width = self.rect.width * 0.4
        
        agora = pygame.time.get_ticks()
        self.cooldown_tp = self.novo_cooldown(6000, 10000)
        self.ultimo_tp = agora
        self.tp_orb = None
        
        # ENCAMINHA PARA O PRÓXIMO ATAQUE (ou 'idle' por padrão)
        self.estado_habilidade = getattr(self, 'tp_prox_estado', 'idle')
        
        if self.estado_habilidade == 'idle':
            self.wait = agora + 500
            
        # Reseta as variáveis de configuração do TP para evitar vazamentos
        self.tp_raio_min = 350
        self.tp_raio_max = 450
        self.tp_prox_estado = 'idle'


    #====================================
    # -------- BRUISER ------------------
    #====================================

    def executar_chop(self):
        agora = pygame.time.get_ticks()
        
        self.velocidade = 0  
        
        if getattr(self, 'direcao_chop_travada', None) is None:
            self.direcao_chop_travada = self.jogador.posicao - self.posicao

        if agora - self.start_chop >= self.wait_chop:
            
            ConeStrikeAviso(
                posicao=self.posicao,
                direcao=self.direcao_chop_travada,
                grupos=[entity_manager.all_sprites],
                game=self.game,
                dono='INIMIGO',
                preset='warden_chop' # Chama a configuração visual/dano que criamos
            )

            self.cooldown_chop = self.novo_cooldown(5000, 7500) # Reusa o mixin nativo de combate!
            self.ultimo_chop = agora
            self.wait = agora + 1000 # Fica parado um tempo depois de bater
            self.estado_habilidade = 'idle'
            # Limpa a trava para o próximo golpe
            self.direcao_chop_travada = None

    def iniciar_bruiser_leap(self, agora):
        self.estado_habilidade = 'bruiser_leap'
        self.velocidade        = 0
        self.leap_start_pos    = self.posicao.copy()
        self.leap_target       = self.jogador.posicao.copy()
        self.leap_start_time   = agora
        self.leap_duracao      = 1200

        self.is_inofensivo  = True

    def processar_bruiser_leap(self, agora, delta_time):
        progresso = (agora - self.leap_start_time) / self.leap_duracao

        if progresso >= 1.0:
            # POUSO — igual ao Tartarus
            self.is_inofensivo   = False

            ArtilhariaAviso(
                posicao=self.posicao.copy(),
                grupos=[entity_manager.all_sprites],
                game=self.game,
                dono='INIMIGO',
                preset='warden_bruiser_leap'
            )

            self.ultimo_stomp   = agora
            self.cooldown_stomp = self.novo_cooldown(7000, 10000)
            self.wait           = agora + 800
            self.estado_habilidade = 'idle'
            return

        self.posicao = self.leap_start_pos.lerp(self.leap_target, progresso)

        altura = math.sin(progresso * math.pi) * 350
        self.rect.center = (round(self.posicao.x), round(self.posicao.y - altura))


    #====================================
    # -------- SNIPER -------------------
    #====================================

    def executar_heavy_rifle(self):
        agora = pygame.time.get_ticks()
        self.velocidade = 0  
        
        if getattr(self, 'direcao_rifle_travada', None) is None:
            self.direcao_rifle_travada = self.calcular_direcao_tiro(0)
            # Cria um objeto "falso" genérico apenas para segurar a posição travada
            class AlvoTravado:
                def __init__(self, pos):
                    self.posicao = pos
            
            # Salva a cópia exata de onde o jogador estava no frame 1 do ataque
            alvo_congelado = AlvoTravado(self.jogador.posicao.copy())
            LaserWarning(owner=self, alvo=alvo_congelado, grupos=[entity_manager.all_sprites], game=self.game, duracao=self.wait_heavy_rifle)
            
        if agora - self.start_heavy_rifle >= self.wait_heavy_rifle:
            LightRifle(
                posicao_inicial=self.posicao.copy(),
                grupos=[entity_manager.all_sprites, entity_manager.projeteis_inimigos_grupo],
                jogador=self.jogador,
                game=self.game,
                dono='INIMIGO',
                tamanho=(96, 96),                
                dano=self.dano_base * 2.5,        
                velocidade=1200,                    
                direcao_spread=self.direcao_rifle_travada
            )
            
            self.cooldown_heavy_rifle = self.novo_cooldown(6000, 9000)
            self.ultimo_heavy_rifle = agora
            self.direcao_rifle_travada = None
            
            # --- INICIA REPOSICIONAMENTO TÁTICO ---
            self.estado_habilidade = 'reposicionando'
            
            # Escolhe um lado para rotacionar (-60 a -30 ou 30 a 60 graus) em relação ao vetor do player
            vetor_para_player = self.jogador.posicao - self.posicao
            angulo_base = math.atan2(vetor_para_player.y, vetor_para_player.x)
            desvio = math.radians(random.choice([random.uniform(-60, -30), random.uniform(30, 60)]))
            
            distancia_reposicao = random.uniform(150, 250)
            novo_x = self.posicao.x + math.cos(angulo_base + desvio) * distancia_reposicao
            novo_y = self.posicao.y + math.sin(angulo_base + desvio) * distancia_reposicao
            
            self.alvo_reposicionamento = pygame.math.Vector2(novo_x, novo_y)

    def executar_hardlight_laser(self, agora, delta_time):
        self.velocidade = 0  # Fica plantado canalizando o laser
        
        if self.estado_habilidade == 'laser_charge':
            # Pequeno tremor na tela para dar peso ao ataque
            if hasattr(self.game, 'camera'):
                self.game.camera.shake(intensidade=1)
                
            # Telegraph (800ms canalizando antes de atirar)
            if agora - self.tempo_inicio_laser > 800:
                self.estado_habilidade = 'laser_firing'
                self.tempo_inicio_laser = agora
                
                # Trava a mira inicial na direção do player para não atirar para trás
                offset_x = 40 if self.estado_animacao == 'right' else -40
                self.beam_principal.mira_atual = self.posicao + pygame.math.Vector2(offset_x, -20)

        elif self.estado_habilidade == 'laser_firing':
            # Ajusta de onde o laser sai (ex: altura do rifle ou olho)
            offset_x = 40 if self.estado_animacao == 'right' else -40
            self.beam_principal.posicao = self.posicao + pygame.math.Vector2(offset_x, -20)
            
            # Atualiza o laser, perseguindo o jogador
            self.beam_principal.update(delta_time, self.jogador.posicao)
            
            # Desliga o laser quando acabar o tempo
            if agora - self.tempo_inicio_laser > self.duracao_laser:
                self.estado_habilidade = 'idle'
                self.ultimo_laser = agora
                self.cooldown_laser = self.novo_cooldown(7000, 12000)
                
                # Tempo de recuperação antes de poder andar novamente
                self.wait = agora + 800

    def draw_laser(self, superficie, deslocamento):
        if self.estado_habilidade == 'laser_firing':
            offset_x = 150 if self.estado_animacao == 'right' else -150
            self.beam_principal.posicao = self.posicao + pygame.math.Vector2(offset_x, 70)
            self.beam_principal.draw(superficie, deslocamento)
    
    #====================================
    #-------- ASSASSIN ------------------
    #====================================

    def executar_purge_assassino(self):
        agora = pygame.time.get_ticks()
        self.velocidade = 0  
        
        if not getattr(self, 'purge_ativo', False):
            self.purge_ativo = True
            self.start_purge = agora
            
            # Importa o Orquestrador aqui
            from source.feats.skills.purge_grid.orchestrator import PurgeGrid
            
            purge = PurgeGrid(self.game, caster=self, preset='assassino_cross')
            purge.iniciar(agora)

        # Tempo de canalização (o boss fica parado com as mãos no chão ou fazendo pose)
        duracao_cast = 800 
        
        if agora - self.start_purge >= duracao_cast:
            self.purge_ativo = False
            self.cooldown_purge = self.novo_cooldown(10000, 14000)
            self.ultimo_purge = agora
            
            # AQUI ESTÁ A MÁGICA: Após atacar, ele ganha o Buff de Velocidade Temporário!
            self.tempo_fim_buff_velocidade = agora + 3500 # Ganha 3.5 segundos de hipervelocidade
            
            self.wait = agora + 200
            self.estado_habilidade = 'idle'