import pygame
from game import *
from items import *
from enemies import *
from player import *
import random
import math

class Didact(InimigoBase):
    def __init__(self, posicao, grupos, jogador, game):
        super().__init__(posicao, grupos, jogador, game, vida_base=1000, dano_base=40, velocidade_base=50)
        self.game = game
        #sprites
        self.sprites = {}
        self.sprites['left'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'didact', 'did1.png')).convert_alpha(), (350,350)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'didact', 'did2.png')).convert_alpha(), (350,350))
            ]
        self.sprites['right'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites['left']
        ]
        #sprite pull
        self.sprites['pull'] = pygame.transform.scale(pygame.image.load(join('assets', 'img', 'didact', 'did3.png')).convert_alpha(), (350,350))
        #sprite laser
        self.sprites['laser'] = pygame.transform.scale(pygame.image.load(join('assets', 'img', 'didact', 'did4.png')).convert_alpha(), (350,350))

        #framagem da sprite
        self.frame_atual = 0  
        self.estado_animacao = 'right'
        self.indice_animacao = 0
        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center=self.posicao)
        self.velocidade_animacao = 500
        self.ultimo_update_animacao = pygame.time.get_ticks()

        #hitbox
        nova_largura = self.rect.width / 2
        self.hitbox = pygame.Rect(0, 0, nova_largura, self.rect.height)
        self.hitbox.center = self.rect.center

        #pull ability
        self.estado_habilidade = 'parado' # 'parado', 'ataque_pull', 'ataque_laser'
        self.cooldown_pull = 1000 # 5 segundos de recarga
        self.tempo_ultimo_pull = pygame.time.get_ticks()
        self.duracao_pull = 5000 # 5 segundos de duração
        self.tempo_inicio_pull = 0
        self.dano_pull = self.jogador.vida_maxima / 100
        self.intervalo_dano_pull = 1000  # Intervalo de 250 milissegundos
        self.tempo_ultimo_dano_pull = 0 

        #laser ability
        self.cooldown_laser = 2000
        self.tempo_ultimo_laser = pygame.time.get_ticks()
        self.duracao_aviso_laser = 1000 # 1.5 segundos de aviso
        self.duracao_disparo_laser = 500 # 0.5 segundos de disparo
        self.tempo_inicio_laser = 0
        self.posicao_alvo_laser = pygame.math.Vector2()

    @property
    def collision_rect(self):
        "Retorna a hitbox de Didact."
        return self.hitbox

    def ativar_laser(self):
        agora = pygame.time.get_ticks()
        if agora - self.tempo_ultimo_laser >= self.cooldown_laser:
            # Define os possíveis valores de cooldown (em milissegundos)
            possiveis_cooldowns = [5000, 6000, 7000, 8000] 
            self.cooldown_laser = random.choice(possiveis_cooldowns)
            self.estado_habilidade = 'aviso_laser'
            self.tempo_inicio_laser = agora
            self.tempo_ultimo_laser = agora
            # Trava a posição do jogador para o aviso e o laser
            self.posicao_alvo_laser = self.jogador.posicao.copy()
            # Cria o aviso do laser (a linha reta)
            LaserWarning(
                start_pos=self.posicao,
                end_pos=self.posicao_alvo_laser,
                grupos=self.game.all_sprites,
                game=self.game
            )
        
    # Crie um método para disparar o laser
    def disparar_laser(self):
        # Cria o projétil de laser
        Laser(
            posicao_inicial=self.posicao.copy(), # Posição atual do Didact
            posicao_final=self.posicao_alvo_laser.copy(), # Posição travada do jogador
            grupos=(self.game.all_sprites, self.game.projeteis_inimigos_grupo),
            game=self.game,
            player=self.game.player
        )

    def puxar_jogador(self):
        agora = pygame.time.get_ticks()
        if agora - self.tempo_ultimo_pull >= self.cooldown_pull:
            novo_cooldown = [8000, 9000, 10000, 11000]
            self.cooldown_pull = random.choice(novo_cooldown)
            self.estado_habilidade = 'ataque_pull'
            self.tempo_inicio_pull = agora
            self.tempo_ultimo_pull = agora

    def aplicar_efeito_pull(self, delta_time):
        # A velocidade com que o jogador é puxado
        velocidade_puxao = 525
        # Calcula a direção do jogador para o Didact
        direcao_puxao = self.posicao - self.jogador.posicao
        if direcao_puxao.length() > 0:
            direcao_puxao.normalize_ip()
        # Move o jogador em direção ao Didact
        self.jogador.posicao += direcao_puxao * velocidade_puxao * delta_time
        # E atualize o rect do jogador
        self.jogador.rect.center = self.jogador.posicao

    def animar(self):
        # Se o Didact está usando o pull, a imagem não muda
        if self.estado_habilidade == 'ataque_pull':
            self.image = self.sprites['pull']
            # Corrija a linha abaixo para atualizar o rect corretamente
            self.rect.center = self.posicao
        else:
            agora = pygame.time.get_ticks()
            if agora - self.ultimo_update_animacao > self.velocidade_animacao:
                self.ultimo_update_animacao = agora
                self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
                self.image = self.sprites[self.estado_animacao][self.frame_atual]
                self.rect = self.image.get_rect(center=self.posicao)
    
    def morrer(self, grupos):
        chance= randint(1,1000)
        if chance >= 950:
            Items(posicao=self.posicao, sheet_item=join('assets', 'img', 'cafe.png'), tipo='cafe', grupos=grupos)
            for _ in range(5):
                posicao_drop = self.posicao + pygame.math.Vector2(randint(-30, 30), randint(-30, 30))
                Items(posicao=posicao_drop, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=grupos)
        elif 800 <= chance < 950:
            chance2 = randint(1,4)
            if chance2 == 4:
                Items(posicao=self.posicao, sheet_item=join('assets', 'img', 'cafe.png'), tipo='cafe', grupos=grupos)
            for _ in range(4):
                posicao_drop = self.posicao + pygame.math.Vector2(randint(-30, 30), randint(-30, 30))
                Items(posicao=posicao_drop, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=grupos)
        elif 500 <= chance < 800:
            for _ in range(3):
                posicao_drop = self.posicao + pygame.math.Vector2(randint(-30, 30), randint(-30, 30))
                Items(posicao=posicao_drop, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=grupos)
        else:
            for _ in range(2):
                posicao_drop = self.posicao + pygame.math.Vector2(randint(-30, 30), randint(-30, 30))
                Items(posicao=posicao_drop, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=grupos)
        self.kill()
        
    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        # Lógica de controle de estado
        if self.estado_habilidade == 'ataque_pull':
            # Aplica o dano ao jogador se o intervalo de tempo foi atingido
            if agora - self.tempo_ultimo_dano_pull >= self.intervalo_dano_pull:
                self.jogador.tomar_dano_direto(self.dano_pull)
                self.tempo_ultimo_dano_pull = agora
            # Se a duração da habilidade terminou, volte ao estado normal
            if agora - self.tempo_inicio_pull >= self.duracao_pull:
                self.estado_habilidade = 'parado'
                self.image = self.sprites[self.estado_animacao][self.frame_atual] # Retorna para o sprite de animação
                self.rect.center = self.posicao
                self.hitbox.center = self.rect.center

            else:
                # Continue aplicando o efeito de puxar
                self.aplicar_efeito_pull(delta_time)
        elif self.estado_habilidade == 'aviso_laser':
            # Verifica se o tempo de aviso terminou
            if agora - self.tempo_inicio_laser >= self.duracao_aviso_laser:
                # O aviso terminou, agora é o momento de disparar
                self.estado_habilidade = 'disparo_laser'
                self.tempo_inicio_laser = agora
                self.disparar_laser()
                # Mude a sprite para o laser no momento do disparo
                self.image = self.sprites['laser']
                self.rect.center = self.posicao
        elif self.estado_habilidade == 'disparo_laser':
            # Fica com a sprite do laser enquanto ele é disparado
            if agora - self.tempo_inicio_laser >= self.duracao_disparo_laser:
                self.estado_habilidade = 'parado'
        else:
            direcao = (self.jogador.posicao - self.posicao)
            if direcao.length() > 0:
                direcao.normalize_ip()
                self.posicao += direcao * self.velocidade * delta_time
                self.rect.center = (round(self.posicao.x), round(self.posicao.y))
            if (self.jogador.posicao - self.posicao).length() > 500:
                self.puxar_jogador()
            if agora - self.tempo_ultimo_laser >= self.cooldown_laser:
                self.ativar_laser()
            if direcao.x < 0:
                self.estado_animacao = 'left'
            elif direcao.x > 0:
                self.estado_animacao = 'right'
        self.animar()
        
