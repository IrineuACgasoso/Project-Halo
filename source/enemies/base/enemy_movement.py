class EnemyMovement:
    def mover(self, delta_time, direcao=None):

        if direcao is None:
            direcao = self.jogador.posicao - self.posicao

        if direcao.length() > 0:
            direcao.normalize_ip()

        self.posicao += direcao * self.velocidade_atual() * delta_time

    def deslocar(self, vetor, paredes):
        """Deslocamento forçado (systems/empurrao), sem atravessar paredes."""
        self.posicao += vetor
        if paredes:
            self.aplicar_colisao_mapa(paredes)
        self.sync_rect()

    def velocidade_atual(self):
        """A velocidade com buffs e lentidão (sistema de status). Sem efeitos, igual a `velocidade`."""
        return self.velocidade * self.status.mult_velocidade