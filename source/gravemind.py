import pygame
from game import *
from items import *
from enemies import *


class Gravemind(InimigoBase):
    def __init__(self, posicao, grupos, jogador, game):
        super().__init__(posicao, grupos, jogador, game, vida_base=250, dano_base=20, velocidade_base=35)
        self.game = game
        self.image = pygame.image.load(join('assets', 'img', 'gravemind', 'gravemind.png')).convert_alpha()
        self.image = pygame.transform.scale(self.image, (450, 450))
        self.rect = self.image.get_rect(center=posicao)
        self.posicao = pygame.math.Vector2(self.rect.center)

        #respawns
        self.vida_limite = self.vida_base / 4

        #animacao
        self.animacao_gravemind_original = [
            pygame.image.load(join('assets', 'img', 'gravemind', 'gravemind.png')).convert_alpha(),
            pygame.image.load(join('assets', 'img', 'gravemind', 'grave2.png')).convert_alpha(),
        ]
        self.ataque_sprite = pygame.transform.scale(pygame.image.load(join('assets', 'img', 'gravemind', 'grave3.png')).convert_alpha(), (450, 450))
        self.animacao_gravemind = []
        for img in self.animacao_gravemind_original:
            scaled_img = pygame.transform.scale(img, (450, 450))
            self.animacao_gravemind.append(scaled_img)
        
        self.frame_atual = 0
        self.image = self.animacao_gravemind[self.frame_atual]
        self.rect = self.image.get_rect(center=posicao)
        self.posicao = pygame.math.Vector2(self.rect.center)
        
        self.velocidade_animacao = 400
        self.ultimo_update_animacao = pygame.time.get_ticks()

        # Variável para controlar o estado da animação
        self.estado_animacao = 'normal'

        #invocar infections
        self.tempo_invocacao = 0
        self.ultimo_spawn = 0
        self.numero_de_infeccao = 20
        self.intervalo_spawn_infeccao = 250
        self.cooldown_invocacao = 8000
        self.infecoes_restantes = 0

        #acid breath
        self.tempo_acido = 0
        self.numero_de_tiros = 20
        self.tempo_burst = 0
        self.intervalo_burst = 250
        self.cooldown_acid_breath = 8000
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
        deslocamento_x = randint(-100, 100)
        deslocamento_y = randint(-100, 100)
        posicao_spawn_aleatoria = self.posicao + pygame.math.Vector2(deslocamento_x, deslocamento_y)

        Infection(
        posicao=posicao_spawn_aleatoria, 
        grupos=(self.game.all_sprites, self.game.inimigos_grupo), 
        jogador=self.jogador,
        game= self.game
        )

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

    def animar(self):
        agora = pygame.time.get_ticks()
        # Verifica se já passou tempo suficiente para mudar de frame
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            # Avança para o próximo frame
            self.frame_atual = (self.frame_atual + 1) % len(self.animacao_gravemind)
            self.image = self.animacao_gravemind[self.frame_atual]
            # O rect precisa ser atualizado para a nova imagem, mas a posição não muda
            self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, delta_time):
        self.animar()
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
                self.estado_animacao = 'atacando' # NOVO: Define o estado para ataque
                self.image = self.ataque_sprite
                self.acid_breath()
        if self.tiros_restantes == 0:
            self.estado_animacao = 'normal'
            

class AcidBreath(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game):
        super().__init__(posicao_inicial, grupos, jogador, game, dano=15,velocidade=300, duracao=4000)
        self.jogador = jogador
        self.game = game
        self.posicao = pygame.math.Vector2(posicao_inicial)

        # Aparência do projétil (imagem temporária)
        self.image = pygame.image.load(join('assets', 'img', 'acid_breath.png')).convert_alpha()
        self.image = pygame.transform.scale(self.image, (48, 48))
        self.rect = self.image.get_rect(center=self.posicao)
        # Calcula a direção para o jogador no momento da criação
        direcao_para_jogador = self.jogador.posicao - self.posicao
        if direcao_para_jogador.length() > 0:
            self.direcao = direcao_para_jogador.normalize()
        else:
            self.direcao = pygame.math.Vector2(0, 0)


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
        self.duracao = 3000  # Duração do aviso em milissegundos (3 segundos)
        self.raio = 500     # Raio do círculo de aviso
        self.dano = 10000      # Dano que o jogador receberá se estiver dentro do círculo
        # Cria a sprite visual do círculo
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        self.image.set_colorkey((0,0,0)) # Torna a superfície preta transparente
        pygame.draw.circle(self.image, (255, 100, 0, 100), (self.raio, self.raio), self.raio)
        
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
            Gravemind(
                posicao=self.posicao, 
                grupos=(self.game.all_sprites, self.game.inimigos_grupo),
                jogador=self.game.player,
                game=self.game
            )        
            # Remove o círculo de aviso
            self.kill()
