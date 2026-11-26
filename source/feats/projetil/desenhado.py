"""Tiros pintados em código (sem asset), no padrão da gota da carabina.

- Acerto: o círculo do `tamanho` (rect e máscara), igual para todo ângulo.
- Corpo (`desenhar_corpo`): apontando para a direita, centrado no ponto de acerto (pode ser maior que o
  `tamanho`: cauda, rastro). Pintado 1× e girado 1× por ângulo (GLOBAL_CACHE).
- Brilho (`desenhar_brilho`, opcional): redondo, sem girar, em `QUADROS` intensidades (o cintilar), somado
  na tela (BLEND_RGB_ADD: fundo preto, sem alpha) por cima do corpo, `BRILHO_A_FRENTE` × tamanho à frente.
- Por frame: um ou dois blits. `preparar(tamanho)` pinta e gira tudo de uma vez (no spawn de quem atira),
  para nenhum cache encher no meio da luta.

Ajudantes: `pintar_perfil` (corpo por círculos ao longo do eixo, de fora para dentro: os degraus de alpha
viram um contorno suave) e `brilho_aditivo` (halo para somar na tela)."""
import math

import pygame

from source.systems.gameclock import relogio
from source.utils.superficies import mascara_de
from .projetil import ProjetilUniversal


def pintar_perfil(surf, x_cauda, x_ponta, cy, perfil, camadas, passos=24):
    """Corpo ao longo do eixo x: em cada ponto `t` (0 = cauda, 1 = ponta) um círculo de raio `perfil(t)`,
    para cada camada `(cor, alpha, escala)` (de fora para dentro)."""
    for cor, alpha, escala in camadas:
        for i in range(passos + 1):
            t = i / passos
            raio = perfil(t) * escala
            if raio >= 0.5:
                pygame.draw.circle(surf, (*cor, alpha), (x_cauda + (x_ponta - x_cauda) * t, cy), raio)


def brilho_aditivo(raio, cor, forca=1.0, expoente=1.8, lado=None):
    """Halo para somar na tela: fundo preto, cor mais forte no centro. `lado`: tamanho da imagem (padrão 2×raio)."""
    lado = lado or round(raio * 2) + 2
    imagem = pygame.Surface((lado, lado))
    centro = (lado / 2, lado / 2)
    r = raio
    while r > 0:
        queda = (1 - r / raio) ** expoente * forca
        pygame.draw.circle(imagem, [min(255, round(c * queda)) for c in cor], centro, r)
        r -= 1.5
    return imagem


def forma_de_acerto(tamanho):
    """O círculo cheio do `tamanho` (dá o rect e a máscara de todo tiro desenhado), em cache."""
    chave = f"acerto_circulo_{tamanho[0]}x{tamanho[1]}"
    forma = ProjetilUniversal.GLOBAL_CACHE.get(chave)
    if forma is None:
        forma = ProjetilUniversal.GLOBAL_CACHE[chave] = pygame.Surface(tamanho, pygame.SRCALPHA)
        pygame.draw.circle(forma, (255, 255, 255, 255), (tamanho[0] // 2, tamanho[1] // 2), min(tamanho) // 2)
    return forma


class ProjetilDesenhado(ProjetilUniversal):
    QUADROS = 1           # quadros do brilho (cintilar)
    PERIODO_MS = 60       # quanto dura cada quadro
    PASSO_ANGULO = 3      # graus (cache do corpo girado)
    BRILHO_A_FRENTE = 0.0   # × tamanho: o centro do brilho fica à frente do ponto de acerto

    def __init__(self, **kwargs):
        kwargs['rotacionar'] = False          # quem gira é o corpo; o acerto é sempre o círculo
        super().__init__(**kwargs)
        corpos, self._brilhos = self._caches(self.tamanho)
        graus = math.degrees(math.atan2(-self.direcao.y, self.direcao.x))
        angulo = round(graus / self.PASSO_ANGULO) * self.PASSO_ANGULO % 360
        self._corpo = corpos.get(angulo)
        if self._corpo is None:
            self._corpo = corpos[angulo] = pygame.transform.rotate(corpos['base'], angulo)
        self._desvio_brilho = pygame.math.Vector2(self.direcao) * (self.BRILHO_A_FRENTE * min(self.tamanho))
        self.image = self._corpo

    # ------------------------------------------------------------ pintura (subclasse)
    @classmethod
    def desenhar_corpo(cls, tamanho):
        """SRCALPHA apontando para a direita, com o ponto de acerto no centro."""
        raise NotImplementedError

    @classmethod
    def desenhar_brilho(cls, tamanho, quadro):
        """Imagem sem alpha (fundo preto) somada na tela, ou None (sem brilho)."""
        return None

    # ------------------------------------------------------------ cache
    @classmethod
    def _caches(cls, tamanho):
        """(corpos por ângulo, com a 'base' sem girar; brilhos por quadro), criados 1× por classe e tamanho."""
        chave = f"desenhado_{cls.__name__}_{tamanho[0]}x{tamanho[1]}"
        caches = ProjetilUniversal.GLOBAL_CACHE.get(chave)
        if caches is None:
            brilhos = tuple(b for b in (cls.desenhar_brilho(tamanho, q) for q in range(cls.QUADROS)) if b is not None)
            caches = ProjetilUniversal.GLOBAL_CACHE[chave] = ({'base': cls.desenhar_corpo(tamanho)}, brilhos)
        return caches

    @classmethod
    def preparar_imagens(cls, tamanho):
        """Pinta o corpo, os brilhos e a forma de acerto (no spawn de quem atira; depois é só consulta)."""
        cls._caches(tamanho)
        mascara_de(forma_de_acerto(tamanho))

    @classmethod
    def preparar(cls, tamanho):
        """`preparar_imagens` e o corpo já girado em todo ângulo (bosses: nada enche no meio da luta)."""
        cls.preparar_imagens(tamanho)
        corpos, _ = cls._caches(tamanho)
        for angulo in range(0, 360, cls.PASSO_ANGULO):
            if angulo not in corpos:
                corpos[angulo] = pygame.transform.rotate(corpos['base'], angulo)

    def obter_imagem_base(self, sprite_key, tamanho):
        return forma_de_acerto(tamanho)

    # ------------------------------------------------------------ desenho
    def draw(self, surface, offset):
        x, y = self.rect.centerx - offset.x, self.rect.centery - offset.y
        corpo = self._corpo
        surface.blit(corpo, (x - corpo.get_width() / 2, y - corpo.get_height() / 2))
        brilhos = self._brilhos
        if brilhos:
            brilho = brilhos[int((relogio.agora() - self.spawn_time) // self.PERIODO_MS) % len(brilhos)]
            surface.blit(brilho, (x + self._desvio_brilho.x - brilho.get_width() / 2,
                                  y + self._desvio_brilho.y - brilho.get_height() / 2),
                         special_flags=pygame.BLEND_RGB_ADD)

