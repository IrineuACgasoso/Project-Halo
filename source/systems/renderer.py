"""
source/systems/renderer.py

Classe responsável por toda a parte de DESENHO do jogo.
apenas organiza e blinda o código de renderização contra falhas comuns
(sprite sem imagem, superfície inválida, atributo faltando, etc).
"""

import pygame


class Renderer:
    """
    Encapsula o desenho de cada estado do jogo.

    Uso no Game:
        self.renderer = Renderer(self)
        ...
        def draw(self):
            self.renderer.draw()
    """
    def __init__(self, game):
        self.game = game

    def draw(self):
        game = self.game
        tela = game.tela

        tela.fill('black')

        estado = game.estado_do_jogo
        metodo = self._dispatch.get(estado)

        if metodo is None:
            self._draw_estado_desconhecido(estado)
        else:
            try:
                metodo(self)
            except Exception as e:
                # Nunca deixamos uma falha de desenho derrubar o jogo.
                self._log_erro(estado, e)
                self._draw_fallback()

        pygame.display.update()

    # ------------------------------------------------------------------ #
    # ESTADOS
    # ------------------------------------------------------------------ #
    def _draw_menu_principal(self):
        self.game.menu_principal.draw(self.game.tela)

    def _draw_jogando(self):
        game = self.game
        tela = game.tela

        deslocamento = game.camera.offset + game.camera.shake_offset

        game.mapa.draw(tela, deslocamento)
        game.mapa.draw_debug(tela, deslocamento)

        self._draw_sprites(deslocamento)
        self._draw_efeitos_inimigos(deslocamento)

        game.hud.draw(tela)
        game.stage_manager.draw()

    def _draw_pausa(self):
        from source.systems.entitymanager import entity_manager
        game = self.game
        self._draw_grupo_seguro(entity_manager.all_sprites)
        game.menu_pausa.draw(game.tela)

    def _draw_colaboradores(self):
        self.game.tela_colaboradores.draw(self.game.tela)

    def _draw_ranking(self):
        self.game.ranking.draw(self.game.tela)

    def _draw_configuracoes(self):
        self.game.tela_configuracoes.draw(self.game.tela)

    def _draw_game_over(self):
        self.game.tela_game_over.draw(self.game.tela)

    def _draw_level_up(self):
        from source.systems.entitymanager import entity_manager
        game = self.game
        self._draw_grupo_seguro(entity_manager.all_sprites)
        game.hud.draw(game.tela)
        if game.tela_de_upgrade_ativa is not None:
            game.tela_de_upgrade_ativa.draw(game.tela)

    # Mapa estado -> método (montado no fim da classe)
    _dispatch = {}

    # ------------------------------------------------------------------ #
    # HELPERS DE DESENHO (com blindagem individual por sprite)
    # ------------------------------------------------------------------ #
    def _draw_sprites(self, deslocamento):
        """Desenha todos os sprites ordenados por profundidade (centery).

        Cada sprite é desenhado isoladamente: se um sprite específico
        falhar (imagem None, rect ausente, etc), pulamos só ele em vez
        de quebrar o frame inteiro.
        """
        from source.systems.entitymanager import entity_manager

        try:
            sprites_ordenados = sorted(
                entity_manager.all_sprites,
                key=lambda s: getattr(s, 'rect', None).centery
                if getattr(s, 'rect', None) else 0
            )
        except Exception as e:
            self._log_erro('ordenacao_sprites', e)
            sprites_ordenados = list(entity_manager.all_sprites)

        tela = self.game.tela
        for sprite in sprites_ordenados:
            try:
                if hasattr(sprite, 'draw'):
                    sprite.draw(tela, deslocamento)
                elif getattr(sprite, 'image', None) is not None and hasattr(sprite, 'rect'):
                    tela.blit(
                        sprite.image,
                        pygame.math.Vector2(sprite.rect.topleft) - deslocamento
                    )
                # sprite sem image/draw: ignora silenciosamente (nada a desenhar)
            except Exception as e:
                self._log_erro(f'sprite:{sprite.__class__.__name__}', e)
                continue

    def _draw_efeitos_inimigos(self, deslocamento):
        """Lasers e extras de inimigos (Sentinel, Scarab, Boss...)."""
        from source.systems.entitymanager import entity_manager

        tela = self.game.tela
        for inimigo in entity_manager.inimigos_grupo:
            try:
                if hasattr(inimigo, 'draw_laser'):
                    inimigo.draw_laser(tela, deslocamento)
            except Exception as e:
                self._log_erro(f'draw_laser:{inimigo.__class__.__name__}', e)

            try:
                if hasattr(inimigo, 'draw_extras'):
                    inimigo.draw_extras(tela, deslocamento)
            except Exception as e:
                self._log_erro(f'draw_extras:{inimigo.__class__.__name__}', e)

    def _draw_grupo_seguro(self, grupo):
        try:
            grupo.draw(self.game.tela)
        except Exception as e:
            self._log_erro('draw_grupo', e)

    # ------------------------------------------------------------------ #
    # FALLBACK / LOG
    # ------------------------------------------------------------------ #
    def _draw_estado_desconhecido(self, estado):
        """Estado sem tela associada: não trava o jogo, só avisa em tela."""
        self._log_erro('estado_desconhecido', f"estado_do_jogo='{estado}' sem draw definido")
        self._draw_fallback(f"Estado desconhecido: {estado}")

    def _draw_fallback(self, mensagem="Erro ao renderizar"):
        """Tela mínima de segurança, para nunca ficar com frame corrompido."""
        try:
            fonte = pygame.font.Font(None, 28)
            texto = fonte.render(mensagem, True, (255, 60, 60))
            self.game.tela.blit(texto, (20, 20))
        except Exception:
            # Se até o fallback falhar, só deixamos a tela preta mesmo.
            pass

    def _log_erro(self, contexto, erro):
        print(f"[Renderer] Falha em '{contexto}': {erro}")


# Registro do dispatch de estados (feito fora do corpo da classe para
# manter os métodos privados legíveis acima).
Renderer._dispatch = {
    'menu_principal': Renderer._draw_menu_principal,
    'jogando':        Renderer._draw_jogando,
    'pausa':          Renderer._draw_pausa,
    'colaboradores':  Renderer._draw_colaboradores,
    'ranking':        Renderer._draw_ranking,
    'configuracoes':  Renderer._draw_configuracoes,
    'game_over':      Renderer._draw_game_over,
    'level_up':       Renderer._draw_level_up,
}