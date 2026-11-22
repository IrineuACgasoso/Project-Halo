import pygame

from source.windows.settings import largura_tela, altura_tela
from .menu_draw import MenuDraw

DICA_CHEATS = 'L: SUBIR DE NIVEL   P: PORTAL   B: BOSS'


class MenuPausa(MenuDraw):
    def __init__(self, game):
        self.game = game
        if hasattr(game.menu_principal, 'font'):
            self.font = game.menu_principal.font
        else:
            self.font = pygame.font.SysFont(None, 48)
        self.fonte_dica = pygame.font.SysFont('Consolas', 22, bold=True)
        self._dica = None   # renderizada no 1º uso

        # IDs devolvidos por handle_event; o texto na tela vem de rotulo()
        self.opcoes = ["RESUME", "CHEATS", "EXIT TO MENU"]
        self.selecionada = 0
        self.timer = 0

    def rotulo(self, opcao):
        if opcao == 'CHEATS':
            return 'DESATIVAR CHEATS' if self.game.cheats else 'ATIVAR CHEATS'
        return opcao

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                self.selecionada = (self.selecionada - 1) % len(self.opcoes)
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                self.selecionada = (self.selecionada + 1) % len(self.opcoes)
            elif event.key == pygame.K_RETURN:
                return self.opcoes[self.selecionada]
        return None

    def draw(self, tela):
        self.timer += 0.01
        self.draw_overlay(tela)

        titulo = self.font.render("SYSTEM PAUSED", True, (0, 255, 255))
        rect_t = titulo.get_rect(center=(largura_tela//2, altura_tela//2 - 100))
        tela.blit(titulo, rect_t)

        for i, opcao in enumerate(self.opcoes):
            self.draw_glow_text(tela, self.rotulo(opcao), largura_tela//2, altura_tela//2 + i * 65,
                                i == self.selecionada)

        if self.game.cheats:
            if self._dica is None:
                self._dica = self.fonte_dica.render(DICA_CHEATS, True, (255, 200, 60))
            y = altura_tela//2 + len(self.opcoes) * 65 + 10
            tela.blit(self._dica, self._dica.get_rect(center=(largura_tela//2, y)))
