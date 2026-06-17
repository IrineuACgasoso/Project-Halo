from source.systems.entitymanager import entity_manager

class GravemindAI:
    def executar_estados(self, agora, delta_time):
        # 1. Trava de Animação de Respawn
        if self.is_animating_respawn:
            self.atualizar_animacao_respawn(delta_time, agora)
            return

        # 2. Ativação Única do Miasma (Exclusivo da Forma Final)
        if getattr(self, 'is_final_form', False) and not getattr(self, 'gas_invocado', False):
            from .vfx import MiasmaGas
            MiasmaGas(self.posicao, self.raio_safezone, self.game, (entity_manager.all_sprites,), self)
            self.gas_invocado = True

        # === 3. SELEÇÃO DE HABILIDADES (ESTADO IDLE) ===
        if self.estado_habilidade == 'idle':
            # TRAVA GLOBAL: Respeita o tempo de respiro entre ataques
            if agora < self.wait:
                return
            
            # Determina quais ataques estão disponíveis para este contexto
            self._processar_escolha_de_ataque(agora)

        # === 4. RESOLUÇÃO/EXECUÇÃO DAS HABILIDADES ===
        if self.estado_habilidade == 'acid': 
            self.acid_breath_attack(agora)
        elif self.estado_habilidade == 'infection': 
            self.spawn_infection_attack(agora)
        elif self.estado_habilidade == 'tentacles': 
            self.tentacles_attack(agora)
        elif self.estado_habilidade == 'infection_forms': 
            self.spawn_infection_forms_attack(agora)  # <-- Nova rota da Fase 2
        elif self.estado_habilidade == 'acid_rain': 
            self.acid_rain_attack(agora)

    def _processar_escolha_de_ataque(self, agora):
        """Mapeia o perfil de habilidades com base na variante e na vida atual."""
        
        # --- PERFIL PROTO GRAVEMIND ---
        if self.variante == 'proto':
            if self.is_minion:
                # Proto (Clone): Apenas Baforada e Infeção
                if agora - self.ultima_baforada >= self.cooldown_acido:
                    self.estado_habilidade = 'acid'
                    self.tiros_restantes = self.tiros_burst
                elif agora - self.ultima_infeccao >= self.cooldown_infeccao:
                    self.estado_habilidade = 'infection'
                    self.spawns_restantes = 5
            else:
                # Proto (Não Clone): Baforada, Infecção e Tentáculos
                if agora - self.ultima_baforada >= self.cooldown_acido:
                    self.estado_habilidade = 'acid'
                    self.tiros_restantes = self.tiros_burst
                elif agora - self.ultima_infeccao >= self.cooldown_infeccao:
                    self.estado_habilidade = 'infection'
                    self.spawns_restantes = 5
                elif agora - getattr(self, 'ultimos_tentaculos', 0) >= getattr(self, 'cooldown_tentaculos', 0):
                    self.estado_habilidade = 'tentacles'

        # --- PERFIL GRAVEMIND FINAL (SISTEMA DE FASES) ---
        elif self.variante == 'final':
            porcentagem_vida = (self.vida / self.vida_base) * 100

            # FASE 1: Vida acima de 80% (Acid Breath, Infection)
            if porcentagem_vida > 80:
                if agora - self.ultima_baforada >= self.cooldown_acido:
                    self.estado_habilidade = 'acid'
                    self.tiros_restantes = self.tiros_burst
                elif agora - self.ultima_infeccao >= self.cooldown_infeccao:
                    self.estado_habilidade = 'infection'
                    self.spawns_restantes = 15

            # FASE 2: Vida entre 50% e 80% (Infection Forms, Tentáculos)
            elif 50 <= porcentagem_vida <= 80:
                if agora - getattr(self, 'ultima_infeccao_forms', 0) >= getattr(self, 'cooldown_infeccao_forms', 0):
                    self.estado_habilidade = 'infection_forms'
                    self.forms_restantes = 10  # Controlado no script de ataque externo
                elif agora - getattr(self, 'ultimos_tentaculos', 0) >= getattr(self, 'cooldown_tentaculos', 0):
                    self.estado_habilidade = 'tentacles'

            # FASE 3: Vida abaixo de 50% (Acid Rain)
            elif porcentagem_vida < 50:
                if agora - getattr(self, 'ultima_chuva', 0) >= getattr(self, 'cooldown_chuva', 0):
                    self.estado_habilidade = 'acid_rain'
                    self.morteiros_restantes = 40
                    self.ultimo_morteiro_tick = agora

