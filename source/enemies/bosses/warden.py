import pygame
from source.feats.items import *
from source.enemies.enemies import *
from source.player.player import *
from source.enemies.minibosses.knight import Knight
import random
import math
from source.systems.entitymanager import entity_manager

class WardenEternal(InimigoBase):
    def __init__(self, posicao, game, grupos, clone = False):
        if clone:
            valor_vida = 10000
            velocidade_base = 100
        else:
            valor_vida = 7000
            velocidade_base = 80
        super().__init__(posicao, vida_base=valor_vida, dano_base=90, velocidade_base=velocidade_base, sprite_key = 'warden')
        self.titulo = "WARDEN ETERNAL, O Guardião do Domínio"
        self.game = game
        self.vida = valor_vida
        self.vida_base = valor_vida
        #sprites
        # Original
        if clone == False:
            self.sprites = self.get_sprites('default')
        # Clone
        else:
            self.sprites = self.get_sprites('clone')

        # Inicia a animação
        self.frame_atual = 0
        self.estado_animacao = 'right' 
        self.velocidade_animacao = 300 # Milissegundos por frame
        self.ultimo_update_animacao = pygame.time.get_ticks()
        
        # Define a imagem e o retângulo inicial
        self.image = self.sprites[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center=self.posicao)

        # Cria a hitbox do warden
        self.mask = pygame.mask.from_surface(self.image)

        #Clone
        self.clone = clone
        if not self.clone:
            self.clones_restantes = 2
        else:
            self.clones_restantes = 0
        self.vida_limite = 0.66 * self.vida_base

        #Invocacao de royal knight
        if not self.clone:
            self.cooldown_knight = 5000
            self.ultimo_knight = 0

        #Chop
        self.cooldown_chop = 5000
        self.ultimo_chop = 0

    @property
    def collision_rect(self):
        return self.mask
    
    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.posicao)
            # Recrie a hitbox aqui para que ela se adapte ao novo tamanho
            self.hitbox = pygame.Rect(0, 0, self.rect.width * 0.6, self.rect.height * 0.9)
            self.hitbox.center = self.rect.center

    def clonar(self):
        # Cria dois novos clones
        for _ in range(2):
            # Posiciona os clones um pouco distantes do original
            posicao_clone = self.posicao + pygame.math.Vector2(random.randint(-700, 700), random.randint(-700, 700))
            
            # Instancia o clone com 'clone=True'
            clone = WardenEternal(
                posicao=posicao_clone,
                grupos=self.grupos,
                jogador=self.jogador,
                game=self.game,
                clone=True
            )
            # Adiciona o clone ao grupo de inimigos
            entity_manager.inimigos_grupo.add(clone)
        # Zera os clones restantes para que o boss não clone novamente
        self.clones_restantes = 0

    def knight(self):
        Knight(
            posicao=self.posicao,
            grupos=self.grupos,
            jogador=self.jogador,
            game=self.game
            )  

    def chop(self):
        # Calcula a direção do inimigo para o jogador
        direcao = self.jogador.posicao - self.posicao
        
        # O ângulo_para_o_jogador é o ângulo em graus (0 a 360) da direção
        angulo_para_o_jogador = direcao.angle_to(pygame.math.Vector2(1, 0))

        # Cria a instância do ataque em cone
        WardenChop(
            posicao=self.posicao,
            angulo=angulo_para_o_jogador,
            grupos=self.game.all_sprites,
            jogador=self.jogador,
            game=self.game
        )

    def morrer(self, grupos = None):
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 8, 100)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 100)
        Items.spawn_drop(self.posicao, grupos, 'cafe', 1, 1)
        self.kill()

    def update(self, delta_time, paredes= None):
        direcao = (self.jogador.posicao - self.posicao)
        agora = pygame.time.get_ticks()
        if direcao.length() > 0:
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * delta_time
            if paredes:
                self.aplicar_colisao_mapa(paredes, self.raio_colisao_mapa)
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        #invocacao de knights
        if not self.clone:
            if agora - self.ultimo_knight >= self.cooldown_knight:
                novo_cooldown = [18000, 21000, 24000, 27000]
                self.cooldown_knight = random.choice(novo_cooldown)
                self.ultimo_knight = agora
                self.knight()
        # Lógica de criação de clones
        if self.clones_restantes > 0 and self.vida <= self.vida_limite:
            self.clonar()
        #ativa chop
        if agora - self.ultimo_chop >= self.cooldown_chop and (self.jogador.posicao - self.posicao).length() < 700:
            novo_cooldown = [5000,7000,9000, 11000]
            self.cooldown_chop = random.choice(novo_cooldown)
            self.ultimo_chop = agora
            self.velocidade = 0
            self.chop()
        if agora - self.ultimo_chop >= 2000:
            self.velocidade = self.velocidade_base
        if direcao.x < 0:
                self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'
        self.animar()

