import pygame

from source.systems.entitymanager import entity_manager


class PlayerInput:
    """O jogador não lê o teclado: o `Game` entrega o `ComandoJogador` do passo em `self.comando`
    (systems/entrada.py, roteiro E3)."""

    def aplicar_direcao_do_comando(self):
        # Direita = +x, baixo = +y. Normaliza para não andar mais rápido na diagonal.
        self.direcao.update(self.comando.direcao)
        if self.direcao != (0, 0):
            self.direcao.normalize_ip()

    # --- ÁREA DOS HACKS ---
    def executar_hacks(self):
        # O Teclado só produz hacks com os cheats ligados (MCE_DEBUG=1 ou o botão da pausa).
        comando = self.comando

        # Hack L: Level Up
        if comando.hack_nivel:
            falta = self.experiencia_level_up - self.experiencia_atual
            self.ganhar_xp(falta)

        # Hack P: Spawnar Portal (Instant Exit)
        elif comando.hack_portal:
            # Verifica se o jogo já tem um portal ativo.
            if self.game.sessao.portal_atual is None:
                # Importação local para evitar erro circular (Player importar Portal e Portal importar Player)
                from source.feats.effects import Portal

                offset = 50 if self.estado_animacao == 'right' else -50
                pos_portal = self.posicao + pygame.math.Vector2(offset, 0)

                novo_portal = Portal(pos_portal, entity_manager.all_sprites)
                self.game.sessao.portal_atual = novo_portal

        elif comando.hack_boss:
            if self.game.sessao.boss_atual is None:
                self.game.spawner.forcar_proximo_boss()
