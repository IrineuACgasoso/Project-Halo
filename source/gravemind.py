import pygame
from game import *
from items import *
from enemies import *
import random


class Gravemind(InimigoBase):
    def __init__(self, posicao, grupos, jogador, game, is_final_form = False):
        super().__init__(posicao, grupos, jogador, game, vida_base=40, dano_base=20, velocidade_base=35)
        self.game = game
        self.is_final_form = is_final_form

        #Carrega a sprite e animacao da forma final
        if self.is_final_form:
            self.sprite_principal = pygame.image.load(join('assets', 'img', 'gravemind', 'proto1.png')).convert_alpha()
            self.animacao_padrao = [self.sprite_principal, pygame.image.load(join('assets', 'img', 'gravemind', 'proto2.png')).convert_alpha()]
            self.ataque_sprite = pygame.transform.scale(pygame.image.load(join('assets', 'img', 'gravemind', 'proto3.png')).convert_alpha(), (600,600))
            self.tamanho_sprite = (600, 600)
            self.vida = 1000
            self.dano = 50

        else:
            #Carrega o grave padrão
            self.sprite_principal = pygame.image.load(join('assets', 'img', 'gravemind', 'gravemind.png')).convert_alpha()
            self.animacao_padrao = [self.sprite_principal, pygame.image.load(join('assets', 'img', 'gravemind', 'grave2.png')).convert_alpha()]
            self.ataque_sprite = pygame.transform.scale(pygame.image.load(join('assets', 'img', 'gravemind', 'grave3.png')).convert_alpha(), (450, 450))
            self.tamanho_sprite = (450, 450)
            self.vida = 50
            self.dano = 20

        # Redimensiona as sprites de acordo com a forma
        self.animacao_gravemind = []
        for img in self.animacao_padrao:
            self.animacao_gravemind.append(pygame.transform.scale(img, self.tamanho_sprite))

        # Variáveis de animação do 'enrolar'
        self.altura_atual = 0 
        self.estado_respawn = 'reaparecendo' 
        self.velocidade_animacao_respawn = 400
        self.is_animating_respawn = True

        # Atribuir a imagem inicial e o rect agora, para que tenham o tamanho correto
        self.image = self.animacao_gravemind[0]
        self.rect = self.image.get_rect(centerx=posicao[0], bottom=posicao[1])
        self.posicao = pygame.math.Vector2(self.rect.center)
        #hitbox
        nova_largura = self.rect.width / 3
        self.hitbox = pygame.Rect(0, 0, nova_largura, self.rect.height)
        self.hitbox.center = self.rect.center

        self.frame_atual = 0
        self.velocidade_animacao = 400
        self.ultimo_update_animacao = pygame.time.get_ticks()

        #respawns
        self.vida_limite = self.vida_base / 4

        # Variável para controlar o estado da animação
        self.estado_animacao = 'normal'

        #invocar infections
        self.tempo_invocacao = 0
        self.ultimo_spawn = 0
        self.numero_de_infeccao = 5
        self.intervalo_spawn_infeccao = 250
        self.cooldown_invocacao = 8000
        self.infecoes_restantes = 0
        if self.is_final_form:
            self.numero_de_infeccao = 20
            self.intervalo_spawn_infeccao = 100
            self.cooldown_invocacao = 5000
            

        #acid breath
        self.tempo_acido = 0
        self.numero_de_tiros = 10
        self.tempo_burst = 0
        self.intervalo_burst = 250
        self.cooldown_acid_breath = 8000
        self.tiros_restantes = 0
        if self.is_final_form:
            self.numero_de_tiros = 20
            self.intervalo_burst = 100
            self. cooldown_acid_breath = 6000

        #invocacao de graveminds (exclusiva do proto gravemind)
        if self.is_final_form:
            self.tempo_cabecas = 0
            self.numero_cabeças = 5
            self.cooldown_cabecas = 12000
            self.cabecas_restantes = 0

    @property
    def collision_rect(self):
        """Retorna a hitbox específica do Gravemind."""
        return self.hitbox
    
    def atualizar_sprite_respawn(self, delta_time):
        if self.estado_respawn == 'reaparecendo':
            self.altura_atual += self.velocidade_animacao_respawn * delta_time
            if self.altura_atual >= self.tamanho_sprite[1]:
                self.altura_atual = self.tamanho_sprite[1]
                self.is_animating_respawn = False
                self.estado_respawn = 'idle'
        elif self.estado_respawn == 'desaparecendo':
            self.altura_atual -= self.velocidade_animacao_respawn * delta_time
            if self.altura_atual <= 0:
                self.altura_atual = 0
                self.is_animating_respawn = False
                self.respawn()
        largura, _ = self.tamanho_sprite
        nova_imagem = pygame.transform.scale(self.sprite_principal, (largura, max(1, self.altura_atual)))
        old_bottom = self.rect.bottom
        self.image = nova_imagem
        self.rect = self.image.get_rect(bottom=old_bottom, centerx=self.posicao.x)

    def respawn(self):
        if self.game.gravemind_reborns > 1:
            self.game.gravemind_reborns -= 1
            # Spawna o aviso na posição do jogador e se destrói
            FloodWarning(posicao=self.jogador.posicao, grupos=self.game.all_sprites, game=self.game)
        elif self.game.gravemind_reborns == 1:
            if self.game.invocacao_protogravemind == 0:
                self.game.invocacao_protogravemind += 1
                ProtoGravePit(posicao=self.jogador.posicao, grupos=self.game.all_sprites, game=self.game)
        self.kill()

    def invocar_infecao(self):
        novo_cooldown = [7500, 8000, 9000, 10000]
        self.cooldown_invocacao = random.choice(novo_cooldown)
        deslocamento_x = randint(-150, 150)
        deslocamento_y = randint(-150, 150)
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
            grupos=(self.game.all_sprites, self.game.projeteis_inimigos_grupo), 
            jogador=self.jogador,
            game=self.game
            )
    
    def invocar_cabecas(self):
        deslocamento_x = randint(-1200, 1200)
        deslocamento_y = randint(-700, 700)
        posicao_spawn_aleatoria = self.jogador.posicao + pygame.math.Vector2(deslocamento_x, deslocamento_y)
        FloodWarning(posicao=posicao_spawn_aleatoria, grupos=self.game.all_sprites, game=self.game)

    def morrer(self, grupos):
        if not self.is_final_form and self.game.gravemind_reborns > 0:
            return
        self.game.gravemind_reborns = 3 
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
        if self.is_animating_respawn:
            self.atualizar_sprite_respawn(delta_time)
            # Retorna para não executar o resto do código enquanto anima
            return
        #Lógica de morte para iniciar a animação de desaparecimento
        if not self.is_final_form and self.vida <= self.vida_limite: 
            self.estado_respawn = 'desaparecendo'
            self.is_animating_respawn = True
            self.vida = self.vida_base
        
        self.tempo_invocacao += delta_time * 1000
        self.tempo_acido += delta_time * 1000
        if self.is_final_form:
            self.tempo_cabecas += delta_time * 1000

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
            novo_cooldown = [6000, 8000, 10000, 12000]
            self.cooldown_acid_breath = random.choice(novo_cooldown)
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

        if self.is_final_form:
            #inicia o spawn de cabecas
            if self.tempo_cabecas >= self.cooldown_cabecas and self.cabecas_restantes==0:
                novo_cooldown_ultimate = [10000, 12000, 15000, 18000]
                self.cooldown_cabecas = random.choice(novo_cooldown_ultimate)
                self.cabecas_restantes = self.numero_cabeças
                self.tempo_cabecas = 0
            if self.cabecas_restantes > 0:
                self.cabecas_restantes -= 1
                self.tempo_cabecas = 0
                self.invocar_cabecas()
        
        if not self.is_animating_respawn:
            self.animar()
            

