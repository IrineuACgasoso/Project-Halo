import pygame
from source.systems.gameclock import relogio
import random
from source.feats.assets import *
from source.feats import particulas
from source.systems.entitymanager import entity_manager
from source.utils.superficies import SUPERFICIE_VAZIA, camada_alpha

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


SORTEIO = random.Random()   # só visual: não mexe na sequência da simulação


# ── Soco Spartan (Mjolnir Punch) ─────────────────────────────────────────────
CORES_SOCO = ((255, 255, 235), (255, 225, 90), (255, 160, 25), (255, 85, 10))


def impacto_do_soco(origem, alvo):
    """Clarão e chuva de faíscas no ponto em que o punho (em `origem`) encontra o corpo de `alvo`."""
    direcao = alvo.posicao - origem
    if direcao.length_squared() == 0:
        direcao = pygame.math.Vector2(1, 0)
    ponto = origem + direcao * 0.5
    ClaraoDoSoco(ponto, direcao, (entity_manager.all_sprites,), y_desenho=alvo.rect.bottom + 2)
    comum = {'y_desenho': alvo.rect.bottom + 1, 'gravidade': 500, 'sorteio': SORTEIO}
    particulas.emitir_leque(ponto, direcao, 42, CORES_SOCO, (6, 8, 11), abertura_graus=120,
                            velocidade=(220, 760), duracao_ms=(400, 850), **comum)
    particulas.emitir_leque(ponto, direcao, 26, CORES_SOCO, (5, 6, 8), abertura_graus=360,
                            velocidade=(90, 380), duracao_ms=(350, 700), **comum)


class ClaraoDoSoco(pygame.sprite.Sprite):
    """Estrela branca e amarela com raios e um anel que se abre."""

    DURACAO_MS = 300
    RAIO = 120
    RAIOS = 14

    def __init__(self, posicao, direcao, grupos, y_desenho=None):
        super().__init__(grupos)
        self.posicao = pygame.math.Vector2(posicao)
        self.direcao = pygame.math.Vector2(direcao).normalize()
        self.y_desenho = y_desenho
        self.nascimento = relogio.agora()
        self.image = SUPERFICIE_VAZIA   # o draw é próprio
        self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))

    def update(self, delta_time):
        if relogio.agora() - self.nascimento >= self.DURACAO_MS:
            self.kill()

    def draw(self, surface, offset):
        t = min(1.0, (relogio.agora() - self.nascimento) / self.DURACAO_MS)
        centro = self.posicao - offset
        r = self.RAIO
        camada, area = camada_alpha(surface, (round(centro.x) - r, round(centro.y) - r, r * 2, r * 2))
        if camada is None:
            return
        alpha = round(255 * (1 - t))
        pygame.draw.circle(camada, (*CORES_SOCO[3], round(150 * (1 - t))), centro, r * (0.5 + 0.2 * t))
        for i in range(self.RAIOS):   # raios alternados: longos e curtos
            raio = self.direcao.rotate(i * 360 / self.RAIOS)
            longo = r * (0.95 if i % 2 == 0 else 0.6)
            pygame.draw.line(camada, (*CORES_SOCO[1 + i % 2], alpha), centro + raio * longo * t * 0.8,
                             centro + raio * longo * (0.45 + 0.55 * t), 8 if i % 2 == 0 else 5)
        pygame.draw.circle(camada, (*CORES_SOCO[2], alpha), centro, r * (0.25 + 0.7 * t), 6)
        pygame.draw.circle(camada, (*CORES_SOCO[1], alpha), centro, r * 0.42 * (1 - t))
        pygame.draw.circle(camada, (255, 255, 255, alpha), centro, r * 0.28 * (1 - t))
        surface.blit(camada, area.topleft, area)
