class KnightAI:
    def executar_estados(self, agora):
        """Gerencia os gatilhos e transições de estado do Knight."""
        
        if self.estado_habilidade == 'idle':
            
            # Respeita a trava global pós-ataques
            if agora < getattr(self, 'wait', 0):
                self.velocidade = self.velocidade_base
                return
                
            self.velocidade = self.velocidade_base

            # Se a trava está desativada (False), significa que um Watcher foi invocado no passado.
            if not self.pode_checar_summon:
                if self.watcher_ativo is None or not self.watcher_ativo.alive():
                    self.ultimo_summon = agora       # Inicia o cooldown DE FATO a partir da morte
                    self.pode_checar_summon = True   # Libera para analisar a Prioridade 0 novamente

            # Prioridade 0: Invocação do Watcher com trava
            if self.pode_checar_summon and (agora - self.ultimo_summon >= self.cooldown_summon):
                self.pode_checar_summon = False  # Tranca imediatamente para não reentrar no loop
                self.executar_summon()           # Executa o estado/método de invocação

            # Prioridade 1: Ativar Laser
            elif agora - getattr(self, 'ultimo_laser', 0) >= getattr(self, 'cooldown_laser', 7000):
                self.estado_habilidade = 'laser'
                self.start_laser = agora
            
            # Prioridade 2: Ativar Cleave (Ataque em Cone) ---
            elif agora - getattr(self, 'ultimo_cleave', 0) >= getattr(self, 'cooldown_cleave', 8000) and self.posicao.distance_squared_to(self.jogador.posicao) <= 90000:
                self.estado_habilidade = 'cleave'
                self.start_cleave = agora

            # Prioridade 3: Ativar Investida (Run)
            elif agora - getattr(self, 'ultima_run', 0) >= getattr(self, 'cooldown_run', 10000):
                self.estado_habilidade = 'run'
                
            # Prioridade 4: Ativar Teleporte (TP)
            elif agora - getattr(self, 'ultimo_tp', 0) >= getattr(self, 'cooldown_tp', 5000):
                self.executar_tp()