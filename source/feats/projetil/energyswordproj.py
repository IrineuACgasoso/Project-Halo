import pygame
from source.systems.gameclock import relogio
import math

from .projetil import ProjetilUniversal
from source.utils.superficies import mascara_de



class EnergySwordProj(ProjetilUniversal):
    """
    Lâmina de energia com o cabo fixo na posição do jogador e a ponta
    apontando pra fora, a `distancia_orbita` de distância. O "orbitar"
    agora é uma rotação de verdade: a cada frame recalculamos o ângulo,
    reposicionamos o eixo cabo->ponta e re-renderizamos a imagem
    rotacionada — em vez de só mover um sprite estático num círculo.

    Dano: um acerto por inimigo a cada volta (`GRAUS_ENTRE_ACERTOS`). A
    lâmina perfura infinito, então sem esse limite o CollisionManager a
    faria bater no mesmo alvo a cada frame.
    """

    GRAUS_ENTRE_ACERTOS = 360

    # A arte da lâmina vem desenhada apontando ~45° para cima-direita em
    # vez de reto para a direita (0°). Este valor compensa isso na hora
    # de rotacionar. Se ainda ficar torta, inverta o sinal (-45) ou
    # ajuste o número — não dá pra acertar de olho sem rodar o jogo.
    AJUSTE_ANGULO_SPRITE = 45

    def __init__(self, posicao_inicial, grupos, game, dano, angulo_inicial, duracao, velocidade_rotacao, distancia_orbita):
        self.distancia_orbita = distancia_orbita
        self.angulo = angulo_inicial
        self._angulo_do_acerto = {}   # inimigo -> ângulo em que esta lâmina o acertou por último

        super().__init__(
            posicao_inicial=posicao_inicial, 
            grupos=grupos, 
            game=game, 
            dono='PLAYER', 
            sprite_key='energy_sword', 
            tamanho=(80, 80), 
            dano=dano, 
            velocidade=0, # Ela gira, não tem velocidade linear
            duracao=duracao, 
            piercing=float('inf')
        )
        self.jogador = game.player
        self.velocidade_rotacao = velocidade_rotacao #graus por segundo
        self.tempo_criacao = relogio.agora()
        self.duracao = duracao

        # Metade do comprimento da lâmina (eixo cabo -> ponta). Usado pra
        # puxar o centro do sprite pra fora: a ponta cai exatamente em
        # distancia_orbita e a base (cabo) fica perto do jogador.
        # OBS: se distancia_orbita for muito maior/menor que o tamanho do
        # sprite, o cabo não vai encostar perfeitamente no jogador — nesse
        # caso ajuste `tamanho` ou me avise que eu deixo isso dinâmico.
        self.alcance_lamina = self.tamanho[0] / 2

        self._atualizar_lamina()

    def _atualizar_lamina(self):
        direcao_radial = pygame.math.Vector2(
            math.cos(math.radians(self.angulo)),
            math.sin(math.radians(self.angulo))
        )

        # Centro do sprite entre o cabo (perto do player) e a ponta (na borda da órbita)
        centro_lamina = direcao_radial * (self.distancia_orbita - self.alcance_lamina)
        self.posicao = self.jogador.posicao + centro_lamina

        # Rotaciona a imagem pra acompanhar o ângulo atual, já compensando
        # a inclinação nativa da arte.
        angulo_render = int(round(-self.angulo - self.AJUSTE_ANGULO_SPRITE)) % 360
        cache = ProjetilUniversal.GLOBAL_CACHE.setdefault(self.chave_cache, {})
        if angulo_render not in cache:
            cache[angulo_render] = pygame.transform.rotate(self.image_base, angulo_render)
        self.image = cache[angulo_render]
        # A área de acerto é a da lâmina desenhada neste ângulo (rect e máscara giram juntos)
        self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))
        self.mask = mascara_de(self.image)

    def ao_atingir_alvo(self, alvo):
        if getattr(alvo, 'invulneravel', False):
            return   # não gasta o acerto da volta
        ultimo = self._angulo_do_acerto.get(alvo)
        if ultimo is not None and self.angulo - ultimo < self.GRAUS_ENTRE_ACERTOS:
            return
        self._angulo_do_acerto[alvo] = self.angulo
        super().ao_atingir_alvo(alvo)

    def update(self, delta_time):
        self.angulo += self.velocidade_rotacao * delta_time
        self._atualizar_lamina()

        if relogio.agora() - self.tempo_criacao > self.duracao:
            self.kill()