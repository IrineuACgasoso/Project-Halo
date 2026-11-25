import random

import pygame

from source.feats.skills.dash import Dash
from .config import CFG

V2 = pygame.math.Vector2


class ArbiterMovement:
    """Movimento tático. A percepção comum (contexto, mira antecipada) vem da BossBase.

    ATENÇÃO: este mixin precisa vir ANTES de BossBase na herança da classe (MRO)."""

    # -------------------------------------------------------- comandos
    def _resetar_movimento(self):
        """Default de TODO frame: perseguir na velocidade da fase, olhando para o jogador. Rotinas sobrescrevem."""
        self._ir(None)
        self._olhar_x = None
        self.animador.tocar('andar')

    def orientar(self):
        if self._olhar_x is not None:
            self.set_sprite_direction(self._olhar_x)
        else:
            super().orientar()

    def _parar(self, olhar_x=None):
        self.velocidade = 0
        self._olhar_x = olhar_x
        self.animador.tocar('parado')

    def _aproximar(self, fator=1.0):
        self._ir(self.dir_jogador(), fator)

    def _recuar(self, fator=0.9):
        """Afasta-se do jogador; com parede atrás, circula."""
        para_tras = -self.dir_jogador()
        if self.verificar_posicao_valida(self.posicao + para_tras * 70):
            self._ir(para_tras, fator)
        else:
            self._strafe(fator)

    def _strafe(self, fator=0.7):
        """Circula o jogador; inverte o lado se for bater na parede."""
        to = self.dir_jogador()
        perp = V2(-to.y, to.x) * self._lado_strafe
        if (self._agora >= self._flip_valido_em
                and not self.verificar_posicao_valida(self.posicao + perp * 60)):
            self._lado_strafe *= -1
            self._flip_valido_em = self._agora + 400
            perp = -perp
        self._ir(perp, fator)

    def _dash(self, preset, alvo=None):
        """Sub-rotina: investida até `alvo` (padrão: onde o jogador está agora). Devolve a direção.
        Inofensivo no caminho: quem fere é a espada que vem junto ou no fim (o corpo de 250 px
        encostaria em quem desviou por pouco)."""
        dash = Dash(self, self.jogador.posicao if alvo is None else alvo, preset=preset)
        antes, self.is_inofensivo = self.is_inofensivo, True
        try:
            while not dash.atualizar(self._dt, self._paredes):
                self.velocidade = 0
                self._olhar_x = dash.direcao.x
                self.animador.tocar('investida')
                yield
        finally:
            self.is_inofensivo = antes
        return dash.direcao

    # -------------------------------------------------------- ocioso
    def movimento_ocioso(self, agora):
        """Recuando: abre distância. Avançando: cola para a espada. Neutro: mantém a faixa, que se
        aproxima quanto menos vida o jogador tem, e fecha para a espada quando ela está pronta."""
        dist = self.contexto.dist
        raio_lamina = self._raio_lamina()
        if self.postura == 'recuo':
            if dist < CFG.dist_recuo:
                self._recuar(1.1)
            else:
                self._strafe(0.7)
            return
        if self.postura == 'avanco' or agora + 1200 >= self.cd['lamina']:
            if dist > raio_lamina * 0.85:
                self._aproximar(1.1 if self.postura == 'avanco' else 1.0)
            else:
                self._strafe(0.6)
            return
        aproximar = CFG.aproximacao_jogador_fraco * self.agressividade
        if dist > CFG.dist_max - aproximar:
            self._aproximar(1.0)
        elif dist < CFG.dist_min - aproximar:
            self._recuar(0.9)
        else:
            self._strafe(0.75)

    def _trocar_lado_strafe(self, agora):
        if agora >= self._troca_lado_em:
            self._lado_strafe *= -1
            self._troca_lado_em = agora + random.randint(*CFG.strafe_troca_ms)
