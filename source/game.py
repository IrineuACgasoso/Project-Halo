import pygame
import random
from os.path import join
from settings import *
from player import Player 
from menu import *
from hud import *
from enemies import InimigoBug, InimigoListaIP, Infection, InimigoLadrao, InimigoPython
from weapon import *
from grupos import AllSprites
from colaboradores import TelaColaboradores
from ranking import Ranking 
from levelup import *
from mapa import Mapa
from gravemind import *


class Game:
    def __init__(self, tela):
        self.tela = tela
        self.running = True
        self.clock = pygame.time.Clock()
        self.estado_do_jogo = "menu_principal"

        # Sprites e grupos
        self.all_sprites = AllSprites()
        self.item_group = pygame.sprite.Group()
        self.projeteis_grupo = pygame.sprite.Group()
        self.auras_grupo = pygame.sprite.Group()
        self.inimigos_grupo = pygame.sprite.Group()

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

        # Controle de spawn
        self.tempo_proximo_spawn = 0
        self.intervalo_spawn_atual = 2.0
        self.intervalo_minimo = 0.5
        self.fator_dificuldade = 0.01
        self.hordas_contagem = 0

    def iniciar_novo_jogo(self):
        self.all_sprites.empty()
        self.item_group.empty()
        self.projeteis_grupo.empty()
        self.inimigos_grupo.empty()
        self.tempo_proximo_spawn = 0
        self.intervalo_spawn_atual = 2.0
        self.hordas_contagem = 0

        # Inicializa player
        self.player = Player(self, 400, 300)
        self.hud = HUD(self)
        self.estado_do_jogo = "jogando"

    def spawnar_inimigo(self, tipo='normal'):
        camera_center_x = self.player.posicao.x
        camera_center_y = self.player.posicao.y
        borda_esquerda = camera_center_x - largura_tela / 2
        borda_direita = camera_center_x + largura_tela / 2
        borda_topo = camera_center_y - altura_tela / 2
        borda_baixo = camera_center_y + altura_tela / 2
        lado = random.choice(['top', 'bottom', 'left', 'right'])
        if lado == 'top':
            self.pos = (random.uniform(borda_esquerda, borda_direita), borda_topo - 50)
        elif lado == 'bottom':
            self.pos = (random.uniform(borda_esquerda, borda_direita), borda_baixo + 50)
        elif lado == 'left':
            self.pos = (borda_esquerda - 50, random.uniform(borda_topo, borda_baixo))
        else:
            self.pos = (borda_direita + 50, random.uniform(borda_topo, borda_baixo))

        if tipo == 'boss':
            FloodWarning(posicao=self.pos, grupos=self.all_sprites, game=self)
        else:
            tipos_de_inimigos = [Infection, InimigoListaIP, InimigoBug]
            inimigo = random.choice(tipos_de_inimigos)
            inimigo(posicao=self.pos, grupos=(self.all_sprites, self.inimigos_grupo), jogador=self.player)
    
    def spawnar_gravemind(self, posicao):
        Gravemind(posicao=posicao,grupos=(self.all_sprites, self.inimigos_grupo), jogador=self.player, game=self)

    def eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.running = False
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN and (evento.mod & pygame.KMOD_ALT):
                    pygame.display.toggle_fullscreen()

            # MENU PRINCIPAL
            if self.estado_do_jogo == "menu_principal":
                escolha = self.menu_principal.handle_event(evento)
                if escolha == 'Start Game':
                    self.iniciar_novo_jogo()
                if escolha == 'Colaboradores':
                    self.estado_do_jogo = 'colaboradores'
                if escolha == 'Ranking':
                    self.estado_do_jogo = 'ranking'
                elif escolha == 'Colaboradores':
                    self.estado_do_jogo = 'colaboradores'
                elif escolha == 'Sair':
                    self.running = False

            # JOGANDO
            elif self.estado_do_jogo == "jogando":
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    self.estado_do_jogo = "pausa"

            # PAUSA
            elif self.estado_do_jogo == "pausa":
                escolha = self.menu_pausa.handle_event(evento)
                if escolha == "Continuar":
                    self.estado_do_jogo = "jogando"
                elif escolha == "Sair para Menu":
                    self.estado_do_jogo = "menu_principal"
                    self.menu_principal = MenuPrincipal(self)

            # LEVEL UP
            elif self.estado_do_jogo == 'level_up':
                if self.tela_de_upgrade_ativa:
                    escolha_idx = self.tela_de_upgrade_ativa.handle_event(evento)
           
                    if escolha_idx is not None and escolha_idx < len(self.tela_de_upgrade_ativa.opcoes_de_armas_obj):
                        arma_escolhida = self.tela_de_upgrade_ativa.opcoes_de_armas_obj[escolha_idx]
                        nome_da_arma = arma_escolhida.nome
                        
                        #upgrade em arma no inventario
                        if nome_da_arma in self.player.armas:
                            self.player.armas[nome_da_arma].upgrade()
                        #nova arma
                        else:
                            self.player.armas[nome_da_arma] = arma_escolhida 
                            arma_escolhida.equipar()
                        
                        self.estado_do_jogo = 'jogando'
                        self.tela_de_upgrade_ativa = None
            
            #tela de colaboradores
            elif self.estado_do_jogo == 'colaboradores':
                self.tela_colaboradores.handle_event(evento)
            #tela de ranking
            elif self.estado_do_jogo == 'ranking':
                action = self.ranking.handle_event(evento)
                if action == 'exit_to_menu':
                    self.estado_do_jogo = 'menu_principal'

            # COLABORADORES
            elif self.estado_do_jogo == 'colaboradores':
                action = self.colaboradores.handle_event(evento)
                if action == 'sair':
                    self.estado_do_jogo = 'menu_principal'

            # GAME OVER
            elif self.estado_do_jogo == "game_over":
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_RETURN:
                    if hasattr(self, 'player'):
                        self.ranking.start_name_input(self.player.pontuacao)
                    self.estado_do_jogo = "ranking"

    def update(self, delta_time):
        if self.estado_do_jogo == "jogando":
            self.all_sprites.update(delta_time)
            self.tempo_proximo_spawn += delta_time
            if self.player:
                for arma in self.player.armas.values():
                    arma.update(delta_time)

            if self.tempo_proximo_spawn >= self.intervalo_spawn_atual:
                self.tempo_proximo_spawn = 0
                self.hordas_contagem += 1
                
                for _ in range(4):
                    self.spawnar_inimigo()

                if self.hordas_contagem % 5 == 0:
                    self.spawnar_inimigo(tipo='boss')
                if self.hordas_contagem > 0 and self.hordas_contagem % 100 == 0:
                # Spawna o inimigo especial que aparece a cada 100 hordas
                    self.spawnar_inimigo(tipo='inimigo_horda_100')

            if self.intervalo_spawn_atual > self.intervalo_minimo:
                self.intervalo_spawn_atual -= self.fator_dificuldade * delta_time

            self.colisao(delta_time)

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
            #desenha mapa
            deslocamento = self.mapa.get_camera_offset(self.player.posicao, (largura_tela, altura_tela))
            self.mapa.draw(self.tela, deslocamento)
            self.all_sprites.draw(self.player.posicao)
            self.hud.draw(self.tela)

        elif self.estado_do_jogo == 'pausa':
            
            self.all_sprites.draw(self.player.posicao)
            self.menu_pausa.draw(self.tela)

        elif self.estado_do_jogo == 'colaboradores':
            self.tela_colaboradores.draw(self.tela)

        elif self.estado_do_jogo == 'ranking':
            self.ranking.draw(self.tela)

        elif self.estado_do_jogo == "game_over":
            self.tela_game_over.draw(self.tela)

        elif self.estado_do_jogo == "level_up":
            self.all_sprites.draw(self.player.posicao)
            self.hud.draw(self.tela)
            self.tela_de_upgrade_ativa.draw(self.tela)

        pygame.display.update()
    
    def iniciar_novo_jogo(self):
        self.all_sprites.empty()
        self.item_group.empty()
        self.projeteis_grupo.empty()
        self.inimigos_grupo.empty()

        self.tempo_proximo_spawn = 0
        self.intervalo_spawn_inicial = 2.0
        self.intervalo_spawn_atual = self.intervalo_spawn_inicial
        self.intervalo_minimo = 0.3
        self.fator_dificuldade = 0.04

        self.mapa = Mapa(all_sprites=self.all_sprites)
        self.player = Player(
            posicao_inicial=(self.mapa.largura_mapa_pixels / 2, self.mapa.altura_mapa_pixels),
            sheet_player=join('assets', 'img', 'player.png'),
            grupos=self.all_sprites,
            game=self
        )

        # Certifique que o mixer está inicializado (melhor garantir)
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        pygame.mixer.music.stop()
        pygame.mixer.music.load(join('assets', 'sounds', 'musica_tema.wav'))
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(-1)

        if not hasattr(self.player, 'armas'):
            self.player.armas = {}

        #arma inicial
        arma_Loop = Arma_Loop(
            jogador=self.player,
            grupos=(self.all_sprites, self.projeteis_grupo),
            game=self
        )

        #arma_listas = ArmaLista(jogador=self.player,
                                #grupos=(self.all_sprites, self.projeteis_grupo),
                                #game=self)
                        
        #arma_dicionario = Dicionario_Divino(jogador=self.player,
                     #grupos=(self.all_sprites, self.auras_grupo),
                     #game=self)
        #arma_byte = ArmaByte(
    #jogador=self.player,
    #grupos=(self.all_sprites, self.inimigos_grupo, self.item_group),
    #game=self)

        self.player.armas[arma_Loop.nome] = arma_Loop
        #self.player.armas['Listas'] = arma_listas
        #self.player.armas['Nova'] = arma_dicionario
        #self.player.armas['Byte'] = arma_byte

        self.estado_do_jogo = 'jogando'

    def colisao(self, delta_time):
    # Coleta de itens
        itens_coletados = pygame.sprite.spritecollide(self.player, self.item_group, dokill=True)
        for item in itens_coletados:
            self.player.coletar_item(item)

        # Colisão com inimigos (Jogador vs. Inimigos)
        for inimigo in self.inimigos_grupo:
            if isinstance(inimigo, Gravemind):
                if self.player.rect.colliderect(inimigo.hitbox):
                    self.player.tomar_dano(inimigo)
            else:
                if self.player.rect.colliderect(inimigo.rect):
                    self.player.tomar_dano(inimigo)
        
        # Lógica para Projéteis do Jogador (Ping Pong, etc.)
        for projetil in list(self.projeteis_grupo):
            # Apenas projéteis que não são auras ou do boss.
            if isinstance(projetil, Projetil_PingPong) or isinstance(projetil, Projetil_Lista):
                # Encontra todas as colisões para o projétil
                colisoes = pygame.sprite.spritecollide(
                    projetil, 
                    self.inimigos_grupo, 
                    False # Não remove o projétil ainda
                )
                
                # Aplica dano aos inimigos que foram atingidos
                for inimigo in colisoes:
                    # Agora, verifica se o inimigo não está na lista
                    if inimigo not in projetil.inimigos_atingidos:
                        inimigo.vida -= projetil.dano
                        # Adiciona o inimigo à lista para não dar dano novamente
                        projetil.inimigos_atingidos.append(inimigo)
            
            # Lógica para projéteis de Aura (Dicionário Divino)
            elif isinstance(projetil, Projetil_Area):
                inimigos_na_aura = pygame.sprite.spritecollide(projetil, self.inimigos_grupo, False)
                for inimigo in inimigos_na_aura:
                    # Dano por segundo
                    dano_por_frame = projetil.dano_por_segundo * delta_time
                    inimigo.vida -= dano_por_frame
            
            # Lógica para projéteis do Boss (AcidBreath)
            elif isinstance(projetil, AcidBreath):
                if self.player.rect.colliderect(projetil.rect):
                    self.player.tomar_dano_direto(projetil.dano)
                    projetil.kill()

    def run(self):
        while self.running:
            delta_time = self.clock.tick(fps) / 1000
            self.eventos()
            self.update(delta_time)
            self.draw()