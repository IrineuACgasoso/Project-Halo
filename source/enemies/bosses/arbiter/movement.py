import math
import random
import pygame
from .config import CFG

V2 = pygame.math.Vector2


class ArbiterMovement:
    """Movimento tatico + percepcao do jogador.

    ATENCAO: este mixin precisa vir ANTES de BaseEnemy na heranca da classe,
    senao o `mover` de EnemyMovement ganha na MRO e o override nunca roda."""

    # ------------------------------------------------------------ override
    def mover(self, delta_time, direcao=None):
        if direcao is None and self._dir_mov is not None:
            direcao = self._dir_mov.copy()          # base faz normalize_ip: nao mutar o nosso
        super().mover(delta_time, direcao)

    # ---------------------------------------------------------- percepcao
    def _dir_jogador(self):
        d = self.jogador.posicao - self.posicao
        return d.normalize() if d.length_squared() > 1e-6 else V2(1, 0)

    def _dist_jogador(self):
        return self.posicao.distance_to(self.jogador.posicao)

    def _atualizar_percepcao(self, dt, agora):
        # caminho efetivamente percorrido (pos-colisao) — base do detector de travamento
        if self.rotina is None:
            self._caminho_livre += self.posicao.distance_to(self._pos_ant_frame)
        self._pos_ant_frame = V2(self.posicao)

        pos = self.jogador.posicao
        if dt > 1e-4:
            v = (pos - self._pos_jogador_ant) / dt
            if v.length_squared() < 4000 ** 2:      # descarta teleporte/dash absurdo
                self._vel_jogador = self._vel_jogador.lerp(v, 0.25)
        self._pos_jogador_ant = V2(pos)

        if agora >= self._troca_lado_em:
            self._lado_strafe *= -1
            self._troca_lado_em = agora + random.randint(*CFG.strafe_troca_ms)

    def _ponto_antecipado(self, vel_projetil, fator, max_desloc=250):
        """Onde o jogador estara quando o projetil chegar (com `fator` de confianca)."""
        t = self._dist_jogador() / max(vel_projetil, 1)
        desloc = self._vel_jogador * t * fator
        if desloc.length() > max_desloc:
            desloc.scale_to_length(max_desloc)
        return self.jogador.posicao + desloc

    def _direcao_antecipada(self, vel_projetil, fator):
        d = self._ponto_antecipado(vel_projetil, fator) - self.posicao
        return d.normalize() if d.length_squared() > 1e-6 else self._dir_jogador()

    # -------------------------------------------------------- comandos
    def _resetar_movimento(self):
        """Default de TODO frame: perseguir na velocidade da fase. Rotinas sobrescrevem."""
        self.velocidade = self.velocidade_base * self.fase_cfg.mult_velocidade
        self.velocidade_animacao = 200
        self._dir_mov = None

    def _ir(self, direcao, fator=1.0):
        self._dir_mov = direcao
        self.velocidade = self.velocidade_base * self.fase_cfg.mult_velocidade * fator

    def _parar(self):
        self.velocidade = 0
        self.velocidade_animacao = 300      # 0 aqui = animar a cada frame, nao congelar

    def _aproximar(self, fator=1.0):
        self._ir(self._dir_jogador(), fator)

    def _recuar(self, fator=0.9):
        self._ir(-self._dir_jogador(), fator)

    def _strafe(self, fator=0.7):
        """Circula o jogador; inverte o lado se for bater na parede."""
        to = self._dir_jogador()
        perp = V2(-to.y, to.x) * self._lado_strafe
        if (self._agora >= self._flip_valido_em
                and not self.verificar_posicao_valida(self.posicao + perp * 60)):
            self._lado_strafe *= -1
            self._flip_valido_em = self._agora + 400
            perp = -perp
        self._ir(perp, fator)

    def _mov_idle(self, dist, agora):
        """Pastoreio: fecha distancia pra espada quando ela esta pronta; senao mantem a banda e circula."""
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
