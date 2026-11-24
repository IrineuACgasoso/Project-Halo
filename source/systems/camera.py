import pygame
from source.systems.gameclock import relogio
import random


class Camera:
    """Segue o jogador, treme e afasta.

    Zoom: 1 = normal; menor que 1 mostra mais do mundo (0.5 = o dobro em cada eixo). Quem quer mudar
    chama `definir_zoom(alvo, ms)`; a transição é suave e corre no relógio de jogo. Toda conta de
    "o que está na tela" usa `visao`, o tamanho do trecho do mundo mostrado."""

    def __init__(self, largura_tela, altura_tela, mapa):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        self.mapa = mapa
        self.offset = pygame.math.Vector2()

        # Atributos para o Shake
        self.shake_intensidade = 0
        self.shake_timer = 0
        self.shake_offset = pygame.math.Vector2()

        self.restaurar_zoom()

    # ── Zoom ─────────────────────────────────────────────────────────────────
    def definir_zoom(self, alvo, duracao_ms=0):
        """Vai suavemente até `alvo` (0 < alvo <= 1) em `duracao_ms`. Num mapa pequeno, para no zoom em
        que o mapa ainda cobre a tela."""
        if not 0 < alvo <= 1:
            raise ValueError(f'zoom {alvo!r} (precisa estar em (0, 1])')
        if duracao_ms < 0:
            raise ValueError(f'duração do zoom {duracao_ms!r} (precisa ser >= 0)')
        minimo = max(self.largura_tela / self.mapa.largura_mapa_pixels,
                     self.altura_tela / self.mapa.altura_mapa_pixels)
        self._zoom_de = self.zoom
        self.zoom_alvo = min(1, max(alvo, minimo))
        self._zoom_inicio = relogio.agora()
        self._zoom_duracao = duracao_ms
        self._zoom_maximo = min(self._zoom_maximo, self.zoom_alvo)
        self._atualizar_zoom()

    def restaurar_zoom(self):
        """Volta ao normal na hora (partida ou fase nova)."""
        self.zoom = self.zoom_alvo = self._zoom_de = 1
        self._zoom_inicio = self._zoom_duracao = 0
        self._zoom_maximo = 1      # o mais afastado desde que saiu do normal

    def _atualizar_zoom(self):
        if self.zoom == self.zoom_alvo:
            return
        passou = relogio.agora() - self._zoom_inicio
        if passou < self._zoom_duracao:
            t = passou / self._zoom_duracao
            t = t * t * (3 - 2 * t)      # sai e chega devagar
            self.zoom = self._zoom_de + (self.zoom_alvo - self._zoom_de) * t
            return
        self.zoom = self.zoom_alvo
        if self.zoom == 1:
            self._zoom_maximo = 1

    def _visao_no_zoom(self, zoom):
        return round(self.largura_tela / zoom), round(self.altura_tela / zoom)

    @property
    def visao(self):
        """(largura, altura), em px do mundo, do trecho que aparece na tela."""
        return self._visao_no_zoom(self.zoom)

    @property
    def visao_maxima(self):
        """A maior `visao` desde que o zoom saiu de 1: o tamanho da superfície em que o mundo é
        desenhado (fixo enquanto o zoom anda, para não criar superfície a cada frame)."""
        return self._visao_no_zoom(self._zoom_maximo)

    # ── Tremor e posição ─────────────────────────────────────────────────────
    def shake(self, intensidade, duracao=200):
        self.shake_intensidade = intensidade
        self.shake_timer = relogio.agora() + duracao

    def update(self, player_pos):
        self._atualizar_zoom()
        largura, altura = self.visao

        # 1. Seguir o Jogador (centralizar)
        self.offset.x = player_pos.x - largura / 2
        self.offset.y = player_pos.y - altura / 2

        # 2. Limitar às bordas do mapa
        self.offset.x = max(0, min(self.offset.x, self.mapa.largura_mapa_pixels - largura))
        self.offset.y = max(0, min(self.offset.y, self.mapa.altura_mapa_pixels - altura))

        # 3. Aplicar o Shake se estiver ativo
        if relogio.agora() < self.shake_timer:
            self.shake_offset.x = random.uniform(-self.shake_intensidade, self.shake_intensidade)
            self.shake_offset.y = random.uniform(-self.shake_intensidade, self.shake_intensidade)
        else:
            self.shake_offset = pygame.math.Vector2(0, 0)

    def apply(self, entidade):
        # Retorna o rect da entidade ajustado pela câmera + shake
        return entidade.rect.topleft - self.offset + self.shake_offset

    def apply_pos(self, posicao):
        # Retorna uma posição ajustada (para draw de linhas/partículas)
        return posicao - self.offset + self.shake_offset
