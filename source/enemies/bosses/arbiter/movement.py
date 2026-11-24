import random
import pygame
from .config import CFG


class ArbiterMovement:
    """Movimento tático. A percepção comum (contexto, mira antecipada) vem da BossBase.

    ATENÇÃO: este mixin precisa vir ANTES de BossBase na herança da classe (MRO)."""

    def perceber(self, agora, delta_time):
        super().perceber(agora, delta_time)
        if agora >= self._troca_lado_em:
            self._lado_strafe *= -1
            self._troca_lado_em = agora + random.randint(*CFG.strafe_troca_ms)

    # -------------------------------------------------------- comandos
    def _resetar_movimento(self):
        """Default de TODO frame: perseguir na velocidade da fase. Rotinas sobrescrevem."""
        self.velocidade = self.velocidade_base * self.fase_cfg.mult_velocidade
        self.animador.tocar('andar')
        self._dir_mov = None

    def _parar(self):
        self.velocidade = 0
        self.animador.tocar('parado')

    def _aproximar(self, fator=1.0):
        self._ir(self.dir_jogador(), fator)

    def _recuar(self, fator=0.9):
        self._ir(-self.dir_jogador(), fator)

    def _strafe(self, fator=0.7):
        """Circula o jogador; inverte o lado se for bater na parede."""
        to = self.dir_jogador()
        perp = pygame.math.Vector2(-to.y, to.x) * self._lado_strafe
        if (self._agora >= self._flip_valido_em
                and not self.verificar_posicao_valida(self.posicao + perp * 60)):
            self._lado_strafe *= -1
            self._flip_valido_em = self._agora + 400
            perp = -perp
        self._ir(perp, fator)

    def movimento_ocioso(self, agora):
        """Pastoreio: fecha distância pra espada quando ela está pronta; senão mantém a banda e circula."""
        dist = self.contexto.dist
        raio_lamina = self._raio_lamina()
        if agora + 1200 >= self.cd['lamina']:
            if dist > raio_lamina * 0.85:
                self._aproximar(1.0)
            else:
                self._strafe(0.6)
        elif dist > CFG.dist_max:
            self._aproximar(1.0)
        elif dist < CFG.dist_min:
            self._recuar(0.9)
        else:
            self._strafe(0.75)
