import pygame
from source.systems.gameclock import relogio
import random
from source.feats.assets import *
from source.feats import particulas
from source.systems.entitymanager import entity_manager
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


SORTEIO = random.Random()   # só visual: não mexe na sequência da simulação


# ── Quebra de escudo (padrão de todo escudo, do jogador e dos inimigos) ──────
CORES_FAGULHA_AZUL = ((90, 190, 255), (40, 120, 255), (200, 240, 255))
CORES_FAGULHA_AMARELA = ((255, 235, 120), (255, 200, 50))
FAGULHAS_POR_PX = 0.45          # quantidade pelo tamanho do corpo
FAGULHAS_LIMITES = (26, 70)
MS_ENTRE_QUEBRAS = 400          # escudo que regenera um fio e cai de novo não vira uma chuva
TAMANHOS_FAGULHA = (4, 6, 8)


def preparar_quebra_de_escudo():
    """Pinta já as fagulhas (no início da partida): jogador e Elites quebram escudo no meio da horda."""
    for cor in CORES_FAGULHA_AMARELA + CORES_FAGULHA_AZUL:
        for tamanho in TAMANHOS_FAGULHA:
            particulas.variantes_alpha(particulas.imagem_pixel(cor, tamanho))


def quebra_de_escudo(alvo):
    """Fagulhas azuis e amarelas que saltam em volta do corpo de `alvo` e caem. Devolve False se a
    última quebra dele foi há pouco (sem efeito)."""
    agora = relogio.agora()
    if agora < getattr(alvo, 'proxima_quebra_escudo', 0):
        return False
    alvo.proxima_quebra_escudo = agora + MS_ENTRE_QUEBRAS
    corpo = getattr(alvo, 'hitbox', alvo.rect)
    minimo, maximo = FAGULHAS_LIMITES
    quantidade = max(minimo, min(maximo, round((corpo.width + corpo.height) * FAGULHAS_POR_PX)))
    centro = pygame.math.Vector2(corpo.center)
    for i in range(quantidade):
        direcao = pygame.math.Vector2(1, 0).rotate(SORTEIO.uniform(0, 360))
        borda = pygame.math.Vector2(direcao.x * corpo.width, direcao.y * corpo.height) * SORTEIO.uniform(0.35, 0.6)
        velocidade = direcao * SORTEIO.uniform(60, 220) - (0, SORTEIO.uniform(40, 160))
        cor = SORTEIO.choice(CORES_FAGULHA_AMARELA if i % 3 == 0 else CORES_FAGULHA_AZUL)
        particulas.emitir(centro + borda, particulas.imagem_pixel(cor, SORTEIO.choice(TAMANHOS_FAGULHA)), velocidade,
                          SORTEIO.uniform(700, 1200), y_desenho=alvo.rect.bottom + 1, gravidade=620)
    return True


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
