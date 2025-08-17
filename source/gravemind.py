import pygame
from game import *
from items import *
from enemies import *


class Gravemind(InimigoBase):
    def __init__(self, posicao, grupos, jogador, game):
        super().__init__(posicao, grupos, jogador, vida_base=50, dano_base=20, velocidade_base=35)
        self.game = game
        self.image = pygame.image.load(join('assets', 'img', 'gravemind.png')).convert_alpha()
        self.image = pygame.transform.scale(self.image, (450, 450))
        self.rect = self.image.get_rect(center=posicao)
        self.posicao = pygame.math.Vector2(self.rect.center)

        #respawns
        self.vida_limite = self.vida_base / 4

        #invocar infections
        self.tempo_invocacao = 0
        self.ultimo_spawn = 0
        self.numero_de_infeccao = 20
        self.intervalo_spawn_infeccao = 400
        self.cooldown_invocacao = 10000
        self.infecoes_restantes = 0


        #acid breath
        self.tempo_acido = 0
        self.numero_de_tiros = 20
        self.tempo_burst = 0
        self.intervalo_burst = 300
        self.cooldown_acid_breath = 10000
        self.tiros_restantes = 0

        #hitbox
        largura_hitbox = self.rect.width / 3
        self.hitbox = pygame.Rect(0, 0, largura_hitbox, self.rect.height)
        # Centraliza a hitbox no meio inferior do sprite principal
        self.hitbox.midbottom = self.rect.midbottom

    @property
    def collision_rect(self):
        """Retorna a hitbox específica do Gravemind."""
        return self.hitbox

    def invocar_infecao(self):
        Infection(posicao=self.posicao, grupos=(self.game.all_sprites, self.game.inimigos_grupo), jogador=self.jogador)

    def acid_breath(self):
        # Cria uma instância do novo projétil
        AcidBreath(
            posicao_inicial=self.posicao,
            grupos=(self.game.all_sprites, self.game.projeteis_grupo), 
            jogador=self.jogador,
            game=self.game
            )

    def morrer(self, grupos):
        if self.game.gravemind_reborns > 0:
            # Se ainda houver usos, apenas renascerá
            FloodWarning(posicao=self.posicao, grupos=self.game.all_sprites, game=self.game)
            self.kill()
            return
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
        self.tempo_invocacao += delta_time * 1000
        self.tempo_acido += delta_time * 1000

        #habilidade de respawn
        if (self.vida <= self.vida_limite and
            self.game.gravemind_reborns > 0):
            self.kill()
            # Spawna o aviso na posição do jogador
            FloodWarning(posicao=self.game.player.posicao, grupos=self.game.all_sprites, game=self.game)
            self.game.gravemind_reborns -= 1

        #inicia invocacao
        if self.tempo_invocacao >= self.cooldown_invocacao:
            self.tempo_invocacao = 0
            self.infecoes_restantes = self.numero_de_infeccao
            self.ultimo_spawn = 0
        #cooldown de spawn 
        if self.infecoes_restantes > 0:
            self.ultimo_spawn += delta_time * 1000
            if self.ultimo_spawn >= self.intervalo_spawn_infeccao:
                self.infecoes_restantes -= 1
                self.ultimo_spawn = 0
                self.invocar_infecao()
        
        #ativa acid breath
        if self.tempo_acido >= self.cooldown_acid_breath:
            self.tiros_restantes = self.numero_de_tiros
            self.tempo_acido = 0
            self.tempo_burst = 0
        #dispara
        if self.tiros_restantes > 0:
            self.tempo_burst += delta_time * 1000
            if self.tempo_burst >= self.intervalo_burst:
                self.tempo_burst = 0
                self.tiros_restantes -= 1
                self.acid_breath()
            

class AcidBreath(pygame.sprite.Sprite):
    def __init__(self, posicao_inicial, grupos, jogador, game):
        super().__init__(grupos)
        self.jogador = jogador
        self.game = game
        self.posicao = pygame.math.Vector2(posicao_inicial)
        
        # Atributos do projétil
        self.velocidade = 300  # Velocidade do projétil em pixels/segundo
        self.dano = 15         # Dano que o projétil causa no jogador
        
        # Aparência do projétil (imagem temporária)
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, 'red', (30, 30), 7)
        self.rect = self.image.get_rect(center=self.posicao)
        # Calcula a direção para o jogador no momento da criação
        direcao_para_jogador = self.jogador.posicao - self.posicao
        if direcao_para_jogador.length() > 0:
            self.direcao = direcao_para_jogador.normalize()
        else:
            self.direcao = pygame.math.Vector2(0, 0)
        
        # Define um tempo de vida para o projétil para ele não ficar para sempre
        self.tempo_criacao = pygame.time.get_ticks()
        self.duracao = 4000  # 4 segundos

    def update(self, delta_time):
        # Move o projétil na direção calculada
        self.posicao += self.direcao * self.velocidade * delta_time
        self.rect.center = self.posicao
        
        # Mata o projétil se o tempo de vida se esgotar
        if pygame.time.get_ticks() - self.tempo_criacao >= self.duracao:
            self.kill()

class FloodWarning(pygame.sprite.Sprite):
    def __init__(self, posicao, grupos, game):
        super().__init__(grupos)
        self.game = game
        self.posicao = pygame.math.Vector2(posicao)
        self.duracao = 2000  # Duração do aviso em milissegundos (3 segundos)
        self.raio = 600     # Raio do círculo de aviso
        self.dano = 50       # Dano que o jogador receberá se estiver dentro do círculo
        # Cria a sprite visual do círculo
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        self.image.set_colorkey((0,0,0)) # Torna a superfície preta transparente
        pygame.draw.circle(self.image, (100, 255, 0, 100), (self.raio, self.raio), self.raio)
        
        self.rect = self.image.get_rect(center=self.posicao)
        self.tempo_criacao = pygame.time.get_ticks()

    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        # Verifica se o tempo do aviso acabou
        if agora - self.tempo_criacao >= self.duracao:
            # Verifica a colisão com o jogador
            distancia_do_player = self.game.player.posicao.distance_to(self.posicao)
            if distancia_do_player <= self.raio:
                self.game.player.vida_atual -= self.dano
            self.game.spawnar_gravemind(self.posicao)        
            # Remove o círculo de aviso
            self.kill()
