import pygame
from source.systems.gameclock import relogio
import random
from source.feats.assets import *
from source.feats import particulas
from source.utils.superficies import SUPERFICIE_VAZIA, camada_alpha

DURACAO_POEIRA_MS = 255 / 400 * 1000   # o alpha caía 400/s a partir de 255


def emitir_poeira(posicao, grupos=None):
    """Partícula de terra/lodo que explode para os lados e para cima e some com fade.
    Mesma sequência de sorteios da antiga DustParticle (roteiro C3: agora sem Surface própria)."""
    tamanho = random.randint(4, 8)   # tamanho aleatório para variação visual
    cor = random.choice([(70, 50, 30), (40, 60, 30), (100, 80, 50)])   # marrom esverdeado
    direcao = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-2, -0.5))
    velocidade = random.uniform(50, 150)
    return particulas.emitir(posicao, particulas.imagem_pixel(cor, tamanho, 'circulo'),
                             direcao * velocidade, DURACAO_POEIRA_MS, grupos)


class Portal(pygame.sprite.Sprite):
    def __init__(self, pos, grupos):
        super().__init__(grupos)
        self.image = ASSETS['effects']['portal']
        # Cria a máscara baseada nos pixels não transparentes da imagem
        self.mask = pygame.mask.from_surface(self.image)
        # Desenha um círculo ciano para debug ou visualização
        self.rect = self.image.get_rect(center=pos)


class RaioEscudo(pygame.sprite.Sprite):
    def __init__(self, fonte, alvo, grupos, cor=(255, 40, 0)):
        super().__init__(grupos)
        self.fonte = fonte
        self.alvo = alvo
        self.cor = cor
        
        self.duracao = 250 
        self.tempo_criacao = relogio.agora()

        self.image = SUPERFICIE_VAZIA   # o draw é próprio (roteiro C3: antes, 1 Surface por frame)
        self.atualizar_caixa()

    def atualizar_caixa(self):
        """Caixa do raio no mundo (ordem de desenho e recorte). O raio sai do rect.center."""
        fonte_x, fonte_y = self.fonte.rect.center
        alvo_x, alvo_y = self.alvo.rect.center
        padding = 15
        self.rect = pygame.Rect(min(fonte_x, alvo_x) - padding, min(fonte_y, alvo_y) - padding,
                                max(abs(alvo_x - fonte_x) + padding * 2, 1),
                                max(abs(alvo_y - fonte_y) + padding * 2, 1))
        self.posicao = pygame.math.Vector2(self.rect.center)

    def draw(self, surface, offset):
        camada, area = camada_alpha(surface, self.rect.move(-offset.x, -offset.y))
        if camada is None:
            return
        inicio = pygame.math.Vector2(self.fonte.rect.center) - offset
        fim = pygame.math.Vector2(self.alvo.rect.center) - offset
        pygame.draw.line(camada, (*self.cor, 100), inicio, fim, 15)
        pygame.draw.line(camada, (255, 255, 255), inicio, fim, 3)
        surface.blit(camada, area.topleft, area)

    def update(self, delta_time, paredes=None):
        agora = relogio.agora()
        if agora - self.tempo_criacao > self.duracao or not self.alvo.alive() or not self.fonte.alive():
            self.kill()
        else:
            self.atualizar_caixa()



class EfeitoFaiscas(pygame.sprite.Sprite):
    """
    Pequeno estouro de faíscas, usado no contra-ataque dos espinhos
    (e reaproveitável em qualquer outro impacto/reflexo de dano).
    Não depende de nenhum asset — desenha tudo proceduralmente e some
    sozinho depois de `duracao` ms.
    """

    def __init__(self, posicao, grupos, cor=(255, 210, 90), quantidade=10, duracao=280):
        super().__init__(grupos)
        self.posicao = pygame.math.Vector2(posicao)
        self.cor = cor
        self.duracao = duracao
        self.criado_em = relogio.agora()

        self.particulas = [
            {
                'dir': pygame.math.Vector2(1, 0).rotate(random.uniform(0, 360)),
                'vel': random.uniform(120, 260),
                'tam': random.uniform(2, 5),
            }
            for _ in range(quantidade)
        ]

        tam_canvas = 240
        self.image = pygame.Surface((tam_canvas, tam_canvas), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.posicao)
        self._centro_local = pygame.math.Vector2(tam_canvas / 2, tam_canvas / 2)

    def update(self, delta_time):
        agora = relogio.agora()
        decorrido = agora - self.criado_em
        if decorrido >= self.duracao:
            self.kill()
            return

        progresso = decorrido / self.duracao
        alpha = max(0, int(255 * (1 - progresso)))

        self.image.fill((0, 0, 0, 0))
        for p in self.particulas:
            offset = p['dir'] * p['vel'] * (decorrido / 1000)
            pos = self._centro_local + offset
            raio = max(0.5, p['tam'] * (1 - progresso))
            pygame.draw.circle(self.image, (*self.cor, alpha), pos, raio)

        self.rect.center = self.posicao