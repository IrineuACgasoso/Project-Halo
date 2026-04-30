import pygame
from source.player.levelup import DADOS_ARMAS
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
        if not g.tela_de_upgrade_ativa:
            return
        escolha_idx = g.tela_de_upgrade_ativa.handle_event(evento)
        if escolha_idx is None:
            return

        nome_da_arma = g.tela_de_upgrade_ativa.nomes_das_opcoes[escolha_idx]

        if nome_da_arma in g.player.armas:
            g.player.armas[nome_da_arma].upgrade()
        else:
            dados = DADOS_ARMAS[nome_da_arma]

            # Mapeia nome do grupo -> objeto real no entity_manager
            _grupos_map = {
                'all_sprites':               entity_manager.all_sprites,
                'inimigos_grupo':            entity_manager.inimigos_grupo,
                'projeteis_jogador_grupo':   entity_manager.projeteis_jogador_grupo,
                'projeteis_inimigos_grupo':  entity_manager.projeteis_inimigos_grupo,
                'items_grupo':               entity_manager.items_grupo,
                'auras_grupo':               entity_manager.auras_grupo,
            }
            grupos = tuple(_grupos_map[ng] for ng in dados['grupos'])
            nova_arma = dados['classe'](g.player, grupos, g, criar_sprite=True)
            if hasattr(nova_arma, 'equipar'):
                nova_arma.equipar()
            g.player.armas[nome_da_arma] = nova_arma

        g.estado_do_jogo = 'jogando'
        g.tela_de_upgrade_ativa = None

    def _colaboradores(self, evento):
        g = self.game
        if g.tela_colaboradores.handle_event(evento) == 'sair':
            g.estado_do_jogo = 'menu_principal'

    def _ranking(self, evento):
        g = self.game
        if g.ranking.handle_event(evento) == 'exit_to_menu':
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
