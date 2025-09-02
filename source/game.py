import pygame
import random
from os.path import join
from settings import *
from player import Player 
from menu import *
from hud import *
from enemies import InimigoBug, Grunt, Infection, InimigoLadrao, InimigoPython
from weapon import *
from grupos import AllSprites
from colaboradores import TelaColaboradores
from ranking import Ranking 
from levelup import *
from mapa import Mapa
from hunter import *
from guilty import *
from arbiter import *
from gravemind import *
from didact import *
from warden import *


class Game:
    def __init__(self, tela):
        self.tela = tela
        self.running = True
        self.clock = pygame.time.Clock()
        self.estado_do_jogo = "menu_principal"

        # Sprites e grupos
        self.all_sprites = AllSprites()
        self.item_group = pygame.sprite.Group()
        self.auras_grupo = pygame.sprite.Group()
        self.inimigos_grupo = pygame.sprite.Group()
        self.projeteis_jogador_grupo = pygame.sprite.Group()
        self.projeteis_inimigos_grupo = pygame.sprite.Group()

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

        #mapa 
        self.mapa = None # Inicialize o mapa como None
        self.largura_mapa_pixels = 0
        self.altura_mapa_pixels = 0

        # Controle de spawn
        self.tempo_proximo_spawn = 0
        self.intervalo_spawn_atual = 2.5
        self.intervalo_minimo = 0.8
        self.fator_dificuldade = 0.01
        self.hordas_contagem = 0

        #habilidades dos bosses
        self.gravemind_reborns = 3
        self.contagem_clones = 0
        self.eternal_spawnado = False

        #painel control boss
        self.hunter_1_invocado = False
        self.guilty_invocado = False
        self.arbiter_invocado = False
        self.invocacao_protogravemind = 0
        self.didact_invocado = False
        self.warden_invocado = False


    def iniciar_novo_jogo(self):
        self.all_sprites.empty()
        self.item_group.empty()
        self.projeteis_jogador_grupo.empty()
        self.inimigos_grupo.empty()
        self.tempo_proximo_spawn = 0
        self.intervalo_spawn_atual = 2.0
        self.hordas_contagem = 0

        # Inicializa player
        self.player = Player(self, 400, 300)
        self.hud = HUD(self)
        self.estado_do_jogo = "jogando"

        #habilidades dos bosses
        self.gravemind_reborns = 3

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
        if tipo == 'hunter':
            Hunter(posicao=self.pos, grupos=(self.all_sprites, self.inimigos_grupo), jogador=self.player, game=self)
        if tipo == 'guilty':
            GuiltySpark(posicao=self.pos, grupos=(self.all_sprites, self.inimigos_grupo), jogador=self.player, game=self)
        if tipo == 'arbiter':
            BossArbiter(posicao=self.pos, grupos=(self.all_sprites, self.inimigos_grupo), jogador=self.player, game=self)
        if tipo == 'gravemind':
            FloodWarning(posicao=self.player.posicao, grupos=self.all_sprites, game=self)
        if tipo == 'didact':
            Didact(posicao=self.pos, grupos=(self.all_sprites, self.inimigos_grupo), jogador=self.player, game=self)
        if tipo == 'warden':
            WardenEternal(posicao=self.pos, grupos=(self.all_sprites, self.inimigos_grupo), jogador=self.player, game=self, is_eternal=False)
        if tipo == 'eternal':
            WardenEternal(posicao=self.pos, grupos=(self.all_sprites, self.inimigos_grupo), jogador=self.player, game=self, is_eternal=True)

            
        else:
            tipos_de_inimigos = [Infection, Grunt, InimigoBug]
            inimigo = random.choice(tipos_de_inimigos)
            inimigo(posicao=self.pos, grupos=(self.all_sprites, self.inimigos_grupo), jogador=self.player, game=self)

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
            
            # Lógica para spawnar o boss
            #if self.player.contador_niveis == 1:
                #self.spawnar_inimigo(tipo='gravemind')
                #self.intervalo_spawn_atual = 2.0
                #self.gravemind_spawnado = True

            if self.tempo_proximo_spawn >= self.intervalo_spawn_atual:
                self.tempo_proximo_spawn = 0
                self.hordas_contagem += 1
                
                for _ in range(0):
                    self.spawnar_inimigo()
                if self.player.contador_niveis == 100 and self.guilty_invocado == False:
                    self.guilty_invocado = True
                    self.spawnar_inimigo(tipo='guilty')
                if self.player.contador_niveis == 1 and self.arbiter_invocado == False:
                    self.arbiter_invocado = True
                    self.spawnar_inimigo(tipo='arbiter')
                if self.player.contador_niveis == 100 and self.hunter_1_invocado == False:
                    self.hunter_1_invocado = True
                    self.spawnar_inimigo(tipo='hunter')
                if self.player.contador_niveis == 100 and self.gravemind_spawnado == False:
                    self.gravemind_spawnado = True
                    self.spawnar_inimigo(tipo='gravemind')
                if self.player.contador_niveis == 100 and self.didact_invocado == False:
                    self.didact_invocado = True
                    self.spawnar_inimigo(tipo='didact')
                if self.player.contador_niveis == 100 and self.warden_invocado == False:
                    self.warden_invocado = True
                    self.spawnar_inimigo(tipo='warden')
                # Spawna o Warden Eternal quando 10 clones morrem
                if self.contagem_clones >= 10 and not self.eternal_spawnado:
                    self.eternal_spawnado = True
                    self.spawnar_inimigo(tipo='eternal')
                    
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
            deslocamento = self.mapa.get_camera_offset(self.player.posicao, (largura_tela, altura_tela))
            self.mapa.draw(self.tela, deslocamento)
            # Itera por todos os sprites e desenha cada um
            for sprite in sorted(self.all_sprites, key=lambda s: s.rect.centery):
                # Se for um LaserWarning, use o método de desenho personalizado
                if isinstance(sprite, LaserWarning):
                    sprite.draw(self.tela, deslocamento)
                else:
                    # Para todos os outros sprites, desenha normalmente
                    self.tela.blit(sprite.image, pygame.math.Vector2(sprite.rect.topleft) - deslocamento)
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
        self.projeteis_jogador_grupo.empty()
        self.inimigos_grupo.empty()

        self.gravemind_reborns = 3
        self.contagem_clones = 0
        self.eternal_spawnado = False

        self.invocacao_protogravemind = 0
        self.invocacao_protogravemind = 0
        self.didact_invocado = False
        self.hunter_1_invocado = False
        self.arbiter_invocado = False
        self.guilty_invocado = False
        self.warden_invocado = False


        self.tempo_proximo_spawn = 0
        self.intervalo_spawn_inicial = 2.0
        self.intervalo_spawn_atual = self.intervalo_spawn_inicial
        self.intervalo_minimo = 0.3
        self.fator_dificuldade = 0.04

        self.mapa = Mapa(all_sprites=self.all_sprites)
        self.largura_mapa_pixels = self.mapa.largura_mapa_pixels
        self.altura_mapa_pixels = self.mapa.altura_mapa_pixels
        self.player = Player(
            posicao_inicial=(self.mapa.largura_mapa_pixels / 2, self.mapa.altura_mapa_pixels),
            grupos=self.all_sprites,
            game=self
        )

        # Certifique que o mixer está inicializado (melhor garantir)
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        pygame.mixer.music.stop()
        pygame.mixer.music.load(join('assets', 'sounds', 'musica_tema.wav'))
        pygame.mixer.music.set_volume(0.0)
        pygame.mixer.music.play(-1)

        if not hasattr(self.player, 'armas'):
            self.player.armas = {}

        #arma inicial
        arma_Loop = Arma_Loop(
            jogador=self.player,
            grupos=(self.all_sprites, self.projeteis_jogador_grupo, self.inimigos_grupo),
            game=self
        )

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

        self.player.armas[arma_Loop.nome] = arma_Loop
        #self.player.armas['Listas'] = arma_listas
        #self.player.armas['Nova'] = arma_dicionario
        #self.player.armas['Arbitro'] = arma_arbitro

        self.estado_do_jogo = 'jogando'

    def colisao(self, delta_time):
        # Colisão de Projéteis do Jogador com Inimigos
        # Separa projéteis que não ricocheteiam
        projeteis_sem_ricochete = pygame.sprite.Group([p for p in self.projeteis_jogador_grupo if not p.ricochete])

        # Colisão para projéteis que não ricocheteiam (mata o projétil na colisão)
        colisoes_normais = pygame.sprite.groupcollide(
            projeteis_sem_ricochete,
            self.inimigos_grupo,
            True,  # dokill=True: remove o projétil na colisão
            False, # dokill=False: não remove o inimigo
            pygame.sprite.collide_mask
        )

        # Aplica dano aos inimigos atingidos por projéteis que não ricocheteiam
        for inimigo_atingido in colisoes_normais.values():
            for inimigo in inimigo_atingido:
                # Pega o primeiro projétil que colidiu para obter o dano
                dano_do_primeiro_projetil = list(colisoes_normais.keys())[0].dano
                if not (isinstance(inimigo, WardenEternal) and inimigo.invencivel):
                    inimigo.vida -= dano_do_primeiro_projetil


        # Agora, lida com projéteis que ricocheteiam
        projeteis_com_ricochete = pygame.sprite.Group([p for p in self.projeteis_jogador_grupo if p.ricochete])

        # Colisão para projéteis que ricocheteiam (não mata o projétil na colisão)
        colisoes_ricochete = pygame.sprite.groupcollide(
            projeteis_com_ricochete,
            self.inimigos_grupo,
            False, # dokill=False: não remove o projétil
            False, # dokill=False: não remove o inimigo
            pygame.sprite.collide_mask
        )

        # Aplica dano a todos os inimigos que um projétil de ricochete atingiu
        for projetil, inimigos_atingidos in colisoes_ricochete.items():
            for inimigo in inimigos_atingidos:
                if not (isinstance(inimigo, WardenEternal) and inimigo.invencivel):
                    inimigo.vida -= projetil.dano

        # Colisão de Projéteis dos Inimigos com o Jogador
        # Remove os projéteis inimigos quando eles atingem o jogador.
        projeteis_filtrados = [
            p for p in self.projeteis_inimigos_grupo if not isinstance(p, GuiltyLaser)
            ]
        colisoes_projeteis_inimigos = pygame.sprite.groupcollide(
            pygame.sprite.Group(projeteis_filtrados),
            pygame.sprite.Group(self.player),  # Cria um grupo temporário apenas com o jogador
            True,  # 'dokill' True: remove o projetil
            False, # 'dokill' False: não remove o jogador
            pygame.sprite.collide_mask # Use collide_rect para o jogador ou collide_mask se ele tiver
        )
        # Aplica o dano do projétil ao jogador
        for projetil, _ in colisoes_projeteis_inimigos.items():
            self.player.tomar_dano_direto(projetil.dano)
        
        # Colisão do Jogador com Inimigos
        for inimigo in self.inimigos_grupo:
            if pygame.sprite.collide_mask(self.player, inimigo):
                self.player.tomar_dano(inimigo)

        # Coleta de itens (não precisa de mudanças)
        itens_coletados = pygame.sprite.spritecollide(self.player, self.item_group, dokill=True)
        for item in itens_coletados:
            self.player.coletar_item(item)

        # Colisão com Dot (dano ao longo do tempo)
        if self.auras_grupo:
            colisoes_aura = pygame.sprite.groupcollide(
                self.inimigos_grupo, 
                self.auras_grupo, 
                False, 
                False, 
                pygame.sprite.collide_circle
            )
            for inimigo, auras in colisoes_aura.items():
                for aura in auras: 
                    dano_neste_frame = aura.dano_por_segundo * delta_time
                    inimigo.vida -= dano_neste_frame

        # Lógica de morte de inimigos (não precisa de mudanças)
        for inimigo in list(self.inimigos_grupo):
            if inimigo.vida <= 0:
                inimigo.morrer((self.all_sprites, self.item_group))


    def run(self):
        while self.running:
            delta_time = self.clock.tick(fps) / 1000
            self.eventos()
            self.update(delta_time)
            self.draw()