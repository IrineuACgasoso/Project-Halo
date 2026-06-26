import pygame


class SniperBehavior:
    def _comportamento_atirador(self, delta_time):
        """Fuga tática: mantém distância e cede espaço se for o mais próximo."""
        self.velocidade = 0

        if self.estado_habilidade == 'reposicionando':
            self.processar_reposicionamento(delta_time)
        elif self.estado_habilidade == 'idle':
            if self.sou_o_mais_proximo():
                direcao_fuga = self.posicao - self.jogador.posicao
                if direcao_fuga.length_squared() > 0:
                    direcao_fuga.normalize_ip()
                    self.posicao += direcao_fuga * 100 * delta_time
                    self.rect.center = (round(self.posicao.x), round(self.posicao.y))