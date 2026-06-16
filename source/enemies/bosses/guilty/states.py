import pygame
from source.feats.auras import EnergyAura

class GuiltyAI:
    def verificar_fases(self, agora):
        # 1. Gatilho para iniciar a Transição (Apenas uma vez)
        if self.estado_fase == 'FASE1' and self.vida <= self.vida_base * 0.999999:
            self.iniciar_transicao()

        # 2. Monitoramento durante a Transição
        if self.estado_fase == 'TRANSICAO':
            # Limpa terminais que já foram destruídos do array
            self.terminais = [t for t in self.terminais if t.alive()]
            
            # Gatilho do RAGE: Se todos morreram, desperta a Fase 2!
            if len(self.terminais) == 0 and not self.enrage:
                self.rage(agora)

    def iniciar_transicao(self):
        """Prepara a arena e trava o boss no centro"""
        self.estado_fase = 'TRANSICAO'
        self.imune = True
        self.estado_habilidade = 'manutencao'
        self.velocidade = 0
        
        EnergyAura(
            owner=self, 
            raio=160, 
            dano_contato=15, 
            game=self.game, 
            cor_base=(0, 150, 255),  
            impenetravel=True        # Mantém a parede física (empurra o jogador)
        )
        
        from .terminal import ForerunnerTerminal
        from source.systems.entitymanager import entity_manager
        
        posicoes_terminais = [
            self.posicao + pygame.math.Vector2(-250, -200),
            self.posicao + pygame.math.Vector2(250, -200),
            self.posicao + pygame.math.Vector2(0, 250)
        ]

        self.terminais = []
        for pos in posicoes_terminais:
            novo_terminal = ForerunnerTerminal(pos, self.game, self)
            entity_manager.all_sprites.add(novo_terminal)
            entity_manager.inimigos_grupo.add(novo_terminal)
            self.terminais.append(novo_terminal)

    def executar_estados(self, agora, delta_time):
        self.verificar_fases(agora)

        # Na transição, ele não ataca, apenas assiste os terminais
        if self.estado_fase == 'TRANSICAO':
            return

        # === MÁQUINA DE ESTADOS DO COMBATE ===
        if self.estado_habilidade == 'idle':
            self.velocidade = self.velocidade_anterior

            # TRAVA GLOBAL: Se o boss ainda está no período de espera, ele apenas flutua e não decide nada novo
            if agora < self.wait:
                return

            distancia_sq = self.posicao.distance_squared_to(self.jogador.posicao)
            
            # 1. Habilidade Suprema: Purga (Bullet Hell - Fase 2)
            if self.estado_fase == 'RAGE_F2':
                purga_rodando = self.ataque_purga is not None and self.ataque_purga.alive()
                
                if not purga_rodando and (agora - getattr(self, 'ultimo_purge', 0) >= self.purge_cooldown):
                    self.purge(agora)
                    # Dá 2 segundos de respiro pro jogador lidar SÓ com a parede antes do boss atirar
                    self.wait = agora + 2000 
                    return # Impede que a checagem desça e dispare um laser no mesmo frame!

            # 2. Prioridade de Ataques Normais
            if agora - getattr(self, 'ultimo_laser', 0) >= self.cooldown_laser:
                self.estado_habilidade = 'laser_charge'
                self.tempo_inicio_laser = agora
                self.velocidade = 0 
                # (O reset do self.wait deve acontecer lá no arquivo onde o ataque finaliza)
                
            elif agora - getattr(self, 'ultima_invocacao', 0) >= self.cooldown_invocacao:
                self.estado_habilidade = 'sentinel'
                self.start_sentinel = agora
                self.velocidade = 0
                
            elif distancia_sq > 810000 and (agora - getattr(self, 'ultimo_tp', 0) >= getattr(self, 'cooldown_tp', 0)):
                self.estado_habilidade = 'teleporte'
                self.velocidade = 0

        # === RESOLUÇÃO DO ESTADO ATUAL ===
        if self.estado_habilidade in ['laser_charge', 'laser_firing']:
            self.logica_laser_rastreavel(agora, delta_time)
        elif self.estado_habilidade == 'sentinel':
            self.invocar_sentinelas(de_elite=(self.estado_fase == 'RAGE_F2'))
        elif self.estado_habilidade == 'teleporte':
            self.teleporte()