import pygame
from source.systems.levelup import ARMAS_REGISTRO
from source.systems.entitymanager import entity_manager


class EventManager:
    """
    Responsável exclusivamente por capturar e despachar eventos pygame.
    O Game.eventos() vira uma linha: self.event_manager.processar()
    """

    def __init__(self, game):
        self.game = game
        # Mapeia estado -> método handler
        self._dispatch = {
            'menu_principal': self._menu_principal,
            'jogando':        self._jogando,
            'pausa':          self._pausa,
            'level_up':       self._level_up,
            'configuracoes':  self._configuracoes,
            'colaboradores':  self._colaboradores,
            'ranking':        self._ranking,
            'game_over':      self._game_over,
        }

    def processar(self):
        g = self.game
        handler = self._dispatch.get(g.estado_do_jogo)

        for evento in pygame.event.get():
            # Globais — sempre ativos
            if evento.type == pygame.QUIT:
                g.running = False
                return

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN and (evento.mod & pygame.KMOD_ALT):
                    pygame.display.toggle_fullscreen()

            # Delega para o handler do estado atual
            if handler:
                handler(evento)

    # ── Handlers por estado ──────────────────────────────────────────────────

    def _menu_principal(self, evento):
        g = self.game
        escolha = g.menu_principal.handle_event(evento)
        if escolha == 'START GAME':
            g.iniciar_novo_jogo()
        elif escolha == 'RANKING':
            g.estado_do_jogo = 'ranking'
        elif escolha == 'SETTINGS':
            g.estado_do_jogo = 'configuracoes'
        elif escolha == 'CREATORS':
            g.estado_do_jogo = 'colaboradores'
        elif escolha == 'QUIT':
            g.running = False
    
    def _jogando(self, evento):
        g = self.game
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            g.estado_do_jogo = 'pausa'

    def _pausa(self, evento):
        g = self.game
        escolha = g.menu_pausa.handle_event(evento)
        if escolha == 'RESUME':
            g.estado_do_jogo = 'jogando'
        elif escolha == 'EXIT TO MENU':
            g.estado_do_jogo = 'menu_principal'
            g.menu_principal = type(g.menu_principal)(g)  # Recria sem hardcode

    def _level_up(self, evento):
        g = self.game
        tela = g.tela_de_upgrade_ativa
        if not tela:
            return

        # handle_event devolve sempre o ID da arma (str) — os ramos "índice inteiro" antigos eram código morto.
        id_da_arma = tela.handle_event(evento)
        if id_da_arma is None:
            return

        self._aplicar_escolha_de_upgrade(id_da_arma)

        # Retorna o fluxo do gameplay e, se houver level-ups acumulados, abre a próxima tela.
        g.estado_do_jogo = 'jogando'
        g.tela_de_upgrade_ativa = None
        g.player.abrir_proxima_tela_de_upgrade()

    def _aplicar_escolha_de_upgrade(self, id_da_arma):
        g = self.game
        if id_da_arma in g.player.armas:
            g.player.armas[id_da_arma].upgrade()
            return

        dados = ARMAS_REGISTRO[id_da_arma]
        # Nome do grupo -> grupo real do entity_manager
        grupos = tuple(getattr(entity_manager, nome) for nome in dados.grupos)

        nova_arma = dados.classe(g.player, grupos, g, criar_sprite=True)
        if hasattr(nova_arma, 'equipar'):
            nova_arma.equipar()
        g.player.armas[id_da_arma] = nova_arma

    def _colaboradores(self, evento):
        g = self.game
        if g.tela_colaboradores.handle_event(evento) == 'sair':
            g.estado_do_jogo = 'menu_principal'

    def _ranking(self, evento):
        g = self.game
        if g.ranking.handle_event(evento) == 'exit_to_menu':
            g.estado_do_jogo = 'menu_principal'

    def _configuracoes(self, evento):
        g = self.game
        if g.tela_configuracoes.handle_event(evento) == 'sair':
            g.estado_do_jogo = 'menu_principal'

    def _game_over(self, evento):
        g = self.game
        escolha = g.tela_game_over.handle_event(evento)
        if escolha in ('RESTART MISSION', 'EXIT TO MENU'):
            if g.player:
                g.ranking.start_name_input(g.player.pontuacao)
            g.tela_game_over.som_tocado = False
            if escolha == 'RESTART MISSION':
                g.iniciar_novo_jogo()
            else:
                g.estado_do_jogo = 'menu_principal'
