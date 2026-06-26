import math
import random
import pygame


class AssassinBehavior:
    def _comportamento_assassino(self, delta_time, agora):
        """Kiting e Avanço Feroz."""
        self.velocidade = 0

        if self.estado_habilidade == 'reposicionando':
            self.processar_reposicionamento(delta_time)
            return

        if self.estado_habilidade == 'idle':
            distancia_jogador_sq = self.posicao.distance_squared_to(self.jogador.posicao)
            buff_ativo = getattr(self, 'tempo_fim_buff_velocidade', 0) > agora

            if buff_ativo:
                direcao_avanco = self.jogador.posicao - self.posicao
                if direcao_avanco.length_squared() > 0:
                    direcao_avanco.normalize_ip()
                    self.posicao += direcao_avanco * 280 * delta_time
                    self.rect.center = (round(self.posicao.x), round(self.posicao.y))
            else:
                if distancia_jogador_sq < 490000:
                    direcao_fuga = self.posicao - self.jogador.posicao
                    if direcao_fuga.length_squared() > 0:
                        direcao_fuga.normalize_ip()
                        self.posicao += direcao_fuga * 140 * delta_time
                        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
                else:
                    if not hasattr(self, 'alvo_reposicionamento') or self.alvo_reposicionamento is None:
                        if random.random() < 0.01:
                            self._calcular_ponto_strafe()

    def _calcular_ponto_strafe(self):
        """Gera um ponto lateral aleatório para simular movimentação inteligente."""
        self.estado_habilidade = 'reposicionando'
        vetor = self.jogador.posicao - self.posicao

        angulo_base = math.atan2(vetor.y, vetor.x) if vetor.length_squared() > 0 else 0
        desvio = math.radians(random.choice([random.uniform(-70, -40), random.uniform(40, 70)]))
        dist_repo = random.uniform(150, 300)

        novo_x = self.posicao.x + math.cos(angulo_base + desvio) * dist_repo
        novo_y = self.posicao.y + math.sin(angulo_base + desvio) * dist_repo
        self.alvo_reposicionamento = pygame.math.Vector2(novo_x, novo_y)