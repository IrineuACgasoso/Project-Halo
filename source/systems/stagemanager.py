import pygame
from source.systems.mapmanager import Mapa
from source.systems.entitymanager import entity_manager
from source.systems.eventos import eventos, FASE_TROCADA
from source.utils.paths import path
from source.systems.spawner import Spawner
from source.feats.buddies import Companheiro

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
        if self.transicao_ativa:
            return
        # Última fase com mapa: não há para onde ir -> encerra a campanha em vez de crashar
        if not self.game.existe_proxima_fase():
            self.game.finalizar_campanha()
            return
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
        game.sessao.fase_atual += 1
        
        # Só sobrevive quem declara `sobrevive_troca_de_fase = True` na classe (roteiro E5):
        # jogador, companheiros e aura do MK2. O resto (inimigos, projéteis, itens, portal) sai.
        sobreviventes = []
        for sprite in list(entity_manager.all_sprites):
            if getattr(sprite, 'sobrevive_troca_de_fase', False):
                sobreviventes.append(sprite)
            else:
                sprite.kill()

        game.sessao.portal_atual = None             # Remove a referência do portal antigo
        game.sessao.spawnar_portal_em_breve = False # Garante que a flag de espera suma
        game.sessao.boss_atual = None
        
        # Novo Mapa
        caminho = path('assets', 'img', 'map', f'{game.sessao.fase_atual}', f'm{game.sessao.fase_atual}.tmj')
        game.mapa = Mapa(caminho, game.sessao.fase_atual, all_sprites=entity_manager.all_sprites)
        # A câmera guardava o mapa ANTIGO: limites errados na fase nova (jogador saía da tela).
        game.camera.mapa = game.mapa
        game.camera.shake_timer = 0
        
        # Player
        nova_pos = game.mapa.get_player_spawn_pos()
        game.player.posicao = pygame.math.Vector2(nova_pos)
        game.player.hitbox.center = nova_pos
        game.player.rect.center = nova_pos
        game.camera.update(game.player.posicao)

        # Companheiros junto do jogador, no spawn do mapa NOVO (antes liam o do mapa antigo e
        # cruzavam o mapa voando até ele)
        for sprite in sobreviventes:
            if isinstance(sprite, Companheiro):
                sprite.posicao = pygame.math.Vector2(nova_pos)
                sprite.rect.center = nova_pos

        # Reseta spawner
        game.spawner = Spawner(game)
        eventos.emitir(FASE_TROCADA, fase=game.sessao.fase_atual)
        

    def draw(self):
        if self.fade_alpha > 0:
            self.fade_surface.set_alpha(self.fade_alpha)
            self.tela.blit(self.fade_surface, (0, 0))