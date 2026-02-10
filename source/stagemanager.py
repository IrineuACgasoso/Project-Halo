import pygame
from os.path import join
from mapmanager import Mapa
from entitymanager import entity_manager
from feats.effects import Portal
from spawner import Spawner

class StageManager:
    def __init__(self, game):
        self.game = game
        self.tela = game.tela
        
        # Controle de Fade
        self.fade_surface = pygame.Surface(self.tela.get_size())
        self.fade_surface.fill((0, 0, 0))
        self.fade_alpha = 0
        self.fade_velocidade = 300
        
        # Estados da Transição
        self.transicao_ativa = False
        self.fase_carregada = False

    def iniciar_transicao(self):
        if not self.transicao_ativa:
            self.transicao_ativa = True
            self.fase_carregada = False

    def update(self, delta_time):
        if not self.transicao_ativa: return

        # Fase 1: Escurecendo
        if not self.fase_carregada:
            self.fade_alpha += self.fade_velocidade * delta_time
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                self._trocar_dados_fase()
                self.fase_carregada = True
        
        # Fase 2: Clareando
        else:
            self.fade_alpha -= self.fade_velocidade * delta_time
            if self.fade_alpha <= 0:
                self.fade_alpha = 0
                self.transicao_ativa = False

    def _trocar_dados_fase(self):
        game = self.game
        game.fase_atual += 1
        
        # Limpeza
        for sprite in list(entity_manager.all_sprites):
            if sprite != game.player: sprite.kill()

        game.portal_atual = None             # Remove a referência do portal antigo
        game.spawnar_portal_em_breve = False # Garante que a flag de espera suma
        game.boss_atual = None
        
        # Novo Mapa
        caminho = join('assets', 'map', f'{game.fase_atual}', f'm{game.fase_atual}.tmj')
        game.mapa = Mapa(caminho, game.fase_atual, all_sprites=entity_manager.all_sprites)
        
        # Player
        nova_pos = game.mapa.get_player_spawn_pos()
        game.player.posicao = pygame.math.Vector2(nova_pos)
        game.player.hitbox.center = nova_pos
        game.player.rect.center = nova_pos

        # Reseta spawner
        game.boss_atual = None
        game.spawner = Spawner(game)
        

    def draw(self):
        if self.fade_alpha > 0:
            self.fade_surface.set_alpha(self.fade_alpha)
            self.tela.blit(self.fade_surface, (0, 0))