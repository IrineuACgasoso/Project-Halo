import pygame
import random
from os.path import join
# WINDOWS
from source.windows.settings import *
from source.windows.menu import *
from source.windows.colaboradores import TelaColaboradores
from source.windows.ranking import Ranking 
# SYSTEMS
from source.systems.mapmanager import Mapa
from source.systems.camera import Camera
from source.systems.hud import HUD
from source.systems.collision import CollisionManager 
from source.systems.stagemanager import StageManager
from source.systems.spawner import Spawner
from source.systems.entitymanager import entity_manager
from source.systems.eventmanager import EventManager
# FEATS
from source.feats.buddies import *
from source.feats.effects import Portal
from source.feats.assets import path
# PLAYER
from source.player.weapons import *
from source.player.levelup import *
from source.player.player import Player 




class Game:
    def __init__(self, tela):
        # Variaveis de controle de tempo e fase
        self.tela = tela
        self.running = True
        self.clock = pygame.time.Clock()

        # Estado
        self.estado_do_jogo = 'menu_principal'
        self.player = None
        self.boss_atual = None
        self.portal_atual = None

        # Sistemas que vivem para sempre (não resetam entre jogos)
        self._inicializar_sistemas_permanentes()

        # EventManager gerencia o estado da tela
        self.event_manager = EventManager(self)


    def _inicializar_sistemas_permanentes(self):
        """Sistemas que existem desde o início e nunca são recriados."""
        self.menu_principal     = MenuPrincipal(self)
        self.menu_pausa         = MenuPausa(self)
        self.tela_game_over     = TelaGameOver(self)
        self.tela_colaboradores = TelaColaboradores(self)
        self.ranking            = Ranking(self)
        self.hud                = HUD(self)
        self.collision_manager  = CollisionManager(self)

        # Mapa inicial (fase 0) — só para o construtor não explodir
        caminho = path('assets', 'img', 'map', '0', 'm0.tmj')
        self.mapa   = Mapa(caminho, 0)
        self.camera = Camera(largura_tela, altura_tela, self.mapa)

    #=================== FUNÇÕES DE INÍCIO/REINÍCIO =======================================

    def _resetar_estado_jogo(self):
        """
        Zera TUDO que pertence a uma sessão de jogo.
        Chamado tanto na primeira partida quanto no restart.
        """
        # 1. Limpa todos os grupos de sprite
        entity_manager.all_sprites.empty()
        entity_manager.inimigos_grupo.empty()
        entity_manager.items_grupo.empty()
        entity_manager.projeteis_jogador_grupo.empty()
        entity_manager.projeteis_inimigos_grupo.empty()
        entity_manager.auras_grupo.empty()          

        # 2. Variáveis de sessão
        self.timer_jogo              = 0
        self.fase_atual              = 0
        self.boss_atual              = None
        self.portal_atual            = None          
        self.spawnar_portal_em_breve = False         
        self.timer_portal            = 0             
        self.tela_de_upgrade_ativa   = None          
        self.gravemind_reborns       = 3
        self.invocacao_protogravemind = 0


    def iniciar_novo_jogo(self):
        self._resetar_estado_jogo()

        # Mapa e câmera — recriados juntos (câmera depende do mapa)
        caminho = path('assets', 'img', 'map', '0', 'm0.tmj')
        self.mapa   = Mapa(caminho, 0, all_sprites=entity_manager.all_sprites)
        self.camera = Camera(largura_tela, altura_tela, self.mapa)  # ← estava faltando

        # Player
        pos_inicial = self.mapa.get_player_spawn_pos()
        self.player = Player(pos_inicial, entity_manager.all_sprites, self)
        entity_manager.player = self.player

        # Arma inicial
        rifle = RifleAssalto(
            jogador=self.player,
            grupos=(entity_manager.all_sprites,
                    entity_manager.projeteis_jogador_grupo,
                    entity_manager.inimigos_grupo),
            game=self
        )
        self.player.armas['Rifle de Assalto'] = rifle

        # Spawner — depois do player para não explodir no primeiro spawn
        self.spawner      = Spawner(self)
        self.stage_manager = StageManager(self)

        self.estado_do_jogo = 'jogando'

        # Aliases para compatibilidade (stagemanager, hud, etc ainda usam self.X)
        self.all_sprites              = entity_manager.all_sprites
        self.inimigos_grupo           = entity_manager.inimigos_grupo
        self.projeteis_jogador_grupo  = entity_manager.projeteis_jogador_grupo
        self.projeteis_inimigos_grupo = entity_manager.projeteis_inimigos_grupo
        self.items_grupo              = entity_manager.items_grupo
        self.auras_grupo              = entity_manager.auras_grupo

    #================= FUNÇÕES DO GAME ==========================================================
            
    def eventos(self):
        self.event_manager.processar()


    def update(self, delta_time):
        if self.estado_do_jogo != 'jogando':
            return

        agora = pygame.time.get_ticks()

        # Portal
        if self.spawnar_portal_em_breve:
            if agora - self.timer_portal >= 2000:
                self.portal_atual = Portal(self.mapa.portal_pos, entity_manager.all_sprites)
                self.spawnar_portal_em_breve = False

        # Boss morreu
        if self.boss_atual and not self.boss_atual.alive():
            self.boss_derrotado()

        # Colisão com portal
        if self.portal_atual:
            ox = self.portal_atual.rect.x - self.player.rect.x
            oy = self.portal_atual.rect.y - self.player.rect.y
            if self.player.mask.overlap(self.portal_atual.mask, (ox, oy)):
                if not self.stage_manager.transicao_ativa:
                    self.stage_manager.iniciar_transicao()

        # Timer e spawner só rodam sem boss nem transição ativa
        jogo_livre = (
            not self.stage_manager.transicao_ativa
            and not self.boss_atual
            and not self.spawnar_portal_em_breve
            and not self.portal_atual
        )
        if jogo_livre:
            self.timer_jogo += delta_time
            self.spawner.update(delta_time)

        # Atualiza entidades
        if self.player:
            paredes = self.mapa.get_paredes_proximas(self.player.posicao)
            self.player.update(delta_time, paredes)
            self.camera.update(self.player.posicao)

            for arma in self.player.armas.values():
                arma.update(delta_time)

            for sprite in entity_manager.all_sprites:
                if sprite == self.player:
                    continue
                if sprite in entity_manager.inimigos_grupo:
                    sprite.update(delta_time, paredes)
                else:
                    sprite.update(delta_time)

        self.collision_manager.update(delta_time)
        self.stage_manager.update(delta_time)

        # Game over
        if self.player.vida_atual <= 0:
            self._calcular_pontuacao_final()
            self.estado_do_jogo = 'game_over'
            pygame.mixer.music.pause()


    def _calcular_pontuacao_final(self):
        """Extraído do update para não poluir o loop principal."""
        p = self.player
        p.pontuacao += p.experiencia_atual
        pesos = {'exp_shard': 1, 'big_shard': 2, 'life_orb': 3, 'cafe': 10}
        for tipo, peso in pesos.items():
            p.pontuacao += p.coletaveis.get(tipo, 0) * peso


    def draw(self):
        self.tela.fill('black')
        if self.estado_do_jogo == "menu_principal":
            self.menu_principal.draw(self.tela)

        elif self.estado_do_jogo == 'jogando':
            deslocamento = self.camera.offset + self.camera.shake_offset
            self.mapa.draw(self.tela, deslocamento)
            # Função para Debug de Tiled
            self.mapa.draw_debug(self.tela, deslocamento)
            # Itera por todos os sprites e desenha cada um
            for sprite in sorted(entity_manager.all_sprites, key=lambda s: s.rect.centery):
                if hasattr(sprite, 'draw'):
                    sprite.draw(self.tela, deslocamento)
                else:
                    self.tela.blit(sprite.image, pygame.math.Vector2(sprite.rect.topleft) - deslocamento)
            
            # Desenha lasers por cima dos sprites
            for inimigo in entity_manager.inimigos_grupo:
                # Verifica se o inimigo tem o método draw_laser (Sentinel e Scarab terão)
                if hasattr(inimigo, 'draw_laser'):
                    inimigo.draw_laser(self.tela, deslocamento)
                    
            self.hud.draw(self.tela)

            self.stage_manager.draw()
            

        elif self.estado_do_jogo == 'pausa':
            
            entity_manager.all_sprites.draw(self.tela)
            self.menu_pausa.draw(self.tela)

        elif self.estado_do_jogo == 'colaboradores':
            self.tela_colaboradores.draw(self.tela)

        elif self.estado_do_jogo == 'ranking':
            self.ranking.draw(self.tela)

        elif self.estado_do_jogo == "game_over":
            self.tela_game_over.draw(self.tela)

        elif self.estado_do_jogo == "level_up":
            entity_manager.all_sprites.draw(self.tela)
            self.hud.draw(self.tela)
            self.tela_de_upgrade_ativa.draw(self.tela)

        pygame.display.update()

    def boss_derrotado(self):
        print(f"Boss da fase {self.fase_atual} derrotado!")
        self.boss_atual = None
        self.spawnar_portal_em_breve = True
        self.timer_portal = pygame.time.get_ticks()

    def run(self):
        while self.running:
            delta_time = self.clock.tick(fps) / 1000
            self.eventos()
            self.update(delta_time)
            self.draw()