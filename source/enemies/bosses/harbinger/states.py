# source/enemies/bosses/harbinger/states.py
import pygame
import random

class HarbingerAI:
    def executar_ia_harbinger(self, agora, delta_time, paredes=None):
        """Processa a máquina de estados tática de evasão e assalto usando o suporte nativo."""
        direcao = (self.jogador.posicao - self.posicao)

        # 1. Atualiza o motor nativo de camuflagem (converte delta_time de segundos para ms)
        self.atualizar_invisibilidade(delta_time * 1000)

        # 2. Gerenciamento do estado de Teleporte e Invulnerabilidade Nativa
        if self.teleportando:
            if self.invis_phase is not None:
                return  # Trava ações e mantém a invulnerabilidade enquanto o ciclo nativo rodar
            else:
                # O ciclo de fade_in terminou nativamente (self.invis_phase virou None)
                self.teleportando = False
                self.is_invulneravel = False  # Janela de vulnerabilidade reaberta!
                self.hitbox.center = self.rect.center

        # 3. IA de Posicionamento e Zoneamento por distância
        if agora - self.ultimo_tp > self.tp_cooldown:
            # Se o jogador fugir demais, ela encurta a distância agressivamente
            if direcao.length() > 1170:
                self.teleporte(200, 250)
                self.ultimo_tp = agora
                return
            # Se o jogador encurralar ela em combate corpo a corpo, ela recua
            elif direcao.length() < 300:
                self.teleporte(500, 550)
                self.ultimo_tp = agora
                return

        # 4. Movimentação de perseguição flutuante padrão
        if direcao.length() > 0:
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * delta_time
            if paredes:
                self.aplicar_colisao_mapa(paredes)
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        # 5. Gatilho e Sequenciador de Disparos da Carabina
        if agora - self.ultima_carabina >= self.cooldown_carabin:
            self.carabina_restante = self.contagem_carabina
            novo_cooldown_carabina = [6000, 8000, 10000, 11000]
            self.cooldown_carabin = random.choice(novo_cooldown_carabina)
            self.ultima_carabina = agora
            
        if self.carabina_restante > 0:
            self.cronometro_carabina += delta_time * 1000
            if self.cronometro_carabina >= self.intervalo_carabina:
                self.cronometro_carabina = 0
                self.carabina_restante -= 1
                self.carabin()

        if agora - getattr(self, 'ultimo_emp', 0) >= getattr(self, 'cooldown_emp', 5000):
            # A IA decide soltar se o jogador estiver no campo de visão (raio aceitável) 
            # com uma pequena chance por frame para não ser 100% previsível
            if direcao.length() < 950 and random.random() < 0.015:
                self.executar_onda_emp()
                return

        # 6. Flip visual de orientação da sprite baseado no alvo
        if direcao.x < 0:
            self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'