import math

import pygame
from .projetil import ProjetilUniversal
from source.systems.dano import Dano, PROJETIL
from source.utils.superficies import mascara_de

class Carabin(ProjetilUniversal):
    """Tiro da carabina Covenant: gota de plasma alongada na direção do voo (cabeça redonda e brilhante,
    cauda que afina), com halo em degraus de alpha e núcleo branco. Desenhada uma vez por tamanho e
    girada uma vez por ângulo (GLOBAL_CACHE). Só o desenho gira: o rect e a máscara de acerto são o
    círculo do `tamanho`, como antes da gota."""

    # (cor, alpha, escala do raio), de fora para dentro
    CAMADAS = {
        'carabin': (((60, 150, 255), 85, 1.0), ((110, 195, 255), 150, 0.78),
                    ((170, 225, 255), 230, 0.56), ((255, 255, 255), 255, 0.32)),
        'bcarabin': (((200, 20, 30), 85, 1.0), ((255, 60, 60), 150, 0.78),
                     ((255, 150, 140), 230, 0.56), ((255, 240, 235), 255, 0.32)),
    }
    PASSOS = 14          # círculos ao longo do corpo, da cauda à cabeça
    PASSO_ANGULO = 2     # graus (cache das imagens giradas)

    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread, duracao=2000, is_Banished=False, fonte=None):
        s_key = 'bcarabin' if is_Banished else 'carabin'
        super().__init__(
            posicao_inicial = posicao_inicial,
            grupos = grupos,
            game = game,
            dono=dono,
            fonte=fonte,
            sprite_key = s_key,
            tamanho = tamanho,
            dano = dano,
            velocidade = velocidade,
            duracao = duracao,
            direcao_custom = direcao_spread,
            rotacionar = False,
            )
        self.mask = mascara_de(self._forma_de_acerto(tamanho))
        self.image = self._girada()

    @staticmethod
    def _forma_de_acerto(tamanho):
        chave = f"acerto_carabin_{tamanho[0]}x{tamanho[1]}"
        forma = ProjetilUniversal.GLOBAL_CACHE.get(chave)
        if forma is None:
            forma = ProjetilUniversal.GLOBAL_CACHE[chave] = pygame.Surface(tamanho, pygame.SRCALPHA)
            pygame.draw.circle(forma, (255, 255, 255, 255), (tamanho[0] // 2, tamanho[1] // 2), tamanho[0] // 2)
        return forma

    def _girada(self):
        graus = math.degrees(math.atan2(-self.direcao.y, self.direcao.x))
        angulo = round(graus / self.PASSO_ANGULO) * self.PASSO_ANGULO % 360
        cache = ProjetilUniversal.GLOBAL_CACHE.setdefault(f"girada_{self.sprite_key}_{self.tamanho[0]}x{self.tamanho[1]}", {})
        imagem = cache.get(angulo)
        if imagem is None:
            imagem = cache[angulo] = pygame.transform.rotate(self.image_base, angulo)
        return imagem

    def draw(self, surface, offset):
        surface.blit(self.image, self.image.get_rect(center=(self.rect.centerx - offset.x, self.rect.centery - offset.y)))

    def obter_imagem_base(self, sprite_key, tamanho):
        """Desenha a gota (apontando para a direita) uma vez e cacheia no GLOBAL_CACHE. Num SRCALPHA o
        círculo de dentro sobrescreve o de fora: os degraus de alpha viram um halo suave."""
        base_key = f"base_{sprite_key}_{tamanho[0]}x{tamanho[1]}"
        if base_key not in ProjetilUniversal.GLOBAL_CACHE:
            w, h = tamanho
            surf = pygame.Surface(tamanho, pygame.SRCALPHA)
            raio_cabeca = min(w, h) * 0.30
            cabeca = w - raio_cabeca - 1
            cauda = 1 + raio_cabeca * 0.3
            for cor, alpha, escala in self.CAMADAS.get(sprite_key, self.CAMADAS['carabin']):
                inicio = cabeca - (cabeca - cauda) * (0.3 + 0.7 * escala)   # o miolo é mais curto
                for i in range(self.PASSOS + 1):
                    t = i / self.PASSOS
                    raio = raio_cabeca * escala * (0.25 + 0.75 * t * t)
                    x = inicio + (cabeca - inicio) * t
                    pygame.draw.circle(surf, (*cor, alpha), (x, h / 2), max(1.0, raio))
            # brilho na frente da cabeça
            pygame.draw.circle(surf, (255, 255, 255, 255), (cabeca + raio_cabeca * 0.25, h / 2),
                               max(1.0, raio_cabeca * 0.18))
            ProjetilUniversal.GLOBAL_CACHE[base_key] = surf
        return ProjetilUniversal.GLOBAL_CACHE[base_key]

    def ao_atingir_alvo(self, alvo):
        qtd = self.dano
        # Checa se o alvo existe e se NÃO está invulnerável
        if alvo and not getattr(alvo, 'invulneravel', False):
            if hasattr(alvo, 'escudo_atual') and alvo.escudo_atual > 0:
                qtd *= 3
            alvo.receber_dano(Dano(qtd, PROJETIL, self.fonte, habilidade=self.habilidade))
        self.kill()
        