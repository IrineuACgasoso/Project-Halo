import pygame
from settings import *
from levelup import TelaDeUpgrade


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
        self.image = pygame.image.load(join('assets', 'img', 'player', 'player.png')).convert_alpha()

        #animacao
        self.sprites = {}
        sprite_right = [pygame.image.load(join('assets', 'img', 'player', 'player.png')).convert_alpha(),
                        pygame.image.load(join('assets', 'img', 'player', 'player2.png')).convert_alpha(),
                        pygame.image.load(join('assets', 'img', 'player', 'player3.png')).convert_alpha(),
                        pygame.image.load(join('assets', 'img', 'player', 'player2.png')).convert_alpha()
        ]
        #sprites direita
        self.sprites['right'] = [pygame.transform.scale(sprite, (128, 128)) for sprite in sprite_right]

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
        self.rect = self.image.get_rect(center = (posicao_inicial[0]/2, posicao_inicial[1]/2))
        self.posicao = pygame.math.Vector2(self.rect.center)
        self.velocidade_animacao = 150
        self.ultimo_update_animacao = pygame.time.get_ticks()

        #hitbox
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

    def movimentacao(self, delta_time):
        #delta_time serve pra o jogador sempre se mover na mesma velocidade independente do fps
        self.posicao +=  self.direcao * self.velocidade * delta_time #atualiza a posição atual

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
        self.rect.center = self.posicao
        self.hitbox.center = self.rect.center


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

    def update(self, delta_time):
        self.input()
        self.movimentacao(delta_time)

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
            self.image = pygame.transform.scale(pygame.image.load(join('assets', 'img', 'player', 'player.png')).convert_alpha(), (128,128))

        if self.direcao.x != 0 or self.direcao.y != 0:
            self.animar()
        

        if self.experiencia_atual >= self.experiencia_level_up:
            self.level_up()
        hack = pygame.key.get_pressed()
        if hack[pygame.K_l]:
            falta = self.experiencia_level_up - self.experiencia_atual
            self.experiencia_atual += falta





   


