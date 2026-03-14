import pygame
import random
from os.path import join
from settings import *
from player import Player 
from menu import *
from systems.spawner import Spawner
from systems.entitymanager import entity_manager
from feats.weapon import *
from feats.effects import Portal
from colaboradores import TelaColaboradores
from ranking import Ranking 
from levelup import *
from systems.mapmanager import Mapa
from systems.camera import Camera
from systems.hud import HUD
from systems.collision import CollisionManager 
from systems.stagemanager import StageManager
from enemies.standard.sentinel import Sentinel



class Game:
    def __init__(self, tela):
        # Variaveis de controle de tempo e fase
        self.tela = tela
        self.running = True
        self.clock = pygame.time.Clock()
        self.estado_do_jogo = "menu_principal"
        self.timer_jogo = 0  # Tempo em segundos
        self.fase_atual = 0
        self.boss_atual = None

        # Sprites e grupos
        self.all_sprites = entity_manager.all_sprites
        self.inimigos_grupo = entity_manager.inimigos_grupo
        self.auras_grupo = entity_manager.auras_grupo
        self.inimigos_grupo = entity_manager.inimigos_grupo
        self.projeteis_jogador_grupo = entity_manager.projeteis_jogador_grupo
        self.projeteis_inimigos_grupo = entity_manager.projeteis_inimigos_grupo
        self.item_group = entity_manager.item_group

        # Menus
        self.menu_principal = MenuPrincipal(self)
        self.menu_pausa = MenuPausa(self)
        self.tela_game_over = TelaGameOver(self)
        self.tela_colaboradores = TelaColaboradores(self)
        self.ranking = Ranking(self)
        self.tela_colaboradores = TelaColaboradores(self)

        # Player e HUD
        self.player = None
        self.hud = HUD(self)
        self.tela_de_upgrade_ativa = None
        self.buff = False

        # Collision Sys
        self.collision_manager = CollisionManager(self)

        # Mapa 
        self.mapa = None # Inicialize o mapa como None
        self.caminho_mapa = join(f'assets', 'map', f'{self.fase_atual}', f'm{self.fase_atual}.tmj')
        self.mapa = Mapa(self.caminho_mapa, self.fase_atual)
        self.camera = Camera(largura_tela, altura_tela, self.mapa)
        self.largura_mapa_pixels = 0
        self.altura_mapa_pixels = 0

        # Controle de spawn
        self.spawner = Spawner(self) # Inicializa o spawner
        self.gravemind_reborns = 3        
        self.invocacao_protogravemind = 0

        # Mudança de Fase
        self.stage_manager = StageManager(self) # Centraliza transições
        self.portal_atual = None
        self.timer_portal = 0
        self.spawnar_portal_em_breve = False


    def boss_derrotado(self):
        print(f"Boss da fase {self.fase_atual} derrotado!")
        self.boss_atual = None
        self.spawnar_portal_em_breve = True
        self.timer_portal = pygame.time.get_ticks()
            
    def eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.running = False
            
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN and (evento.mod & pygame.KMOD_ALT):
                    pygame.display.toggle_fullscreen()

            # --- MENU PRINCIPAL ---
            if self.estado_do_jogo == "menu_principal":
                escolha = self.menu_principal.handle_event(evento)
                if escolha == 'START GAME':
                    self.iniciar_novo_jogo()
                elif escolha == 'RANKING':
                    self.estado_do_jogo = 'ranking'
                elif escolha == 'CREATORS':
                    self.estado_do_jogo = 'colaboradores'
                elif escolha == 'QUIT':
                    self.running = False

            # --- JOGANDO ---
            elif self.estado_do_jogo == "jogando":
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    self.estado_do_jogo = "pausa"

            # --- PAUSA (CORRIGIDO) ---
            elif self.estado_do_jogo == "pausa":
                escolha = self.menu_pausa.handle_event(evento)
                
                # As strings devem bater com as opções definidas em MenuPausa
                if escolha == "RESUME":
                    self.estado_do_jogo = "jogando"
                elif escolha == "EXIT TO MENU":
                    self.estado_do_jogo = "menu_principal"
                    # Opcional: Reiniciar o menu principal para resetar animações
                    self.menu_principal = MenuPrincipal(self)

            # --- LEVEL UP ---
            elif self.estado_do_jogo == 'level_up':
                if self.tela_de_upgrade_ativa:
                    escolha_idx = self.tela_de_upgrade_ativa.handle_event(evento)
                    if escolha_idx is not None and escolha_idx < len(self.tela_de_upgrade_ativa.opcoes_de_armas_obj):
                        arma_escolhida = self.tela_de_upgrade_ativa.opcoes_de_armas_obj[escolha_idx]
                        nome_da_arma = arma_escolhida.nome
                        
                        if nome_da_arma in self.player.armas:
                            self.player.armas[nome_da_arma].upgrade()
                        else:
                            self.player.armas[nome_da_arma] = arma_escolhida 
                            arma_escolhida.equipar()
                        
                        self.estado_do_jogo = 'jogando'
                        self.tela_de_upgrade_ativa = None
            
            # --- COLABORADORES ---
            elif self.estado_do_jogo == 'colaboradores':
                action = self.tela_colaboradores.handle_event(evento)
                if action == 'sair':
                    self.estado_do_jogo = 'menu_principal'
            
            # --- RANKING ---
            elif self.estado_do_jogo == 'ranking':
                action = self.ranking.handle_event(evento)
                if action == 'exit_to_menu':
                    self.estado_do_jogo = 'menu_principal'

            # --- GAME OVER (CORRIGIDO) ---
            elif self.estado_do_jogo == "game_over":
                escolha = self.tela_game_over.handle_event(evento)
                
                # Strings devem bater com TelaGameOver.opcoes
                if escolha == "RESTART MISSION":
                    if hasattr(self, 'player') and self.player:
                        self.ranking.start_name_input(self.player.pontuacao)
                    self.iniciar_novo_jogo()
                    self.tela_game_over.som_tocado = False
                    
                elif escolha == "EXIT TO MENU":
                    if hasattr(self, 'player') and self.player:
                        self.ranking.start_name_input(self.player.pontuacao)
                    self.estado_do_jogo = "menu_principal"
                    self.tela_game_over.som_tocado = False

    def update(self, delta_time):
        if self.estado_do_jogo == "jogando":
            agora = pygame.time.get_ticks()

            # Lógica do Timer do Portal
            if self.spawnar_portal_em_breve:
                if agora - self.timer_portal >= 2000: # 2000ms = 2 segundos
                    self.portal_atual = Portal(self.mapa.portal_pos, self.all_sprites)
                    self.spawnar_portal_em_breve = False
                
            # Verificamos se o boss morreu para limpar a referência
            if self.boss_atual and not self.boss_atual.alive():
                self.boss_derrotado() # Chama o método que incrementa fase e carrega mapa
            
            # Checar transição de fase via Portal
            # Verificação de Colisão com Máscara
            if self.portal_atual:
                # Calcula o deslocamento (offset) entre o player e o portal
                offset_x = self.portal_atual.rect.x - self.player.rect.x
                offset_y = self.portal_atual.rect.y - self.player.rect.y
                
                # Verifica se as máscaras se sobrepõem
                if self.player.mask.overlap(self.portal_atual.mask, (offset_x, offset_y)):
                    if not self.stage_manager.transicao_ativa:
                        self.stage_manager.iniciar_transicao()

            # SÓ INCREMENTA O TIMER SE A FASE ESTIVER CARREGADA
            if not self.stage_manager.transicao_ativa and not self.boss_atual \
                and not self.spawnar_portal_em_breve and not self.portal_atual:
                self.timer_jogo += delta_time
                self.hud.desenhar_timer(self.tela)
                self.spawner.update(delta_time) # Spawner só roda sem boss                

            if self.player:
                #paredes_ativas = self.mapa.paredes   
                paredes_ativas = self.mapa.get_paredes_proximas(self.player.posicao)             
                self.player.update(delta_time, paredes_ativas) 
                self.camera.update(self.player.posicao)               
                for arma in self.player.armas.values():
                    arma.update(delta_time)
                for sprite in self.all_sprites:
                    if sprite != self.player:
                        # Se for um inimigo, enviamos as paredes
                        if sprite in self.inimigos_grupo:
                            sprite.update(delta_time, paredes_ativas)
                        else:
                            # Projéteis e itens geralmente não precisam colidir com paredes (ou tem lógica própria)
                            sprite.update(delta_time)
            
            self.collision_manager.update(delta_time)

            self.stage_manager.update(delta_time)

            if self.player.vida_atual <= 0:
                #atualizacao pos morte para o ranking
                self.player.pontuacao += self.player.experiencia_atual
                for tipo, contagem in self.player.coletaveis.items():
                    if tipo == 'exp_shard':
                        self.player.pontuacao += contagem
                    elif tipo == 'big_shard':
                        self.player.pontuacao += contagem * 2
                    elif tipo == 'life_orb':
                        self.player.pontuacao += contagem * 3
                    elif tipo == 'cafe':
                        self.player.pontuacao += 10
                self.estado_do_jogo = 'game_over'
                pygame.mixer.music.pause()  # pausa a música no game over

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
            for sprite in sorted(self.all_sprites, key=lambda s: s.rect.centery):
                if hasattr(sprite, 'draw'):
                    sprite.draw(self.tela, deslocamento)
                else:
                    self.tela.blit(sprite.image, pygame.math.Vector2(sprite.rect.topleft) - deslocamento)
            
            # Desenha lasers por cima dos sprites
            for inimigo in self.inimigos_grupo:
                # Verifica se o inimigo tem o método draw_laser (Sentinel e Scarab terão)
                if hasattr(inimigo, 'draw_laser'):
                    inimigo.draw_laser(self.tela, deslocamento)
                    
            self.hud.draw(self.tela)

            self.stage_manager.draw()
            

        elif self.estado_do_jogo == 'pausa':
            
            self.all_sprites.draw(self.tela)
            self.menu_pausa.draw(self.tela)

        elif self.estado_do_jogo == 'colaboradores':
            self.tela_colaboradores.draw(self.tela)

        elif self.estado_do_jogo == 'ranking':
            self.ranking.draw(self.tela)

        elif self.estado_do_jogo == "game_over":
            self.tela_game_over.draw(self.tela)

        elif self.estado_do_jogo == "level_up":
            self.all_sprites.draw(self.tela)
            self.hud.draw(self.tela)
            self.tela_de_upgrade_ativa.draw(self.tela)

        pygame.display.update()

        
    def iniciar_novo_jogo(self):

        # Limpa tudo
        entity_manager.all_sprites.empty()
        entity_manager.inimigos_grupo.empty()
        entity_manager.item_group.empty()
        entity_manager.projeteis_jogador_grupo.empty()
        entity_manager.projeteis_inimigos_grupo.empty()

        # Reseta o spawner para zerar os timers e flags de bosses
        self.timer_jogo = 0
        self.fase_atual = 0
        self.spawner = Spawner(self)

        self.gravemind_reborns = 3
        self.invocacao_protogravemind = 0

        self.mapa = Mapa(self.caminho_mapa, self.fase_atual, all_sprites=self.all_sprites)
        self.largura_mapa_pixels = self.mapa.largura_mapa_pixels
        self.altura_mapa_pixels = self.mapa.altura_mapa_pixels

        posicao_inicial = self.mapa.get_player_spawn_pos()

        # Cria o player
        self.player = Player(
            posicao_inicial=posicao_inicial,
            grupos=self.all_sprites,
            game=self
        )
        entity_manager.player = self.player

        # Certifique que o mixer está inicializado (melhor garantir)
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        #pygame.mixer.music.stop()
        #pygame.mixer.music.load(join('assets', 'sounds', 'musica_tema.wav'))
        #pygame.mixer.music.set_volume(0.0)
        #pygame.mixer.music.play(-1)

        if not hasattr(self.player, 'armas'):
            self.player.armas = {}

        #arma inicial
        rifle = RifleAssalto(jogador=self.player,
            grupos=(self.all_sprites, self.projeteis_jogador_grupo, self.inimigos_grupo),
            game=self
            )
        #arma_Loop = Arma_Loop(
            #jogador=self.player,
            #grupos=(self.all_sprites, self.projeteis_jogador_grupo, self.inimigos_grupo),
            #game=self)

        #arma_listas = ArmaLista(jogador=self.player,
                                #grupos=(self.all_sprites, self.projeteis_jogador_grupo),
                                #game=self)
                        
        #arma_dicionario = Dicionario_Divino(jogador=self.player,
                     #grupos=(self.all_sprites, self.auras_grupo),
                     #game=self)
        #arma_arbitro = ArmaArbitro(
            #jogador=self.player,
            #grupos=(self.all_sprites, self.inimigos_grupo, self.item_group),
            #game=self)

        self.player.armas['Rifle de Assalto'] = rifle
        #self.player.armas[arma_Loop.nome] = arma_Loop
        #self.player.armas['Listas'] = arma_listas
        #self.player.armas['Nova'] = arma_dicionario
        #self.player.armas['Arbitro'] = arma_arbitro

        self.estado_do_jogo = 'jogando'

    def run(self):
        while self.running:
            delta_time = self.clock.tick(fps) / 1000
            self.eventos()
            self.update(delta_time)
            self.draw()