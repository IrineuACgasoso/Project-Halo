class EnemyScaling:
    def aplicar_dificuldade(self):
        # 1. Calcula os multiplicadores com base no nível atual do player
        mult_vida = 1 + self.jogador.contador_niveis / 10
        mult_dano = 1 + self.jogador.contador_niveis / 10
        mult_vel  = 1 + self.jogador.contador_niveis / 100

        # Aplica e sela os novos valores Máximos e de Base Real do Inimigo
        self.vida_maxima = self.vida_base * mult_vida
        self.vida_base = self.vida_maxima
        self.vida = self.vida_maxima

        # Faz o mesmo com o dano e velocidade para evitar comportamentos anômalos
        self.dano_base = self.dano_base * mult_dano
        self.dano = self.dano_base

        self.velocidade_base = self.velocidade_base * mult_vel
        self.velocidade = self.velocidade_base
