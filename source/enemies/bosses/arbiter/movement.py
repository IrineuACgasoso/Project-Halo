import math
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
        """Afasta-se do jogador pelo melhor rumo com chão (`_rumo_de_recuo`); encurralado, circula."""
        rumo = self._rumo_de_recuo()
        if rumo is not None:
            self._ir(rumo, fator)
        else:
            self._strafe(fator)

    def _rumo_de_recuo(self):
        """Rumo do recuo, guardado por `recuo_rumo_ms` (sem tremer a cada frame): entre os ângulos do
        leque em volta do "para trás", o que tem chão a `recuo_sonda` px e mais se afasta do jogador,
        puxado para a escolta viva (os Elites cobrem o recuo). None: encurralado."""
        agora = self._agora
        rumo = self._rumo_recuo
        if (rumo is not None and agora < self._rumo_recuo_ate
                and self.verificar_posicao_valida(self.posicao + rumo * 70)):
            return rumo
        para_tras = -self.dir_jogador()
        escolta = self._direcao_da_escolta()
        melhor, melhor_nota = None, -math.inf
        for graus in CFG.recuo_leque:
            candidato = para_tras.rotate(graus)
            if not self.verificar_posicao_valida(self.posicao + candidato * CFG.recuo_sonda):
                continue
            nota = candidato.dot(para_tras)
            if escolta is not None:
                nota += CFG.recuo_puxa_escolta * candidato.dot(escolta)
            if nota > melhor_nota:
                melhor, melhor_nota = candidato, nota
        self._rumo_recuo, self._rumo_recuo_ate = melhor, agora + CFG.recuo_rumo_ms
        return melhor

    def _direcao_da_escolta(self):
        """Direção (unitária) até o meio dos Elites vivos; None sem escolta ou em cima dela."""
        vivos = self.escoltas_vivas
        if not vivos:
            return None
        meio = sum((e.posicao for e in vivos), V2()) / len(vivos) - self.posicao
        return meio.normalize() if meio.length_squared() > 1e-6 else None

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

    def _dash(self, preset, alvo=None, gatilho=None):
        """Sub-rotina: investida até `alvo` (padrão: onde o jogador está agora). Devolve a direção.
        Inofensivo no caminho: quem fere é a espada que vem junto ou no fim (o corpo de 250 px
        encostaria em quem desviou por pouco). `gatilho` = (fração, função): chama `função(posição,
        direção)` uma vez, quando ele passa por essa fração do caminho (ou no fim, se parou antes)."""
        dash = Dash(self, self.jogador.posicao if alvo is None else alvo, preset=preset)
        inicio = V2(self.posicao)
        caminho = (dash.alvo - inicio).dot(dash.direcao)
        antes, self.is_inofensivo = self.is_inofensivo, True
        try:
            while True:
                acabou = dash.atualizar(self._dt, self._paredes)
                if gatilho is not None and (acabou or (self.posicao - inicio).dot(dash.direcao)
                                            >= gatilho[0] * caminho):
                    gatilho[1](V2(self.posicao), V2(dash.direcao))
                    gatilho = None
                if acabou:
                    break
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
                self._recuar(CFG.recuo_mult_vel)
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