class LaserWarning(pygame.sprite.Sprite):
    def __init__(self, start_pos, end_pos, grupos, game):
        super().__init__(grupos)
        self.game = game
        self.start_pos = pygame.math.Vector2(start_pos)
        
        # Calcular a direção do laser
        direcao = pygame.math.Vector2(end_pos) - self.start_pos
        if direcao.length() > 0:
            direcao.normalize_ip()
        else:
            # Caso o jogador esteja exatamente na mesma posição do didact
            direcao = pygame.math.Vector2(1, 0)
        
        self.end_pos = self.start_pos + direcao * 2000

        self.duracao = 1000  # 1.5 segundos de aviso
        self.largura = 400
        self.tempo_criacao = pygame.time.get_ticks()

        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.start_pos)
    def draw(self, surface, offset):
        agora = pygame.time.get_ticks()
        if agora - self.tempo_criacao < self.duracao:
            # Posições ajustadas pela câmera
            start_pos_ajustada = self.start_pos - offset
            end_pos_ajustada = self.end_pos - offset
            
            # Desenha a linha na tela principal
            pygame.draw.line(surface, (250, 0, 0, 100), start_pos_ajustada, end_pos_ajustada, self.largura)

    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        if agora - self.tempo_criacao >= self.duracao:
            self.kill() # Remove o aviso depois que o tempo de vida termina

class Laser(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, posicao_final, grupos, game, player):
        super().__init__(
            posicao_inicial=posicao_inicial,
            grupos=grupos,
            jogador=player, # O jogador já está definido como alvo na classe base
            game=game,
            dano=player.vida_maxima/2,
            velocidade=5000, # Velocidade do projétil, ajustada para o laser
            duracao=1500 # A duração em milissegundos
        )

        self.posicao_alvo_laser = pygame.math.Vector2(posicao_final)
        self.direcao = self.posicao_alvo_laser - self.posicao
        if self.direcao.length() > 0:
            self.direcao.normalize_ip()
        else:
            self.direcao = pygame.math.Vector2(1, 0)

        #sprite
        laser_img_original = pygame.transform.scale(pygame.image.load(join('assets', 'img', 'didact', 'laser.gif')).convert_alpha(), (150, 150))
        self.image = laser_img_original        
        # Calcula o ângulo em graus a partir da direção
        angulo = math.degrees(math.atan2(-self.direcao.y, self.direcao.x))
        self.image = pygame.transform.rotate(laser_img_original, angulo)        
        self.rect = self.image.get_rect(center=self.posicao)
        self.mask = pygame.mask.from_surface(self.image)

        #colisao
        self.ja_colidiu = False

    def update(self, delta_time):
        super().update(delta_time)
        self.rect.center = self.posicao
        

     