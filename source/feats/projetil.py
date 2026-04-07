from source.systems.entitymanager import entity_manager
from source.enemies.enemies import *
from source.feats.items import *
from source.feats.weapons import *
from source.feats.assets import *
import math

#PROJETIL INIMIGO BASE
class ProjetilInimigoBase(pygame.sprite.Sprite):
    GLOBAL_PROJECTILE_CACHE = {}

    def __init__(self, posicao_inicial, grupos, jogador, game, dano, velocidade, duracao, 
                 tamanho=(20, 20), sprite_key=None, direcao_custom=None):
        super().__init__(grupos)
        # 1. ATRIBUTOS BÁSICOS (Definir antes de qualquer lógica visual)
        self.game = game
        self.jogador = jogador
        self.dano = dano
        self.velocidade = velocidade
        self.duracao = duracao
        self.spawn_time = pygame.time.get_ticks()
        self.posicao = pygame.math.Vector2(posicao_inicial)

        # 2. DEFINIR DIREÇÃO (Obrigatório para a rotação funcionar)
        if direcao_custom is not None:
            if isinstance(direcao_custom, pygame.math.Vector2):
                self.direcao = direcao_custom
            else:
                self.direcao = pygame.math.Vector2(direcao_custom)
        else:
            # Se não houver direção customizada, mira no jogador
            alvo = self.jogador.posicao - self.posicao
            if alvo.length() > 0:
                self.direcao = alvo.normalize()
            else:
                self.direcao = pygame.math.Vector2(1, 0) # Direção padrão caso esteja em cima do player

        # 3. GERENCIAR VISUAL (Agora self.direcao já existe!)
        if sprite_key and sprite_key in ASSETS['projectiles']:
            self.chave_cache = f"{sprite_key}_{tamanho[0]}x{tamanho[1]}"
            self.image_base = self.obter_imagem_base(sprite_key, tamanho)
            self.image = self.renderizar_com_rotacao()
        else:
            self.image = pygame.Surface(tamanho, pygame.SRCALPHA)
            self.image.fill((255, 0, 255))

        self.rect = self.image.get_rect(center=self.posicao)
        self.mask = pygame.mask.from_surface(self.image)

    @staticmethod
    def limpar_cache_global():
        ProjetilInimigoBase.GLOBAL_PROJECTILE_CACHE.clear()

    def obter_imagem_base(self, sprite_key, tamanho):
        """ Garante que o pygame.transform.scale só ocorra UMA vez por tipo de projétil """
        # Usamos uma sub-chave para a imagem original escalada
        base_key = f"base_{sprite_key}_{tamanho[0]}x{tamanho[1]}"
        if base_key not in ProjetilInimigoBase.GLOBAL_PROJECTILE_CACHE:
            ProjetilInimigoBase.GLOBAL_PROJECTILE_CACHE[base_key] = pygame.transform.scale(ASSETS['projectiles'][sprite_key], tamanho)
        return ProjetilInimigoBase.GLOBAL_PROJECTILE_CACHE[base_key]

    def renderizar_com_rotacao(self):
        """ O CORAÇÃO DO LAZY LOADING """
        # 1. Prepara o dicionário daquela arma se não existir
        if self.chave_cache not in ProjetilInimigoBase.GLOBAL_PROJECTILE_CACHE:
            ProjetilInimigoBase.GLOBAL_PROJECTILE_CACHE[self.chave_cache] = {}

        # 2. Calcula o ângulo
        angulo_exato = math.degrees(math.atan2(-self.direcao.y, self.direcao.x))
        angulo_int = int(round(angulo_exato)) % 360

        # 3. LAZY LOADING: Só rotaciona se este ângulo específico nunca foi pedido
        if angulo_int not in ProjetilInimigoBase.GLOBAL_PROJECTILE_CACHE[self.chave_cache]:
            #print(f"[CACHE] Gerando nova rotação: {self.chave_cache} Angulo: {angulo_int}")
            ProjetilInimigoBase.GLOBAL_PROJECTILE_CACHE[self.chave_cache][angulo_int] = \
                pygame.transform.rotate(self.image_base, angulo_int)

        return ProjetilInimigoBase.GLOBAL_PROJECTILE_CACHE[self.chave_cache][angulo_int]
    
    def update(self, delta_time):
        # Movimento
        self.posicao += self.direcao * self.velocidade * delta_time
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        # Cooldown de vida
        if pygame.time.get_ticks() - self.spawn_time > self.duracao:
            self.kill()

# --- CLASSES FILHAS SIMPLIFICADAS ---

class PlasmaGun(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, tamanho, dano, velocidade, direcao_spread):
        super().__init__(posicao_inicial, grupos, jogador, game, dano, velocidade, 
                         duracao=3000, tamanho=tamanho, sprite_key='plasma', direcao_custom=direcao_spread)

class Carabin(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, tamanho, dano, velocidade, duracao=2000, is_Banished=False):
        s_key = 'bcarabin' if is_Banished else 'carabin'
        super().__init__(posicao_inicial, grupos, jogador, game, dano, velocidade, 
                         duracao=duracao, tamanho=tamanho, sprite_key=s_key)

class M50(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, tamanho, dano, velocidade):
        super().__init__(posicao_inicial, grupos, jogador, game, dano, velocidade, 
                         duracao=2500, tamanho=tamanho, sprite_key='m50')

class Dizimator(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, tamanho, dano, velocidade, duracao=1500):
        super().__init__(posicao_inicial, grupos, jogador, game, dano, velocidade, 
                         duracao=duracao, tamanho=tamanho, sprite_key='dizimator')

class BurstRifle(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, tamanho, dano, velocidade, direcao_spread):
        super().__init__(posicao_inicial, grupos, jogador, game, dano, velocidade, 
                         duracao=2000, tamanho=tamanho, sprite_key='ar', direcao_custom=direcao_spread)

class LightRifle(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, tamanho, dano, velocidade, direcao_spread):
        super().__init__(posicao_inicial, grupos, jogador, game, dano, velocidade, 
                         duracao=2000, tamanho=tamanho, sprite_key='lightrifle', direcao_custom=direcao_spread)

class AcidBreath(ProjetilInimigoBase):
    def __init__(self, posicao_inicial, grupos, jogador, game, velocidade):
        super().__init__(posicao_inicial, grupos, jogador, game, dano=25, velocidade=velocidade, 
                         duracao=2700, tamanho=(48, 48), sprite_key='acid_breath')
        
class LaserBeam(ProjetilInimigoBase):
    """ Usado pelo Scarab e GuiltySpark """
    def __init__(self, posicao_inicial, grupos, jogador, game, dano, velocidade, duracao, color='red', tamanho=(120, 12)):
        if color == 'red':
            s_key = 'red_laser'
        elif color == 'blue':
            s_key = 'blue_laser'
        else:
            s_key = 'green_laser'
        super().__init__(posicao_inicial, grupos, jogador, game, dano, velocidade, 
                         duracao=duracao, tamanho=tamanho, sprite_key=s_key)
        self.dano_aplicado = False

    def update(self, delta_time):
        super().update(delta_time)
        # Lógica extra de dano único por colisão se necessário
        if not self.dano_aplicado and pygame.sprite.collide_mask(self, self.jogador):
            self.jogador.tomar_dano_direto(self.dano)
            self.dano_aplicado = True
    


