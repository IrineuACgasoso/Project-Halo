class WardenAI:
    def executar_estados(self, agora, delta_time):
        """Gerencia os gatilhos de ataque do Warden baseados na Função."""
        
        # Despachante de estados contínuos (não precisam do 'idle')
        if self.estado_habilidade == 'tp_traveling':
            self.update_tp()
            return # Trava a IA até o TP terminar
        
        if getattr(self, 'estado_habilidade', 'idle') in ['idle', 'parado', 'reposicionando']:
            if self.estado_habilidade in ['parado', 'idle']:
                self.estado_habilidade = 'idle'
            
            # Repare que passei o delta_time para sua função!
            self.aplicar_comportamento_da_funcao(delta_time)
            
            # 2. Respeita o delay pós-ataque travando o movimento (sobrepõe a regra acima)
            if agora < getattr(self, 'wait', 0):
                self.velocidade = 0
                return
                
            distancia_jogador_sqr = self.posicao.distance_squared_to(self.jogador.posicao)
            
            # --- GATILHOS DO ATIRADOR ---
            if self.funcao_atual == 'ATIRADOR':
                # Gatilho 1: Defesa Pessoal (Inimigo muito perto!)
                if distancia_jogador_sqr < 90000 and agora - getattr(self, 'ultimo_tp', 0) >= getattr(self, 'cooldown_tp', 6000):
                    self.estado_habilidade = 'executando_tp'
                    return

                # Gatilho 2: Atirar (Agora com duas armas!)
                if self.estado_habilidade == 'idle':
                    # 1ª Prioridade: Laser Contínuo
                    if agora - getattr(self, 'ultimo_laser', 0) >= getattr(self, 'cooldown_laser', 8000):
                        self.estado_habilidade = 'laser_charge'
                        self.tempo_inicio_laser = agora
                        return
                        
                    # 2ª Prioridade: Heavy Rifle
                    elif agora - getattr(self, 'ultimo_heavy_rifle', 0) >= getattr(self, 'cooldown_heavy_rifle', 6000):
                        self.estado_habilidade = 'heavy_rifle'
                        self.start_heavy_rifle = agora
                        return
            
            # --- GATILHOS DO COMBATENTE / ASSASSINO ---
            elif self.funcao_atual in ['COMBATENTE', 'ASSASSINO']:
                # Gatilho 1: Defesa de Área (STOMP) - EXCLUSIVO DO COMBATENTE
                if self.funcao_atual == 'COMBATENTE':
                    # Distância <= 300px (300^2 = 90000)
                    if distancia_jogador_sqr <= 90000 and agora - getattr(self, 'ultimo_stomp', 0) >= getattr(self, 'cooldown_stomp', 7000):
                        self.iniciar_bruiser_leap(agora)
                        return
                    
                    if agora - getattr(self, 'ultimo_chop', 0) >= getattr(self, 'cooldown_chop', 5000):
                        if distancia_jogador_sqr <= 160000:
                            self.estado_habilidade = 'chop'
                            self.start_chop = agora
                            return
                        
                if self.funcao_atual == 'ASSASSINO':
                    # Só inicia o combo se o Purge Grid não estiver em cooldown
                    if agora - getattr(self, 'ultimo_purge', 0) >= getattr(self, 'cooldown_purge', 10000):
                        self.tp_raio_min = 250   # Aparece colado no player!
                        self.tp_raio_max = 350  
                        self.tp_prox_estado = 'purge_assassino' # Diz para o TP o que fazer quando acabar
                        self.estado_habilidade = 'executando_tp'
                        return

        # ==========================================
        # Despachante de Ataques
        # ==========================================
        if self.estado_habilidade == 'chop':
            self.executar_chop()
        elif self.estado_habilidade == 'heavy_rifle':
            self.executar_heavy_rifle()
        elif self.estado_habilidade in ['laser_charge', 'laser_firing']:
            self.executar_hardlight_laser(agora, delta_time)
        elif self.estado_habilidade == 'executando_tp':
            self.executar_tp()
        elif self.estado_habilidade == 'purge_assassino':
            self.executar_purge_assassino()