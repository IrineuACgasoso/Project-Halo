import pygame

class ScarabAI:
    def checar_fases(self):
        if not self.fase_desestabilizado and self.vida < self.vida_base * 0.6:
            self.fase_desestabilizado = True
            self.sprites = self.get_sprites('damaged')
            self.cooldown_laser = self.novo_cooldown(9000, 11000)
            
        if not self.fase_critica and self.vida < self.vida_base * 0.4:
            self.fase_critica = True
            self.sprites = self.get_sprites('broken')
            self.cooldown_plasma = self.novo_cooldown(2000, 5000)
            self.cooldown_laser = self.novo_cooldown(7000, 9000)
            self.velocidade *= 2
            self.velocidade_animacao /= 2
            self.delay_entre_tiros /= 1.5
            self.intensidade_shake *= 3

    def executar_ia(self, agora, delta_time):
        # 1. ESTADO DE ATORDOAMENTO (Prioridade Máxima)
        if getattr(self, 'estado_combate', '') == 'STUNNED':
            if agora - getattr(self, 'tempo_inicio_stun', 0) >= getattr(self, 'duracao_stun', 6000):
                # Fim do Stun: Reseta escudo e volta ao combate
                self.estado_combate = 'MOVENDO'
                self.adicionar_escudo(self.escudo_maximo)
                
                # Reseta cooldowns para não dar um "Insta-Kill" logo ao acordar
                self.ultimo_laser = agora
                self.ultimo_tiro_plasma = agora
            return  # Ignora o resto da IA enquanto estiver atordoado!

        # 2. ESTADOS NORMAIS
        self.checar_fases()
        self.logica_laser(agora, delta_time)
        self.gerenciar_rajada(agora)