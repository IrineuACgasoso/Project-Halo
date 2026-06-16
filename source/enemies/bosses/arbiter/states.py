import pygame

class ArbiterAI:
    def executar_estados(self, agora, delta_time, dist_sq):
        fase_invis = getattr(self, 'invis_phase', None)

        # 1. ATUALIZA A MÁQUINA DE INVISIBILIDADE DA CLASSE BASE
        if fase_invis is not None:
            self.atualizar_invisibilidade(delta_time * 1000)

        # --------------------------------------------------
        # TRAVAS DE DEPENDÊNCIA ABSOLUTA (RETURNS CRÍTICOS)
        # --------------------------------------------------

        # SE ESTIVER TRAVADO: Ativa o contra-ataque estático e ignora tudo abaixo
        if self.estado_habilidade == 'antistuck_combat':
            self.processar_antistuck_combat(agora, delta_time, fase_invis)
            return

        # SE ESTIVER ATIRANDO: Processa a rajada comum e impede outras ações
        if self.estado_habilidade == 'shooting':
            self.velocidade = self.velocidade_base * 0.4
            self.processar_tiro_carabina(agora, delta_time)
            return

        # SE ESTIVER INVOCANDO: Fica totalmente imóvel conjurando os aliados
        if self.estado_habilidade == 'summoning':
            self.velocidade = 0
            self.processar_invocacao(agora)
            return

        # SE ESTIVER NA SPRINT INVISÍVEL: Trava de Fade-In (Acelera correndo pro player)
        if fase_invis == 'fade_in':
            self.velocidade = self.velocidade_base * 4  
            self.velocidade_animacao = 80
            return

        # SE ESTIVER NAS FASES INICIAIS DA SPRINT INVISÍVEL (Fade-Out ou Hold)
        if fase_invis in ['fade_out', 'hold']:
            self.velocidade = self.velocidade_base * 4
            self.velocidade_animacao = 100
            self.checar_colisao_stealth()
            
            if fase_invis == 'hold' and not getattr(self, 'ja_teleportou', False):
                self.realizar_teleporte()
                self.ja_teleportou = True
            return

        # VERIFICAÇÃO DO TRAVAMENTO MECÂNICO (SÓ VALIDA SE ESTIVER EM IDLE)
        if self.checar_se_travou(agora, dist_sq):
            return  # Se travou, o gatilho mudou o estado para 'antistuck_combat' e abortamos o frame

        # --------------------------------------------------
        # PENSADOR (Estado IDLE limpo - Pronto para novas decisões)
        # --------------------------------------------------
        if self.estado_habilidade == 'idle':
            self.velocidade = self.velocidade_base
            self.velocidade_animacao = 200

            # Verifica se ele tem um tempo de exaustão/espera.
            if getattr(self, 'wait', 0) > 0:
                self.wait -= delta_time * 1000
                return
            
            # Decisão 1: Invocar Elites
            if agora - self.ultima_invocacao >= self.cooldown_invocacao:
                self.estado_habilidade = 'summoning'
                self.tempo_inicio_summon = agora
                return

            # Decisão 2: Sprint Invisível
            elif agora - self.ultima_invisibi >= self.cooldown_invisibilidade:
                self.processar_inicio_stealth(agora)
                return

            # Decisão 3: Carabina Burst Comum
            elif agora - self.ultima_carabina >= self.cooldown_carabin:
                self.estado_habilidade = 'shooting'
                self.carabina_restante = self.contagem_carabina
                self.ultima_carabina = agora
                return