class WardenChop(pygame.sprite.Sprite):
    def __init__(self, posicao, angulo, grupos, jogador, game, dano=400, duracao=2000):
        super().__init__(grupos)
        
        self.game = game
        self.jogador = jogador
        self.posicao = pygame.math.Vector2(posicao)
        self.angulo = angulo
        
        self.dano = dano
        self.duracao = duracao 
        self.raio_do_cone = 900 
        self.largura_do_cone = 120
        
        self.image = pygame.Surface((self.raio_do_cone * 2, self.raio_do_cone * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.posicao)
        
        self.tempo_criacao = pygame.time.get_ticks()
        
    def _desenhar_cone_com_cor(self, cor_rgba):
        self.image.fill((0, 0, 0, 0)) # Limpa a superfície
        
        cor_rgb = cor_rgba[:3]
        alpha = cor_rgba[3]
        
        # Ponto central do cone, que será o primeiro e o último vértice do polígono
        centro_x, centro_y = self.raio_do_cone, self.raio_do_cone
        
        # Converte os ângulos de graus para radianos para as funções trigonométricas
        angulo_inicial_rad = math.radians(self.angulo - self.largura_do_cone / 2)
        angulo_final_rad = math.radians(self.angulo + self.largura_do_cone / 2)

        # O número de pontos define a suavidade do arco
        num_pontos = 50 
        
        # Cria a lista de vértices do polígono
        vertices = [(centro_x, centro_y)]

        # Cria os pontos ao longo do arco
        for i in range(num_pontos + 1):
            angulo_atual_rad = angulo_inicial_rad + (angulo_final_rad - angulo_inicial_rad) * i / num_pontos
            x = centro_x + self.raio_do_cone * math.cos(angulo_atual_rad)
            y = centro_y + self.raio_do_cone * -math.sin(angulo_atual_rad)
            vertices.append((x, y))

        # Desenha o polígono preenchido
        pygame.draw.polygon(self.image, cor_rgb, vertices)
        
        self.image.set_alpha(alpha)

    def _is_angle_between(self, angulo_teste, angulo_min, angulo_max):
        angulo_teste = angulo_teste % 360
        angulo_min = angulo_min % 360
        angulo_max = angulo_max % 360

        if angulo_min > angulo_max:
            return (angulo_teste >= angulo_min) or (angulo_teste <= angulo_max)
        else:
            return (angulo_teste >= angulo_min) and (angulo_teste <= angulo_max)
        
    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        tempo_passado = agora - self.tempo_criacao
        
        if tempo_passado < self.duracao * 0.8:
            self._desenhar_cone_com_cor((255, 160, 0, 200))
        else:
            self._desenhar_cone_com_cor((255, 0, 0, 200))
            
        self.rect.center = self.posicao
        
        if tempo_passado >= self.duracao:
            distancia_do_player = self.jogador.posicao.distance_to(self.posicao)
            
            if distancia_do_player <= self.raio_do_cone:
                direcao_para_o_jogador = self.jogador.posicao - self.posicao
                angulo_do_jogador = direcao_para_o_jogador.angle_to(pygame.math.Vector2(1, 0))
                
                angulo_min = self.angulo - self.largura_do_cone / 2
                angulo_max = self.angulo + self.largura_do_cone / 2

                if self._is_angle_between(angulo_do_jogador, angulo_min, angulo_max):
                    self.jogador.tomar_dano_direto(self.dano)
            
            self.kill()



    