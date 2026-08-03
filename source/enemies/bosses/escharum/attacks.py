import pygame
import math
from source.systems.entitymanager import entity_manager
from source.feats.skills.artilharia.core import ArtilhariaAviso
from source.feats.skills.purge_grid import PurgeGrid
from source.enemies.standard.brute import Brute

class TartarusAttacks:
    def processar_hammer_run(self, agora, delta_time, paredes=None):
        # 1. Move o boss baseado no vetor já calculado
        self.posicao += self.direcao * self.velocidade * delta_time
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        # 2. Colisão (opcional, se quiser que ele pare em paredes)
        if paredes:
            self.aplicar_colisao_mapa(paredes)

        # 3. Checa fim da corrida
        dist_sq = self.posicao.distance_squared_to(self.hammer_target)
        if dist_sq <= 400 or (agora - self.hammer_start_time > self.hammer_duration_max):
            # Finaliza o ataque
            self.velocidade = self.velocidade_anterior
            self.ultimo_hammer = agora
            self.estado_habilidade = 'idle'
            self.cooldown_hammer = self.novo_cooldown(4000, 8000)
            self.wait = agora + 1000
            
            # Invoca impacto
            ArtilhariaAviso(
                posicao=self.posicao, 
                grupos=(self.game.all_sprites,), 
                game=self.game,
                dono='BOSS',
                preset='tartarus_run'
            )

    def checar_se_travou(self, agora, dist_sq):
        """Verifica se o boss está preso numa parede. Se sim, força um Leaping Strike."""
        if agora - getattr(self, 'ultimo_check_posicao', 0) > 1500:
            pos_anterior = getattr(self, 'posicao_anterior', self.posicao)
            dist_movida_sq = self.posicao.distance_squared_to(pos_anterior)
            
            # Se moveu menos de 30 pixels (900 sq) em 1.5s e NÃO está colado no player
            if dist_movida_sq < 900 and dist_sq > 40000 and self.estado_habilidade == 'idle':
                
                self.iniciar_pulo(agora) # Força o salto imediatamente
                
                # Atualiza os trackers para não repetir o check no frame que ele pousar
                self.ultimo_check_posicao = agora
                self.posicao_anterior = pygame.math.Vector2(self.posicao.x, self.posicao.y)
                return True
            
            # Atualiza o tracker pro próximo ciclo de 1.5s
            self.ultimo_check_posicao = agora
            self.posicao_anterior = pygame.math.Vector2(self.posicao.x, self.posicao.y)
            
        return False

    def iniciar_pulo(self, agora):
        self.estado_habilidade = 'leaping_takeoff'
        self.tempo_pulo = agora
        self.pulo_start_pos = self.posicao.copy()
        self.pulo_target = self.jogador.posicao.copy()
        self.duracao_pulo = 1200 # 1.2 segundos no ar
        # --- DESLIGA O DANO DE CONTATO ---
        self.is_inofensivo = True 
        self.is_invulneravel = True

    def processar_salto(self, agora, delta_time):
        progresso = (agora - self.tempo_pulo) / self.duracao_pulo
        
        if progresso >= 1.0:
            # Lógica de Pouso
            self.estado_habilidade = 'idle'
            self.ultimo_pulo = agora
            self.cooldown_pulo = self.novo_cooldown(4000, 6000)
            self.wait = agora + 800 # Tempo de recuperação do impacto

            # --- LIGA O DANO DE CONTATO NOVAMENTE ---
            self.is_inofensivo = False 
            self.is_invulneravel = False
            
            # Dano no impacto
            ArtilhariaAviso(
                posicao=self.posicao, 
                grupos=(self.game.all_sprites,), 
                game=self.game,
                dono='BOSS',
                preset='tartarus_leap'
                )
            return

        # Movimento parabólico (interpolação)
        self.posicao = self.pulo_start_pos.lerp(self.pulo_target, progresso)
        
        # Efeito visual de subida (similar ao Hunter)
        altura = math.sin(progresso * math.pi) * 300
        self.rect.center = (round(self.posicao.x), round(self.posicao.y - altura))

    def iniciar_smash_energia(self, agora):
        self.estado_habilidade = 'energy_smash'
        self.velocidade = 0 # Fica parado enquanto bate o martelo no chão
        self.fase_smash = 0
        self.tempo_proximo_smash = agora + 1000 # 0.6s de atraso para o segundo golpe
        
    def processar_smash_energia(self, agora):
        if self.fase_smash == 0 and agora >= self.tempo_proximo_smash:
            self.fase_smash = 1
            self.tempo_proximo_smash = agora + 800 # 0.6s de atraso para a segunda onda
            
            # Dispara o ataque padrão
            purge = PurgeGrid(self.game, self, preset='tartarus_smash_1')
            purge.iniciar(agora)

        # 2. Acabou o delay da primeira onda: Dispara a SEGUNDA onda
        elif self.fase_smash == 1 and agora >= self.tempo_proximo_smash:
            self.fase_smash = 2
            self.tempo_proximo_smash = agora + 800 # Tempo de recuperação antes de andar de novo
            
            # Dispara o ataque invertido
            purge = PurgeGrid(self.game, self, preset='tartarus_smash_2')
            purge.iniciar(agora)
            
        # 3. Finaliza o ataque e volta ao normal (IDLE)
        elif self.fase_smash == 2 and agora >= self.tempo_proximo_smash:
            self.ultimo_smash = agora
            self.estado_habilidade = 'idle'
            self.cooldown_smash = self.novo_cooldown(8000, 12000)
            self.wait = agora + 500

    def iniciar_invocacao(self, agora):
        """Ativa o estado de invocação e imobiliza o boss."""
        self.estado_habilidade = 'summon_brutes'
        self.velocidade = 0  # Trava o movimento durante o rugido/canalização
        self.tempo_inicio_summon = agora

    def processar_invocacao(self, agora):
        """Aguarda 1 segundo canalizando e spawna os Brutes nas laterais se o mapa permitir."""
        # Checa se já passou 1 segundo de canalização
        if agora - self.tempo_inicio_summon >= self.duracao_summon:
            # Define os offsets (60 pixels para a direita e 60 para a esquerda)
            offsets = [pygame.math.Vector2(60, 0), pygame.math.Vector2(-60, 0)]
            
            for offset in offsets:
                pos_spawn = self.posicao + offset
                
                # Só spawna se a posição for válida (não estiver dentro de paredes)
                if self.verificar_posicao_valida(pos_spawn):
                    novo_brute = Brute(pos_spawn, game=self.game)

                    entity_manager.all_sprites.add(novo_brute)
                    entity_manager.inimigos_grupo.add(novo_brute)

            # Finaliza a habilidade e coloca o boss em recuperação
            self.ultimo_summon = agora
            self.estado_habilidade = 'idle'
            self.cooldown_invocacao = self.novo_cooldown(12000, 18000)
            self.wait = agora + 1200  # 1.2s parado se recuperando após o esforço de invocar
