from entitymanager import EntityManager
from enemies.enemies import *
from feats.items import *
from feats.weapon import *
from feats.assets import *

#PROJETEIS INIMIGOS
class ProjetilInimigoBase(pygame.sprite.Sprite):
    def __init__(self, posicao_inicial, grupos, jogador, game, dano, velocidade, duracao):
        super().__init__(grupos)
        self.jogador = jogador
        self.game = game
        self.posicao = pygame.math.Vector2(posicao_inicial)
        
        #status
        self.dano = dano
        self.velocidade = velocidade
        self.duracao = duracao

        # Aparência
        self.image = pygame.Surface((20,20))
        self.rect = self.image.get_rect(center=self.posicao)

        # Calcula a direção para o jogador
        direcao_para_jogador = self.jogador.posicao - self.posicao
        if direcao_para_jogador.length() > 0:
            self.direcao = direcao_para_jogador.normalize()
        else:
            self.direcao = pygame.math.Vector2(0, 0)
        
        self.tempo_criacao = pygame.time.get_ticks()

    def update(self, delta_time):
        self.posicao += self.direcao * self.velocidade * delta_time
        self.rect.center = self.posicao
        
        # Mata o projétil se o tempo de vida se esgotar
        if pygame.time.get_ticks() - self.tempo_criacao >= self.duracao:
            self.kill()

class PlasmaGun(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, tamanho, dano, velocidade):
        super().__init__(posicao_inicial, grupos, jogador, game, dano=dano, velocidade=velocidade, duracao=3000)
        self.image = pygame.transform.scale(ASSETS['projectiles']['plasma'], tamanho)
        self.rect = self.image.get_rect(center=self.posicao)

class Carabin(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, tamanho, dano, velocidade, duracao =2000):
        super().__init__(posicao_inicial, grupos, jogador, game, dano=dano, velocidade=velocidade, duracao=duracao)
        self.image = pygame.transform.scale(ASSETS['projectiles']['carabin'], tamanho)
        self.rect = self.image.get_rect(center=self.posicao)

class M50(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, tamanho, dano, velocidade):
        super().__init__(posicao_inicial, grupos, jogador, game, dano=dano, velocidade=velocidade, duracao=2500)
        self.image = pygame.transform.scale(ASSETS['projectiles']['m50'], tamanho)    
        self.rect = self.image.get_rect(center=self.posicao)

class Dizimator(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, tamanho, dano, velocidade, duracao = 1500):
        super().__init__(posicao_inicial, grupos, jogador, game, dano=dano, velocidade=velocidade, duracao=duracao)
        self.image = pygame.transform.scale(ASSETS['projectiles']['dizimator'], tamanho)
        self.rect = self.image.get_rect(center=self.posicao)

class CannonBeam(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, dano, velocidade, duracao):
        super().__init__(posicao_inicial, grupos, jogador, game, dano=dano, velocidade=velocidade, duracao=duracao)
        
        # Sprite e Animação
        self.sprites = [pygame.transform.scale(img, (80, 80)) for img in ASSETS['projectiles']['cannon']]

        self.frame_atual = 0
        self.velocidade_animacao = 150
        self.ultimo_update_animacao = pygame.time.get_ticks()
        self.image = self.sprites[self.frame_atual]
        self.rect = self.image.get_rect(center=self.posicao)

        # Cria um novo retângulo menor para a colisão
        tamanho_hitbox = (75, 75)  # Ajuste este valor para o tamanho correto do feixe
        self.rect = pygame.Rect(0, 0, tamanho_hitbox[0], tamanho_hitbox[1])
        self.rect.center = self.image.get_rect(center=self.posicao).center
        #direcao
        direcao = self.jogador.posicao - self.posicao
        if direcao.length() > 0:
            self.direcao = direcao.normalize()
        else:
            self.direcao = pygame.math.Vector2(1, 0)
        #self kill
        self.tempo_criacao = pygame.time.get_ticks()

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites)
            self.image = self.sprites[self.frame_atual]

    def update(self, delta_time):
        super().update(delta_time)
        self.animar()


class Laser(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, posicao_final, grupos, game, player):
        super().__init__(
            posicao_inicial=posicao_inicial,
            grupos=grupos,
            jogador=player, # O jogador já está definido como alvo na classe base
            game=game,
            dano=player.vida_maxima/2,
            velocidade=2500, # Velocidade do projétil, ajustada para o laser
            duracao=2500 # A duração em milissegundos
        )
        tamanho = (150, 150)
        self.posicao_alvo_laser = pygame.math.Vector2(posicao_final)
        self.direcao = self.posicao_alvo_laser - self.posicao
        if self.direcao.length() > 0:
            self.direcao.normalize_ip()
        else:
            self.direcao = pygame.math.Vector2(1, 0)

        #sprite
        laser_img_original = pygame.transform.scale(ASSETS['projectiles']['laser'], tamanho)

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

class AcidBreath(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, velocidade):
        super().__init__(posicao_inicial, grupos, jogador, game, dano=25, velocidade=velocidade, duracao=2700)
        self.jogador = jogador
        self.game = game
        self.posicao = pygame.math.Vector2(posicao_inicial)

        # Aparência do projétil (imagem temporária)
        tamanho = (48, 48)
        self.image = pygame.transform.scale(ASSETS['projectiles']['acid_breath'], tamanho)
        self.rect = self.image.get_rect(center=self.posicao)
        # Calcula a direção para o jogador no momento da criação
        direcao_para_jogador = self.jogador.posicao - self.posicao
        if direcao_para_jogador.length() > 0:
            self.direcao = direcao_para_jogador.normalize()
        else:
            self.direcao = pygame.math.Vector2(0, 0)

        
class LaserBeam(ProjetilInimigoBase):
    def __init__(self, posicao_inimigo, grupos, jogador, game, dano, velocidade, duracao, color):
        super().__init__(posicao_inimigo, grupos, jogador, game, dano=dano, velocidade=velocidade, duracao=duracao)

        self.dano_aplicado = False
        
        tamanho = (120, 12)
        # Sprite do Laser
        if color == 'red':
            self.image = pygame.transform.scale(ASSETS['projectiles']['red_laser'], tamanho)
        else:
            self.image = pygame.transform.scale(ASSETS['projectiles']['blue_laser'], tamanho)

        
        # Calcula a direção do GuiltySpark para o jogador
        self.direcao = (self.jogador.posicao - self.posicao).normalize()

        # Rotaciona a sprite do laser na direção do tiro
        angulo = self.direcao.as_polar()[1]
        self.image = pygame.transform.rotate(self.image, -angulo)
        self.image.set_alpha(255)
        
        self.rect = self.image.get_rect(center=self.posicao)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        tempo_decorrido = agora - self.tempo_criacao
        
        # Move o projétil a cada frame
        self.posicao += self.direcao * self.velocidade * delta_time
        self.rect.center = self.posicao
        
        # Lógica de colisão
        if not self.dano_aplicado and pygame.sprite.collide_mask(self, self.jogador):
            self.jogador.tomar_dano_direto(self.dano)
            self.dano_aplicado = True
        
        # Destrói o projétil após a duração
        if tempo_decorrido >= self.duracao:
            self.kill()
