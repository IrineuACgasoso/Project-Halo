import pygame
from source.systems.entitymanager import entity_manager


class TartarusAI:
    def executar_estados(self, agora, delta_time):
        # TRAVA GLOBAL: Se o boss está no período de espera, ele não decide nada novo
        if agora < self.wait:
            return

        # === GATILHOS DE HABILIDADE ===
        if self.estado_habilidade == 'idle':
            self.velocidade_base = self.velocidade_anterior
            distancia_sq = self.posicao.distance_squared_to(self.jogador.posicao)

            # PRIORIDADE 0: Verificação de Anti-Stuck (Se ativou, encerra o frame)
            if self.checar_se_travou(agora, distancia_sq):
                return

            # Só invoca se o cooldown estiver pronto E se houver menos de 4 inimigos na tela
            inimigos_vivos = len(entity_manager.inimigos_grupo)
            if (agora - getattr(self, 'ultimo_summon', 0) >= self.cooldown_summon) and inimigos_vivos < 4:
                self.iniciar_invocacao(agora)
                return
            
            # Prioridade 1: Salto padrão se estiver muito longe
            elif distancia_sq > 640000 and (agora - getattr(self, 'ultimo_pulo', 0) >= self.cooldown_pulo):
                self.iniciar_pulo(agora)
                
            # Prioridade 2: Hammer Run se estiver perto
            elif distancia_sq < 490000 and (agora - getattr(self, 'ultimo_hammer', 0) >= self.cooldown_hammer):
                self.estado_habilidade = 'hammer_run'
                self.hammer_target = self.jogador.posicao.copy() 
                self.hammer_start_time = agora
                self.velocidade = self.velocidade_anterior * 4.0

                vetor = self.hammer_target - self.posicao
                self.direcao = vetor.normalize() if vetor.length() > 0 else pygame.math.Vector2(1, 0)

            # Prioridade 3: Energy Smash (Alcance médio)
            elif 160000 < distancia_sq < 490000 and (agora - getattr(self, 'ultimo_smash', 0) >= self.cooldown_smash):
                self.iniciar_smash_energia(agora)