class AcidBreath(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game):
        super().__init__(posicao_inicial, grupos, jogador, game, dano=25,velocidade=400, duracao=2700)
        self.jogador = jogador
        self.game = game
        self.posicao = pygame.math.Vector2(posicao_inicial)

        # Aparência do projétil (imagem temporária)
        self.image = pygame.image.load(join('assets', 'img', 'gravemind', 'acid_breath.png')).convert_alpha()
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
        self.raio = 200     # Raio do círculo de aviso
        self.dano = 100      # Dano que o jogador receberá se estiver dentro do círculo
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

class ProtoGravePit(pygame.sprite.Sprite):
    def __init__(self, posicao, grupos, game):
        super().__init__(grupos)
        
        self.game = game 
        self.posicao = pygame.math.Vector2(posicao)
        self.duracao = 4000 
        self.raio = 500      
        self.dano = 10000 

        # Cria a sprite visual do círculo
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        self.image.set_colorkey((0, 0, 0))
        pygame.draw.circle(self.image, (255, 0, 0, 150), (self.raio, self.raio), self.raio)
        
        self.rect = self.image.get_rect(center=self.posicao)
        self.tempo_criacao = pygame.time.get_ticks()

    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        # Verifica se o tempo do aviso acabou
        if agora - self.tempo_criacao >= self.duracao:
            # Verifica a colisão com o jogador e causa dano
            distancia_do_player = self.game.player.posicao.distance_to(self.posicao)
            if distancia_do_player <= self.raio:
                self.game.player.vida_atual -= self.dano
            #Proto Gravemind
            Gravemind(
                posicao=self.posicao,
                grupos=(self.game.all_sprites, self.game.inimigos_grupo),
                jogador=self.game.player,
                game=self.game,
                is_final_form=True  
            )
                
            self.kill()
