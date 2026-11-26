"""Movimento do Tartarus: nunca recua. Sem rotina, avança em linha reta no jogador (o contato fere).

ATENÇÃO: este mixin precisa vir ANTES de BossBase na herança da classe (MRO)."""
import pygame

from source.feats.particulas.poeira import rastro_de_poeira
from source.feats.skills.dash import Dash

from .config import CFG

V2 = pygame.math.Vector2


class TartarusMovement:
    def _resetar_movimento(self):
        """Default de TODO frame: perseguir, olhando para o jogador. Rotinas sobrescrevem."""
        self._ir(None)
        self._olhar_x = None
        self.animador.tocar('andar')

    def orientar(self):
        if self._olhar_x is not None:
            self.set_sprite_direction(self._olhar_x)
        else:
            super().orientar()

    def _parar(self, olhar_x=None, clip='parado'):
        self.velocidade = 0
        self._olhar_x = olhar_x
        self.animador.tocar(clip)

    def movimento_ocioso(self, agora):
        if self.contexto.dist > CFG.perto_px:
            self._ir(self.dir_jogador())
        else:
            self._parar()

    # -------------------------------------------------------- sub-rotinas
    def _esperar(self, ms, olhar_x=None, clip='parado'):
        """Passa `ms` de tempo de jogo parado (`olhar_x` None: encarando o jogador)."""
        fim = self._agora + ms
        while self._agora < fim:
            self._parar(self.dir_jogador().x if olhar_x is None else olhar_x, clip)
            yield

    def _ate_explodir(self, aviso, olhar_x=None, limite_ms=4000):
        """Parado até o aviso estourar (ou sumir). Não trava se ele nunca estourar."""
        fim = self._agora + limite_ms
        while not aviso.explodiu and aviso.alive() and self._agora < fim:
            self._parar(self.dir_jogador().x if olhar_x is None else olhar_x)
            yield

    def _dash(self, preset, alvo=None, inofensivo=True, rastro=False):
        """Investida até `alvo` (padrão: onde o jogador está agora). Devolve a direção.
        `inofensivo`: o corpo não fere no caminho (quem fere é o golpe do fim)."""
        dash = Dash(self, self.jogador.posicao if alvo is None else alvo, preset=preset)
        antes, self.is_inofensivo = self.is_inofensivo, inofensivo or self.is_inofensivo
        proximo_rastro = self._agora
        try:
            while not dash.atualizar(self._dt, self._paredes):
                self.velocidade = 0
                self._olhar_x = dash.direcao.x
                self.animador.tocar('corrida')
                if rastro and self._agora >= proximo_rastro:
                    proximo_rastro = self._agora + CFG.corrida_poeira_ms
                    rastro_de_poeira(V2(self.posicao.x, self.hitbox.bottom - 10), dash.direcao, 3)
                yield
        finally:
            self.is_inofensivo = antes
        return dash.direcao
