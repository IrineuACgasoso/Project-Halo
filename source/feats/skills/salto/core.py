"""Salto: pulo em arco, reutilizável por qualquer inimigo (generaliza o salto do Tartarus).

No ar o inimigo fica `no_ar` (ninguém o mira; as paredes não o seguram), inofensivo (sem dano de
contato) e, com `invulneravel`, sem tomar dano. O destino é travado no início e o pouso é sempre em
chão válido: se o ponto pedido não for, recua pela linha do salto até achar (ou pula no lugar).

Uso numa rotina geradora:
    salto = Salto(self, preset='arbiter_investida')
    try:
        while not salto.atualizar(self._dt):
            self.velocidade = 0
            yield
    finally:
        salto.cancelar()          # rotina cortada no meio: pousa e devolve as flags
"""
import math
import random

import pygame

from .config import SALTO_PRESETS

V2 = pygame.math.Vector2

_FRACOES_POUSO = (1.0, 0.85, 0.7, 0.55, 0.4, 0.25, 0.1)   # do destino de volta à origem
_SOMBRA_PASSO = 8   # px: largura da sombra arredondada (poucos tamanhos em cache)
_SOMBRAS = {}


class Salto:
    __slots__ = ('inimigo', 'cfg', 'inicio', 'destino', 'decorrido', 'terminou', '_flags')

    def __init__(self, inimigo, preset='padrao', alvo=None, config=None):
        if config is None and preset not in SALTO_PRESETS:
            raise KeyError(f'preset de salto desconhecido: {preset!r}')
        self.inimigo = inimigo
        self.cfg = config if config is not None else SALTO_PRESETS[preset]
        if self.cfg.alvo == 'ponto' and alvo is None:
            raise ValueError("salto com alvo 'ponto' precisa de `alvo`")
        self.inicio = V2(inimigo.posicao)
        self.destino = self._escolher_destino(alvo)
        self.decorrido = 0.0
        self.terminou = False
        self._flags = (inimigo.no_ar, getattr(inimigo, 'is_inofensivo', False),
                       getattr(inimigo, 'is_invulneravel', False))
        inimigo.no_ar = True
        inimigo.is_inofensivo = True
        if self.cfg.invulneravel:
            inimigo.is_invulneravel = True

    # ------------------------------------------------------------ destino
    def _escolher_destino(self, alvo):
        cfg = self.cfg
        if cfg.alvo == 'aleatorio':
            for _ in range(cfg.tentativas):
                ponto = self.inicio + V2(random.uniform(*cfg.distancia), 0).rotate(random.uniform(0, 360))
                if self.inimigo.verificar_posicao_valida(ponto):
                    return ponto
            return V2(self.inicio)
        ponto = V2(self.inimigo.jogador.posicao if cfg.alvo == 'jogador' else alvo)
        linha = ponto - self.inicio
        dist = linha.length()
        if dist < 1e-6:
            return self._pouso_valido(V2(self.inicio))
        minimo, maximo = cfg.distancia
        dist = max(minimo, min(maximo, dist - cfg.recuo))
        return self._pouso_valido(self.inicio + linha / linha.length() * dist)

    def _pouso_valido(self, ponto):
        """O ponto, ou o primeiro válido voltando pela linha do salto; nenhum: pula no lugar."""
        for fracao in _FRACOES_POUSO:
            candidato = self.inicio.lerp(ponto, fracao)
            if self.inimigo.verificar_posicao_valida(candidato):
                return candidato
        return V2(self.inicio)

    @property
    def direcao(self):
        """Unitário do início ao destino (salto no lugar: para o jogador)."""
        linha = self.destino - self.inicio
        if linha.length_squared() > 1e-6:
            return linha.normalize()
        para_jogador = self.inimigo.jogador.posicao - self.inicio
        return para_jogador.normalize() if para_jogador.length_squared() > 1e-6 else V2(1, 0)

    @property
    def progresso(self):
        return min(1.0, self.decorrido / self.cfg.duracao_ms)

    # ------------------------------------------------------------ passo
    def atualizar(self, delta_time):
        """Um passo do salto. Devolve True quando pousou (e continua True nas chamadas seguintes)."""
        if self.terminou:
            return True
        self.decorrido += delta_time * 1000
        progresso = self.progresso
        inimigo = self.inimigo
        inimigo.posicao.update(self.inicio.lerp(self.destino, progresso))
        inimigo.altura_z = math.sin(progresso * math.pi) * self.cfg.altura
        if progresso >= 1.0:
            self._pousar()
        inimigo.sync_rect()
        return self.terminou

    def cancelar(self):
        """Corta o salto: pousa já (no destino, se ainda estiver sobre parede). Sem efeito se pousou."""
        if self.terminou:
            return
        if not self.inimigo.verificar_posicao_valida(self.inimigo.posicao):
            self.inimigo.posicao.update(self.destino)
        self._pousar()
        self.inimigo.sync_rect()

    def _pousar(self):
        inimigo = self.inimigo
        inimigo.altura_z = 0.0
        inimigo.no_ar, inimigo.is_inofensivo, inimigo.is_invulneravel = self._flags
        self.terminou = True


def desenhar_sombra(tela, inimigo, deslocamento, largura):
    """Sombra no chão de quem está no ar: encolhe com a altura. Superfícies em cache por tamanho."""
    if inimigo.altura_z <= 0:
        return
    fator = max(0.45, 1.0 - inimigo.altura_z / 400)
    w = max(_SOMBRA_PASSO, int(largura * fator) // _SOMBRA_PASSO * _SOMBRA_PASSO)
    sombra = _SOMBRAS.get(w)
    if sombra is None:
        sombra = _SOMBRAS[w] = pygame.Surface((w, w // 3), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 90), sombra.get_rect())
    tela.blit(sombra, (inimigo.posicao.x - w / 2 - deslocamento.x,
                       inimigo.posicao.y - w / 6 - deslocamento.y + inimigo.rect.height * 0.35))
