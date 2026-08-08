import random
import pygame
from os.path import join

from source.windows.settings import largura_tela, altura_tela
from .constants import ARMAS_REGISTRO, MAX_ARMAS
from . import draw
import pygame
import os


class TelaDeUpgrade:
    """Orquestra a tela de level-up: decide quais opções aparecem e reage
    aos inputs. Todo o desenho de fato mora em draw.py — esta classe só
    guarda o estado (opções, seleção, rects) que o draw.py consome.

    `id_arma_forcada`: se informado, ignora o sorteio normal e mostra
    APENAS essa arma como opção única (usado, por ex., pelo item
    'upgrade', que força o upgrade de uma arma específica já possuída).
    """

    def __init__(self, tela, jogador, game, id_arma_forcada=None):
        self.tela = tela
        self.jogador = jogador
        self.game = game
        self.opcao_selecionada = 0

        self.modo_unico = id_arma_forcada is not None
        self.ids_das_opcoes = (
            [id_arma_forcada] if self.modo_unico else self.gerar_opcoes_aleatorias()
        )
        # --- CARREGAMENTO DA FONTE ---
        self.font_path = join('assets', 'fonts', 'cinzel', 'Cinzel-Bold.otf')
        try:
            if os.path.exists(self.font_path):
                self.fonte_grande = pygame.font.Font(self.font_path, 24)
                self.fonte_pequena = pygame.font.Font(self.font_path, 12)
            else:
                self.fonte_grande = pygame.font.SysFont('Consolas', 28, bold=True)
                self.fonte_grande = pygame.font.SysFont('Consolas', 20, bold=True)
        except:
            self.fonte_grande = pygame.font.SysFont('Consolas', 28, bold=True)
            self.fonte_pequena = pygame.font.SysFont('Consolas', 20, bold=True)
        
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

    def gerar_opcoes_aleatorias(self):
        opcoes_upgrade = list(self.jogador.armas.keys())

        opcoes_novas = []
        if len(self.jogador.armas) < MAX_ARMAS:
            for id_total in ARMAS_REGISTRO.keys():
                if id_total not in self.jogador.armas:
                    opcoes_novas.append(id_total)

        pool_final = []

        upgrades_escolhidos = random.sample(opcoes_upgrade, min(2, len(opcoes_upgrade)))
        pool_final.extend(upgrades_escolhidos)

        vagas_restantes = 3 - len(pool_final)
        novas_escolhidas = random.sample(opcoes_novas, min(vagas_restantes, len(opcoes_novas)))
        pool_final.extend(novas_escolhidas)

        vagas_restantes = 3 - len(pool_final)
        if vagas_restantes > 0:
            upgrades_restantes = [u for u in opcoes_upgrade if u not in pool_final]
            mais_upgrades = random.sample(upgrades_restantes, min(vagas_restantes, len(upgrades_restantes)))
            pool_final.extend(mais_upgrades)

        return pool_final

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


class OpcaoDeUpgrade:
    """Só guarda os dados de uma opção (id, rect, referência ao jogador).
    Não desenha nada — draw.py lê esses dados pra renderizar."""

    def __init__(self, id_arma, retangulo, jogador):
        self.id = id_arma
        self.rect = retangulo
        self.jogador = jogador
        self.dados = ARMAS_REGISTRO[id_arma]

        self.font_path = join('assets', 'fonts', 'orbitron', 'Orbitron-ExtraBold.ttf')
        self.font_path2 = join('assets', 'fonts', 'orbitron', 'Orbitron-Medium.ttf')
        try:
            if os.path.exists(self.font_path):
                self.font_title = pygame.font.Font(self.font_path, 20)
                self.font_text = pygame.font.Font(self.font_path2, 14)
            else:
                self.font = pygame.font.SysFont('Consolas', 20, bold=True)
                self.font_text = pygame.font.Font('Consolas', 18)
        except:
            self.font_title = pygame.font.SysFont('Consolas', 18, bold=True)
            self.font_text = pygame.font.Font('Consolas', 18)

        self.fonte_titulo = self.font_title
        self.fonte_texto = self.font_text