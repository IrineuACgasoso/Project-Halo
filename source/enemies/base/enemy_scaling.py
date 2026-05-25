class EnemyScaling:
    def aplicar_dificuldade(self):
        mult_vida = 1 + self.jogador.contador_niveis / 10
        mult_dano = 1 + self.jogador.contador_niveis / 10
        mult_vel  = 1 + self.jogador.contador_niveis / 100

        self.vida_maxima = self.vida_base * mult_vida
        self.vida = self.vida_maxima

        self.dano = self.dano_base * mult_dano
        self.velocidade = self.velocidade_base * mult_vel
