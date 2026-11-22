import random
import pygame

from source.windows.settings import largura_tela, altura_tela
from .constants import ARMAS_REGISTRO, MAX_ARMAS
from . import draw
from source.utils.fonts import carregar_fonte

FONTE_TITULO_TELA = ('assets', 'fonts', 'cinzel', 'Cinzel-Bold.otf')
FONTE_OPCAO_TITULO = ('assets', 'fonts', 'orbitron', 'Orbitron-ExtraBold.ttf')
FONTE_OPCAO_TEXTO = ('assets', 'fonts', 'orbitron', 'Orbitron-Medium.ttf')


class TelaDeUpgrade:
    """Orquestra a tela de level-up: decide quais opções aparecem e reage
    aos inputs. Todo o desenho de fato mora em draw.py — esta classe só
    guarda o estado (opções, seleção, rects) que o draw.py consome.

    `id_arma_forcada`: se informado, ignora o sorteio normal e mostra
    APENAS essa arma como opção única (usado, por ex., pelo item
    'upgrade', que força o upgrade de uma arma específica já possuída).
    `ids_das_opcoes`: opções já sorteadas (`gerar_opcoes`); sem elas, sorteia aqui.
    """

    def __init__(self, tela, jogador, game, id_arma_forcada=None, ids_das_opcoes=None):
        self.tela = tela
        self.jogador = jogador
        self.game = game
        self.opcao_selecionada = 0

        self.modo_unico = id_arma_forcada is not None
        if self.modo_unico:
            self.ids_das_opcoes = [id_arma_forcada]
        else:
            self.ids_das_opcoes = list(ids_das_opcoes) if ids_das_opcoes is not None else gerar_opcoes(jogador)
        if not self.ids_das_opcoes:
            raise ValueError('tela de upgrade sem opções (quem abre a tela checa antes: recompensa_sem_upgrade)')
        # Fontes em cache (antes: 5 leituras de .otf/.ttf do disco a CADA level-up, e atributos
        # inexistentes quando o arquivo de fonte faltava -> AttributeError no meio do jogo).
        self.fonte_grande = carregar_fonte(FONTE_TITULO_TELA, 24, fallback_tamanho=28)
        self.fonte_pequena = carregar_fonte(FONTE_TITULO_TELA, 12, fallback_tamanho=20)

        largura_painel, altura_painel = 1000, 500
        self.painel_rect = pygame.Rect(
            (largura_tela - largura_painel) // 2,
            (altura_tela - altura_painel) // 2,
            largura_painel, altura_painel
        )

        self.opcoes = [
            OpcaoDeUpgrade(id_arma, rect, self.jogador)
            for id_arma, rect in zip(self.ids_das_opcoes, self._calcular_rects_opcoes())
        ]

    def _calcular_rects_opcoes(self):
        padding = 15
        num_opcoes = len(self.ids_das_opcoes)
        altura_opcao = self.painel_rect.height - padding * 3 - 40
        pos_y = self.painel_rect.y + 70

        if num_opcoes == 1:
            # Opção única: painel largo, ocupando quase todo o espaço horizontal
            largura_opcao = self.painel_rect.width - padding * 2
            pos_x = self.painel_rect.x + padding
            return [pygame.Rect(pos_x, pos_y, largura_opcao, altura_opcao)]

        largura_opcao = (self.painel_rect.width - padding * (num_opcoes + 1)) // num_opcoes
        return [
            pygame.Rect(
                self.painel_rect.x + padding + i * (largura_opcao + padding),
                pos_y, largura_opcao, altura_opcao
            )
            for i in range(num_opcoes)
        ]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            # Navegação só faz sentido com mais de uma opção na tela
            if len(self.opcoes) > 1:
                if event.key == pygame.K_d:
                    self.opcao_selecionada = (self.opcao_selecionada + 1) % len(self.opcoes)
                elif event.key == pygame.K_a:
                    self.opcao_selecionada = (self.opcao_selecionada - 1) % len(self.opcoes)

            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                return self.ids_das_opcoes[self.opcao_selecionada]
        return None

    def draw(self, surface):
        draw.draw_tela_upgrade(surface, self)


def sortear_armas_novas(ids, quantidade, rng=random):
    """Até `quantidade` armas distintas de `ids`, cada uma com o peso da sua raridade
    (PESO_SORTEIO_POR_RARIDADE): sorteio ponderado sem reposição."""
    restantes = list(ids)
    escolhidas = []
    while restantes and len(escolhidas) < quantidade:
        pesos = [ARMAS_REGISTRO[i].peso_sorteio for i in restantes]
        escolhida = rng.choices(restantes, weights=pesos)[0]
        escolhidas.append(escolhida)
        restantes.remove(escolhida)
    return escolhidas


def gerar_opcoes(jogador, rng=random):
    """Até 3 opções do level-up: até 2 upgrades (armas abaixo do máximo, sorteio uniforme),
    completadas com armas novas (peso por raridade, se houver vaga no arsenal) e, faltando,
    com mais upgrades. Lista vazia = nada a oferecer (todas as armas no máximo e arsenal cheio)."""
    opcoes_upgrade = [i for i, arma in jogador.armas.items() if not arma.no_maximo]
    opcoes_novas = []
    if len(jogador.armas) < MAX_ARMAS:
        opcoes_novas = [i for i in ARMAS_REGISTRO if i not in jogador.armas]

    escolhidas = rng.sample(opcoes_upgrade, min(2, len(opcoes_upgrade)))
    escolhidas += sortear_armas_novas(opcoes_novas, 3 - len(escolhidas), rng)
    restantes = [u for u in opcoes_upgrade if u not in escolhidas]
    escolhidas += rng.sample(restantes, min(3 - len(escolhidas), len(restantes)))
    return escolhidas


class OpcaoDeUpgrade:
    """Só guarda os dados de uma opção (id, rect, referência ao jogador).
    Não desenha nada — draw.py lê esses dados pra renderizar."""

    def __init__(self, id_arma, retangulo, jogador):
        self.id = id_arma
        self.rect = retangulo
        self.jogador = jogador
        self.dados = ARMAS_REGISTRO[id_arma]

        self.fonte_titulo = carregar_fonte(FONTE_OPCAO_TITULO, 20, fallback_tamanho=18)
        self.fonte_texto = carregar_fonte(FONTE_OPCAO_TEXTO, 14, fallback_tamanho=18, bold=False)
        # nomes antigos mantidos por compatibilidade
        self.font_title = self.fonte_titulo
        self.font_text = self.fonte_texto
