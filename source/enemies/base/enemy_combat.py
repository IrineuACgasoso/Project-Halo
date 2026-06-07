import pygame
import random

from source.feats.items import Items

class EnemyCombat:
    def adicionar_escudo(self, valor):
        """Define o valor do escudo do inimigo."""
        self.escudo_maximo = valor
        self.escudo_atual = valor

    def calcular_direcao_tiro(self, spread_range=0):
        """
        Calcula a direção para o jogador com spread opcional.
        spread_range: 0 para tiro preciso, ou um valor (ex: 0.05) para espalhamento.
        """
        direcao = self.jogador.posicao - self.posicao
        if direcao.length_squared() > 0:
            direcao = direcao.normalize()
        else:
            direcao = pygame.math.Vector2(1, 0)

        if spread_range > 0:
            spread = pygame.math.Vector2(
                random.uniform(-spread_range, spread_range),
                random.uniform(-spread_range, spread_range)
            )
            direcao = (direcao + spread)
            if direcao.length() > 0:
                direcao = direcao.normalize()
                
        return direcao

    def receber_dano(self, quantidade):
        """Gerencia o dano, retirando do escudo primeiro e o restante da vida."""
        if self.escudo_atual > 0:
            self.escudo_atual = self.escudo_atual - quantidade
            if self.escudo_atual < 0:
                # Se o dano for maior que o escudo, o que sobra vai para a vida
                dano_restante = abs(self.escudo_atual)
                self.escudo_atual = 0
                self.vida = max(0, self.vida - dano_restante)
        else:
            # Se não tem escudo, toma dano direto na vida
            self.vida = max(0, self.vida - quantidade)

    def novo_cooldown(self, minimal, maximum):
        updated_cooldown = random.randint(minimal, maximum)
        return updated_cooldown

    def morrer(self, grupos = None):
        Items.spawn_drop(self.posicao, grupos, 'exp_shard', 1, 100)
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 1, 2)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 1)
        self.kill()

    def iniciar_invisibilidade(
        self,
        alpha_alvo,
        fade_out,
        fade_in,
        duracao,
        flashing=False
    ):
        self.invisivel = True
        self.invis_phase = "fade_out"

        self.invis_alpha_base = 255
        self.invis_alpha_target = max(0, min(255, alpha_alvo))

        self.invis_fade_out = fade_out
        self.invis_fade_in = fade_in
        self.invis_duracao = duracao

        self.invis_timer = 0
        self.invis_phase_timer = 0

        # Flashing
        self.flash = flashing
        self.flash_timer = 0
        self.flash_alpha_bonus = 0

        self._aplicar_alpha(self.invis_alpha_base)

    def atualizar_invisibilidade(self, dt):
        """
        dt em milissegundos
        """

        if not self.invisivel:
            return

        self.invis_timer += dt
        self.invis_phase_timer += dt
        alpha_final = self.invis_alpha_base

        # ============================================
        # Fade Out
        # ============================================
        if self.invis_phase == "fade_out":
            t = min(1.0, self.invis_phase_timer / self.invis_fade_out)

            alpha_final = (
                self.invis_alpha_base +
                (self.invis_alpha_target - self.invis_alpha_base) * t
            )
            if t >= 1.0:
                self.invis_phase = "hold"
                self.invis_phase_timer = 0

        # ============================================
        # Hold
        # ============================================
        elif self.invis_phase == "hold":
            alpha_final = self.invis_alpha_target

            if self.invis_timer >= (
                self.invis_duracao - self.invis_fade_in
            ):
                self.invis_phase = "fade_in"
                self.invis_phase_timer = 0

        # ============================================
        # Fade In
        # ============================================
        elif self.invis_phase == "fade_in":
            t = min(1.0, self.invis_phase_timer / self.invis_fade_in)

            alpha_final = (
                self.invis_alpha_target +
                (self.invis_alpha_base - self.invis_alpha_target) * t
            )

            if t >= 1.0:
                self.invisivel = False
                self.invis_phase = None

                alpha_final = self.invis_alpha_base

        # ============================================
        # Flash
        # ============================================
        if self.flash_timer > 0:
            self.flash_timer -= dt
            alpha_final += self.flash_alpha_bonus

        # Clamp final
        alpha_final = max(0, min(255, alpha_final))

        self._aplicar_alpha(alpha_final)

    def _aplicar_alpha(self, alpha):

        self.alpha_atual = int(alpha)

        if hasattr(self, "image"):
            self.image.set_alpha(self.alpha_atual)