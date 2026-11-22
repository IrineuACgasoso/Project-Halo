import pygame
from source.systems.levelup import ARMAS_REGISTRO
from source.systems.estados import (MENU_PRINCIPAL, JOGANDO, PAUSA, CONFIGURACOES,
                                    COLABORADORES, RANKING)


class EventManager:
    """
    Captura os eventos pygame e os entrega ao handler do estado atual.
    O par (handler, desenho) de cada estado fica num registro único: `Game.telas`.
    """

    def __init__(self, game):
        self.game = game

    def processar(self):
        g = self.game
        tela = g.telas.get(g.estado_do_jogo)

        for evento in pygame.event.get():
            # Globais — sempre ativos
            if evento.type == pygame.QUIT:
                g.running = False
                return

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN and (evento.mod & pygame.KMOD_ALT):
                    pygame.display.toggle_fullscreen()

            # Delega para o handler do estado atual
            if tela:
                tela.evento(evento)

    # ── Handlers por estado ──────────────────────────────────────────────────

    def tratar_menu_principal(self, evento):
        g = self.game
        escolha = g.menu_principal.handle_event(evento)
        if escolha == 'START GAME':
            g.iniciar_novo_jogo()
        elif escolha == 'RANKING':
            g.mudar_estado(RANKING)
        elif escolha == 'SETTINGS':
            g.mudar_estado(CONFIGURACOES)
        elif escolha == 'CREATORS':
            g.mudar_estado(COLABORADORES)
        elif escolha == 'QUIT':
            g.running = False

    def tratar_jogando(self, evento):
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            self.game.mudar_estado(PAUSA)

    def tratar_pausa(self, evento):
        g = self.game
        escolha = g.menu_pausa.handle_event(evento)
        if escolha == 'RESUME':
            g.mudar_estado(JOGANDO)
        elif escolha == 'EXIT TO MENU':
            g.mudar_estado(MENU_PRINCIPAL)
            g.menu_principal = type(g.menu_principal)(g)  # Recria sem hardcode

    def tratar_level_up(self, evento):
        g = self.game
        tela = g.sessao.tela_de_upgrade_ativa
        if not tela:
            return

        # handle_event devolve sempre o ID da arma (str) — os ramos "índice inteiro" antigos eram código morto.
        id_da_arma = tela.handle_event(evento)
        if id_da_arma is None:
            return

        self._aplicar_escolha_de_upgrade(id_da_arma)

        # Retorna o fluxo do gameplay e, se houver level-ups acumulados, abre a próxima tela.
        g.mudar_estado(JOGANDO)
        g.sessao.tela_de_upgrade_ativa = None
        g.player.abrir_proxima_tela_de_upgrade()

    def _aplicar_escolha_de_upgrade(self, id_da_arma):
        g = self.game
        if id_da_arma in g.player.armas:
            g.player.armas[id_da_arma].upgrade()
            return

        nova_arma = ARMAS_REGISTRO[id_da_arma].classe(g.player, g)
        if hasattr(nova_arma, 'equipar'):
            nova_arma.equipar()
        g.player.armas[id_da_arma] = nova_arma

    def tratar_colaboradores(self, evento):
        g = self.game
        if g.tela_colaboradores.handle_event(evento) == 'sair':
            g.mudar_estado(MENU_PRINCIPAL)

    def tratar_ranking(self, evento):
        g = self.game
        if g.ranking.handle_event(evento) == 'exit_to_menu':
            g.mudar_estado(MENU_PRINCIPAL)

    def tratar_configuracoes(self, evento):
        g = self.game
        if g.tela_configuracoes.handle_event(evento) == 'sair':
            g.mudar_estado(MENU_PRINCIPAL)

    def tratar_game_over(self, evento):
        g = self.game
        escolha = g.tela_game_over.handle_event(evento)
        if escolha in ('RESTART MISSION', 'EXIT TO MENU'):
            if g.player:
                g.ranking.start_name_input(g.player.pontuacao)
            g.tela_game_over.som_tocado = False
            if escolha == 'RESTART MISSION':
                g.iniciar_novo_jogo()
            else:
                g.mudar_estado(MENU_PRINCIPAL)
