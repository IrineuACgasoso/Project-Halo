class EnemyMovement:
    def mover(self, delta_time, direcao=None):

        if direcao is None:
            direcao = self.jogador.posicao - self.posicao

        if direcao.length() > 0:
            direcao.normalize_ip()

        self.posicao += direcao * self.velocidade * delta_time