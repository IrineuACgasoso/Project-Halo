

class EnemyEffects:
    def trigger_flash(self, duracao=100, bonus_alpha=120):
        """
        Revela parcialmente o inimigo por um curto período.
        """
        if not self.flash:
            return

        self.flash_timer = duracao
        self.flash_alpha_bonus = bonus_alpha