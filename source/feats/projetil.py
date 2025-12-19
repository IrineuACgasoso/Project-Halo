from entitymanager import EntityManager
from enemies.enemies import *
from feats.items import *
from feats.weapon import *

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
        self.image = pygame.image.load(join('assets', 'img', 'plasmagun.png'))
        self.image = pygame.transform.scale(self.image, tamanho)
        self.rect = self.image.get_rect(center=self.posicao)

class Carabin(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, tamanho, dano, velocidade, duracao =2000):
        super().__init__(posicao_inicial, grupos, jogador, game, dano=dano, velocidade=velocidade, duracao=duracao)
        self.image = pygame.image.load(join('assets', 'img', 'carabin.png'))
        self.image = pygame.transform.scale(self.image, tamanho)
        self.rect = self.image.get_rect(center=self.posicao)

class M50(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, tamanho, dano, velocidade):
        super().__init__(posicao_inicial, grupos, jogador, game, dano=dano, velocidade=velocidade, duracao=2500)
        self.image = pygame.image.load(join('assets', 'img', 'm50.png'))
        self.image = pygame.transform.scale(self.image, tamanho)
        self.rect = self.image.get_rect(center=self.posicao)

class Dizimator(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, tamanho, dano, velocidade, duracao = 1500):
        super().__init__(posicao_inicial, grupos, jogador, game, dano=dano, velocidade=velocidade, duracao=duracao)
        self.image = pygame.image.load(join('assets', 'img', 'dizimator.png'))
        self.image = pygame.transform.scale(self.image, tamanho)
        self.rect = self.image.get_rect(center=self.posicao)

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

class CannonBeam(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, dano, velocidade, duracao):
        self.posicao = pygame.math.Vector2(posicao_inicial)
        super().__init__(posicao_inicial, grupos, jogador, game, dano=dano, velocidade=velocidade, duracao=duracao)
        #sprite
        self.image = pygame.transform.scale(pygame.image.load(join('assets', 'img', 'hunter', 'cannon.png')).convert_alpha(), (150, 150))
        #hitbox
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

    def update(self, delta_time):
        # Atualiza a posição com base na direção e velocidade
        self.posicao += self.direcao * self.velocidade * delta_time
        self.rect.center = self.posicao
        
        # Verifica se o projétil passou da duração para removê-lo
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_criacao >= self.duracao:
            self.kill()


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
        
class LaserBeam(ProjetilInimigoBase):
    def __init__(self, posicao_inimigo, grupos, jogador, game, dano, velocidade, duracao):
        super().__init__(posicao_inimigo, grupos, jogador, game, dano=dano, velocidade=velocidade, duracao=duracao)

        self.dano_aplicado = False

        #sprite do laser
        self.image = pygame.transform.scale(pygame.image.load(join('assets', 'img', 'guilty', 'laser.png')).convert_alpha(), (150, 15))
        
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
