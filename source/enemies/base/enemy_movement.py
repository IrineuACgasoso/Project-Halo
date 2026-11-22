class EnemyMovement:
    def mover(self, delta_time, direcao=None):

        if direcao is None:
            direcao = self.jogador.posicao - self.posicao

        if direcao.length() > 0:
            direcao.normalize_ip()

        self.posicao += direcao * self.velocidade_atual() * delta_time

    def velocidade_atual(self):
        """A velocidade com buffs e lentidão (sistema de status). Sem efeitos, igual a `velocidade`."""
        return self.velocidade * self.status.mult_velocidade