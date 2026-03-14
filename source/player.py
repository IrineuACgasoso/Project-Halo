import pygame
from settings import *
from levelup import TelaDeUpgrade
from systems.entitymanager import entity_manager


class Player(pygame.sprite.Sprite):
    def __init__(self, posicao_inicial, grupos, game):
        """
        Inicia o jogador.
        sheet_player: Imagem.
        grupos: grupos de sprite
        """
        super().__init__(grupos)
        self.game = game
        #envolve movimentação
        self.direcao = pygame.math.Vector2()
        self.velocidade = 500

        #animacao
        self.sprites = {}
        sprite_right = [pygame.image.load(join('assets', 'img', 'player', 'player.png')).convert_alpha(),
                        pygame.image.load(join('assets', 'img', 'player', 'player2.png')).convert_alpha(),
                        pygame.image.load(join('assets', 'img', 'player', 'player3.png')).convert_alpha(),
                        pygame.image.load(join('assets', 'img', 'player', 'player2.png')).convert_alpha()
        ]
        #sprites direita
        self.sprites['right'] = [pygame.transform.scale(sprite, (144, 144)) for sprite in sprite_right]

        sprites_left = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites['right']
        ]
        #sprite esquerda
        self.sprites['left'] = sprites_left

        #variaveis de animacao
        self.frame_atual = 0  
        self.estado_animacao = 'right'
        self.indice_animacao = 0

        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center = posicao_inicial)
        self.posicao = pygame.math.Vector2(self.rect.center)
        self.velocidade_animacao = 150
        self.ultimo_update_animacao = pygame.time.get_ticks()

        #hitbox
        self.mask = pygame.mask.from_surface(self.image) 
        self.tamanho_hitbox = self.rect.width / 1.5
        self.hitbox = pygame.Rect(0, 0, self.tamanho_hitbox, self.rect.height)
        self.hitbox.center = self.rect.center
        #armas do player
        self.armas = {}

        #status
        self.vida_maxima = 500
        self.vida_atual = self.vida_maxima
        self.buff_timer = 0
        self.buff_cooldown_ativo = False 
        #exp
        self.contador_niveis = 1
        self.experiencia_level_up_base = 100 
        self.experiencia_level_up = self.experiencia_level_up_base 
        self.experiencia_atual = 0
        #em %
        self.aumento_xp = 1

        self.coletaveis = {
            "exp_shard": 0,
            "life_orb": 0,
            "big_shard": 0,
            "cafe" : 0
        }

        #invencibilidade
        self.invencivel = False
        self.tempo_ultimo_dano = 0
        self.duracao_invencibilidade = 100

        #ranking
        self.pontuacao = 0

    def input(self):
        #muda os vetores se eles estão sendo pressionados ou não
        #direita = 1, esquerda = -1, cima = 1, baixo = -1
        #se a tecla está sendo pressionada, ela é True, true quando convertido pra int é 1
        keys = pygame.key.get_pressed()
        self.direcao.x = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
        self.direcao.y = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
        #caso a direção não for parado(dá erro), normaliza o vetor para que ao se mover na diagonal, não se mova mais rápido
        if self.direcao != (0,0):
            self.direcao = self.direcao.normalize()


    def projetar_fora_da_linha(self, pos_player, p1, p2, raio):
        # Vetor do segmento de linha
        aresta = p2 - p1
        if aresta.length_squared() == 0: return None

        # Acha o ponto mais próximo do centro do player no segmento (p1-p2)
        # Isso usa projeção escalar limitada entre 0 e 1
        t = max(0, min(1, (pos_player - p1).dot(aresta) / aresta.length_squared()))
        ponto_mais_proximo = p1 + t * aresta

        # Vetor do ponto mais próximo até o centro do player
        diff = pos_player - ponto_mais_proximo
        distancia = diff.length()

        if distancia < raio:
            # Se o player está "atravessando" a linha, calculamos o empurrão
            # Se distancia for 0, o player está exatamente sobre a linha (raro, mas tratamos)
            if distancia == 0:
                return pygame.math.Vector2(0, -1) * raio # Empurrão padrão para cima
            
            push_mag = raio - distancia + 0.1
            return diff.normalize() * push_mag
        
        return None
    
    def mover_com_colisao(self, delta_time, paredes_ativas):
        # 1. Aplicamos o movimento bruto
        dt_seguro = min(delta_time, 0.033)
        self.posicao += self.direcao * self.velocidade * dt_seguro
        
        # 2. Resolvemos colisões com Polilinhas (e Polígonos, que viram linhas)
        # Fazemos isso 2 ou 3 vezes (iterações) para garantir que em cantos apertados 
        # um empurrão não nos jogue para dentro de outra linha.
        raio = self.hitbox.width / 2
        
        for _ in range(3): # Iteraçoes de segurança
            for p in paredes_ativas:
                # Pegamos os pontos da polilinha ou polígono
                pontos = p['pontos']
                for i in range(len(pontos) - 1):
                    p1 = pontos[i]
                    p2 = pontos[i+1]
                    
                    push = self.projetar_fora_da_linha(self.posicao, p1, p2, raio)
                    if push:
                        self.posicao += push

        # 3. Sincroniza Hitbox e Rect visual
        self.hitbox.center = (round(self.posicao.x), round(self.posicao.y))
        self.rect.center = self.hitbox.center
    

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]


    def tomar_dano(self, inimigo):
        if not self.invencivel:
            self.vida_atual -= inimigo.dano
            self.invencivel = True
            self.tempo_ultimo_dano = pygame.time.get_ticks()

    def tomar_dano_direto(self, dano):
        """
        Aplica dano direto ao jogador sem a lógica de invencibilidade.
        Usado para ataques especiais, como do boss.
        """
        self.vida_atual -= dano
        if self.vida_atual < 0:
            self.vida_atual = 0
            
    def curar(self, quantidade):
        self.vida_atual = min(self.vida_atual + quantidade, self.vida_maxima)

    def coletar_item(self, item):
        houve_level_up = False
        
        if item.tipo in self.coletaveis:
            self.coletaveis[item.tipo] += 1

        # efeitos
        if item.tipo == 'exp_shard':
            if self.ganhar_xp(10): 
                houve_level_up = True
        elif item.tipo == 'big_shard':
            if self.ganhar_xp(50):
                houve_level_up = True
        elif item.tipo == 'life_orb':
            self.curar(self.vida_maxima/4)
        elif item.tipo == 'cafe':
            self.vida_atual = self.vida_maxima
            self.adicionar_tempo_buff(10)
        
        return houve_level_up
    def ganhar_xp(self, quantidade):
        self.experiencia_atual += quantidade
        if self.experiencia_atual >= self.experiencia_level_up:
            self.level_up()

    def level_up(self):
        self.experiencia_atual -= self.experiencia_level_up
        self.contador_niveis += 1
        self.vida_maxima += 25
        self.velocidade += 10
        self.pontuacao += 100
        self.curar(self.vida_maxima)

        self.game.estado_do_jogo = 'level_up'
        self.game.tela_de_upgrade_ativa = TelaDeUpgrade(self.game.tela, self, self.game)
        
        self.experiencia_level_up = self.experiencia_level_up_base + 10 * self.contador_niveis

    def adicionar_tempo_buff(self, segundos):
        self.buff_timer += segundos

    def update(self, delta_time, paredes=None):
        self.input()

        if paredes is not None:
            self.mover_com_colisao(delta_time, paredes)
        
        # Calcula se o player está em uma zona de Void
        forca, ponto_alvo, dist = self.game.mapa.calcular_puxo_void(self.posicao)

        if ponto_alvo: # Se for diferente de None, o player está no vácuo
            self.posicao += forca
            self.tomar_dano_direto(1)
            
            # Se o player chegar muito perto do VoidPoint ele morre
            if dist < 15: 
                self.tomar_dano_direto(9999)

        if self.buff_timer > 0:
            self.buff_timer -= delta_time
            if not self.buff_cooldown_ativo:
                self.buff_cooldown_ativo = True
                for arma in self.armas.values():
                    if hasattr(arma, 'cooldown') and arma.cooldown != float('inf'):
                        arma.cooldown_original = arma.cooldown
                        arma.cooldown /= 2

        elif self.buff_timer <= 0 and self.buff_cooldown_ativo:
            self.buff_timer = 0
            self.buff_cooldown_ativo = False
            for arma in self.armas.values():
                if hasattr(arma, 'cooldown_original'):
                    arma.cooldown = arma.cooldown_original

        if self.invencivel:
            agora = pygame.time.get_ticks()
            if agora - self.tempo_ultimo_dano > self.duracao_invencibilidade:
                self.invencivel = False
            
            #pisca player
            alpha = 255 if int(pygame.time.get_ticks() / 50) % 2 == 0 else 0
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)
        
        if self.direcao.x < 0:
            self.estado_animacao = 'left'
        elif self.direcao.x > 0:
            self.estado_animacao = 'right'
        if self.direcao.x == 0 and self.direcao.y == 0:
            self.image = self.sprites[self.estado_animacao][0] # Usa o frame 0 da direção atual
        if self.direcao.magnitude() == 0:
            # Mantém o frame parado
            pass 
        else:
            self.animar()
        

        if self.experiencia_atual >= self.experiencia_level_up:
            self.level_up()
        
        # --- ÁREA DOS HACKS ---
        hack = pygame.key.get_pressed()
        
        # Hack L: Level Up
        if hack[pygame.K_l]:
            falta = self.experiencia_level_up - self.experiencia_atual
            self.experiencia_atual += falta
        
        # Hack P: Spawnar Portal (Instant Exit)
        elif hack[pygame.K_p]:
            # Verifica se o jogo já tem um portal ativo. 
            if self.game.portal_atual is None:
                # Importação local para evitar erro circular (Player importar Portal e Portal importar Player)
                from feats.effects import Portal 
                
                offset = 50 if self.estado_animacao == 'right' else -50
                pos_portal = self.posicao + pygame.math.Vector2(offset, 0)
                
                novo_portal = Portal(pos_portal, entity_manager.all_sprites)
                self.game.portal_atual = novo_portal

        elif hack[pygame.K_b]:
            if self.game.boss_atual is None:
                if hasattr(self.game, 'spawner'):
                    self.game.spawner.forcar_proximo_boss()