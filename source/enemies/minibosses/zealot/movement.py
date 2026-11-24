"""Movimentos do Zealot: parar, buff de velocidade da camuflagem, dash e fuga com despiste."""
import random

import pygame

from source.feats.skills.dash import Dash
from source.systems.status import BuffVelocidade, aplicar, remover
from source.utils.vetores import no_cone

from .config import CFG, COS_FUGA

V2 = pygame.math.Vector2


class ZealotMovement:
    def _parar(self):
        self.velocidade = 0
        self.animador.tocar('preparo')

    def _esperar(self, ms, olhar_x=None):
        """Sub-rotina: `ms` de tempo de jogo parado (com `olhar_x`, sem virar para o jogador)."""
        fim = self._agora + ms
        while self._agora < fim:
            self._parar()
            self._olhar_x = olhar_x
            yield

    # ------------------------------------------------------------ buff de velocidade
    def _buffar(self, porcentagem):
        if self._buff != porcentagem:
            self._buff = porcentagem
            aplicar(self, BuffVelocidade(porcentagem), chave=self)

    def _tirar_buff(self):
        if self._buff is not None:
            self._buff = None
            remover(self, BuffVelocidade, chave=self)

    # ------------------------------------------------------------ dash
    def _dash(self, preset):
        """Sub-rotina: investida até onde o jogador está agora. Devolve a direção dela: os golpes
        seguintes saem nesse mesmo vetor, e não no jogador (desviar para o lado funciona)."""
        dash = Dash(self, self.jogador.posicao, preset=preset)
        while not dash.atualizar(self._dt, self._paredes):
            self.velocidade = 0
            self._olhar_x = dash.direcao.x
            self.animador.tocar('dash')
            self.marcar_rastro(self._agora)
            yield
        return dash.direcao

    # ------------------------------------------------------------ perseguição camuflada
    def perseguir(self):
        """Um frame indo até o jogador. Travado numa parede, contorna de lado por um instante."""
        andou = self.posicao.distance_to(self._pos_perseguicao)
        esperado = self.velocidade_atual() * self._dt
        self._pos_perseguicao.update(self.posicao)
        self._travado_ms = self._travado_ms + self._dt * 1000 if andou < esperado * 0.35 else 0.0
        if self._travado_ms >= CFG.contorno_travado_ms:
            self._travado_ms = 0.0
            self._contornar_ate = self._agora + random.randint(*CFG.contorno_ms)
            self._lado_contorno = random.choice((-1, 1))
        direcao = self.dir_jogador()
        if self._agora < self._contornar_ate:
            direcao = V2(-direcao.y, direcao.x) * self._lado_contorno
        self._ir(direcao)
        self.animador.tocar('correr')

    def _reaparecer(self):
        """Sub-rotina: segue andando até o fim do fade in (já pode ser mirado)."""
        self.encerrar_invisibilidade()
        while self.invisibilidade is not None:
            yield

    # ------------------------------------------------------------ fuga
    def fugir(self):
        """Um frame de fuga: corre para um ponto sorteado longe do jogador, mudando de rumo ao acaso."""
        if (self._agora >= self._troca_fuga_em
                or self.posicao.distance_squared_to(self._ponto_fuga) < 60 ** 2):
            self._ponto_fuga = self._sortear_ponto_de_fuga()
            self._troca_fuga_em = self._agora + random.randint(*CFG.fuga_troca_ms)
        direcao = self._ponto_fuga - self.posicao
        self._ir(direcao)
        self._olhar_x = direcao.x
        self.animador.tocar('correr')

    def _sortear_ponto_de_fuga(self):
        """Entre pontos válidos do mapa, um dos 3 mais próximos da distância ideal até o jogador.
        Perto demais dele, só passa pelo jogador se não houver outra saída (encurralado)."""
        mapa = self.game.mapa
        margem = CFG.fuga_margem_mapa
        para_jogador = self.dir_jogador()
        perto = self.dist_jogador() < CFG.fuga_dist_ideal
        candidatos, pelo_jogador = [], []
        for _ in range(CFG.fuga_tentativas):
            direcao = V2(1, 0).rotate(random.uniform(0, 360))
            ponto = self.posicao + direcao * random.uniform(*CFG.fuga_passo)
            if not (margem <= ponto.x <= mapa.largura_mapa_pixels - margem
                    and margem <= ponto.y <= mapa.altura_mapa_pixels - margem
                    and self.verificar_posicao_valida(ponto)):
                continue
            if not mapa.caminho_livre(self.posicao, ponto):
                continue
            lista = pelo_jogador if perto and no_cone((0, 0), para_jogador, direcao, COS_FUGA) else candidatos
            lista.append((abs(ponto.distance_to(self.jogador.posicao) - CFG.fuga_dist_ideal), ponto))
        candidatos = candidatos or pelo_jogador
        if not candidatos:
            # Nenhum ponto válido: para longe, sem sair do mapa (perto da borda, sorteia de novo já)
            ponto = self.posicao - para_jogador * CFG.fuga_passo[0]
            ponto.x = max(margem, min(ponto.x, mapa.largura_mapa_pixels - margem))
            ponto.y = max(margem, min(ponto.y, mapa.altura_mapa_pixels - margem))
            return ponto
        candidatos.sort(key=lambda c: c[0])
        return random.choice(candidatos[:3])[1]

    # ------------------------------------------------------------ anti-stuck
    def realizar_teleporte(self):
        """Ponto válido em volta do jogador (só o anti-stuck usa)."""
        for _ in range(CFG.antistuck_tentativas):
            ponto = (self.jogador.posicao
                     + V2(random.uniform(*CFG.antistuck_raio), 0).rotate(random.uniform(0, 360)))
            if self.verificar_posicao_valida(ponto):
                self.posicao.update(ponto)
                self.sync_rect()
                return True
        return False
