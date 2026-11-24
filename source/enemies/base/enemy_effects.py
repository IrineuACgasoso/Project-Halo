

class EnemyEffects:
    def trigger_flash(self, duracao=100, bonus_alpha=120):
        """
        Revela parcialmente o inimigo camuflado por um curto período (visível, não faz nada).
        """
        if self.invisibilidade is not None:
            self.invisibilidade.revelar(duracao, bonus_alpha)