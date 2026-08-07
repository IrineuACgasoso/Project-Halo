import pygame
import math

from source.systems.entitymanager import entity_manager
from source.feats.assets import *
from source.feats.assets import ASSETS


#PROJETIL BASE
class ProjetilUniversal(pygame.sprite.Sprite):
    GLOBAL_CACHE = {}

    def __init__(self, posicao_inicial, grupos, game, dono, sprite_key, 
                 tamanho=(20, 20), velocidade=500, dano=10, duracao=2000, 
                 direcao_custom=None, piercing=1, rotacionar=True): 
        # Definimos os grupos baseados em quem é o dono
        meus_grupos = list(grupos) # Ex: [all_sprites]
        
        if dono == 'PLAYER':
            meus_grupos.append(entity_manager.projeteis_jogador_grupo)
        elif dono == 'INIMIGO':
            meus_grupos.append(entity_manager.projeteis_inimigos_grupo)

        super().__init__(meus_grupos)
        
        self.game = game
        self.dono = dono # 'PLAYER' ou 'INIMIGO'
        self.sprite_key = sprite_key
        self.dano = dano
        self.velocidade = velocidade
        self.duracao = duracao
        self.piercing = piercing
        self.rotacionar = rotacionar # Se False, economiza RAM e CPU
        self.spawn_time = pygame.time.get_ticks()
        self.posicao = pygame.math.Vector2(posicao_inicial)
        self.direcao = direcao_custom or pygame.math.Vector2(1, 0)
        
        # Gerenciamento de Imagem
        self.tamanho = tamanho
        self.image_base = self.obter_imagem_base(sprite_key, tamanho)
        
        # Só inicializa cache de rotação se for necessário
        if self.rotacionar:
            self.chave_cache = f"{sprite_key}_{tamanho[0]}x{tamanho[1]}"
            self.image = self.renderizar_com_rotacao()
        else:
            self.image = self.image_base

        self.rect = self.image.get_rect(center=self.posicao)
        self.mask = pygame.mask.from_surface(self.image)

        # Ativa a colisão circular
        self.usar_circulo = True
        self.radius = min(self.tamanho) * 0.35

    def obter_imagem_base(self, sprite_key, tamanho):
        base_key = f"base_{sprite_key}_{tamanho[0]}x{tamanho[1]}"
        if base_key not in ProjetilUniversal.GLOBAL_CACHE:
            img = ASSETS['projectiles'].get(sprite_key)
            if img:
                # O scale acontece UMA vez aqui. Se rotacionar=False, para por aqui.
                ProjetilUniversal.GLOBAL_CACHE[base_key] = pygame.transform.scale(img, tamanho)
            else:
                surf = pygame.Surface(tamanho, pygame.SRCALPHA); surf.fill((255,0,255))
                ProjetilUniversal.GLOBAL_CACHE[base_key] = surf
        return ProjetilUniversal.GLOBAL_CACHE[base_key]

    def renderizar_com_rotacao(self):
        # Se for uma bola (rotacionar=False), este método nem é chamado no loop
        if self.chave_cache not in ProjetilUniversal.GLOBAL_CACHE:
            ProjetilUniversal.GLOBAL_CACHE[self.chave_cache] = {}

        angulo = int(round(math.degrees(math.atan2(-self.direcao.y, self.direcao.x)))) % 360
        if angulo not in ProjetilUniversal.GLOBAL_CACHE[self.chave_cache]:
            ProjetilUniversal.GLOBAL_CACHE[self.chave_cache][angulo] = \
                pygame.transform.rotate(self.image_base, angulo)
        return ProjetilUniversal.GLOBAL_CACHE[self.chave_cache][angulo]
    
    def ao_atingir_alvo(self, alvo):
        """
        Gerencia o impacto respeitando o estado do alvo.
        """
        # Checa se o alvo existe e se NÃO está invulnerável
        if alvo and not getattr(alvo, 'invulneravel', False):
            if hasattr(alvo, 'receber_dano'):
                alvo.receber_dano(self.dano)
            # Tenta o padrão que você usa no Player
            elif hasattr(alvo, 'tomar_dano'):
                alvo.tomar_dano(self)
                
            # Lógica de Piercing: só reduz se de fato atingiu algo vulnerável
            if self.piercing <= 1:
                self.kill()
            else:
                self.piercing -= 1

    def update(self, delta_time):
        self.posicao += self.direcao * self.velocidade * delta_time
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        # O CollisionManager cuida do dano. A base só se mata por tempo.
        if pygame.time.get_ticks() - self.spawn_time > self.duracao:
            self.kill()


# --- CLASSES FILHAS SIMPLIFICADAS ---

        
class M50(ProjetilUniversal):
    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread):
        super().__init__(posicao_inicial=posicao_inicial, 
            grupos=grupos, 
            game=game, 
            dono=dono, 
            sprite_key='m50', 
            tamanho=tamanho, 
            dano=dano, 
            velocidade=velocidade, 
            duracao=2500, 
            direcao_custom=direcao_spread, 
            rotacionar=False)
        
class DizimatorBullet(ProjetilUniversal):
    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread):
        # O Dizimator geralmente é uma esfera de energia pesada
        super().__init__(
            posicao_inicial=posicao_inicial, 
            grupos=grupos, 
            game=game, 
            dono=dono, 
            sprite_key='dizimator', 
            tamanho=tamanho, 
            dano=dano, 
            velocidade=velocidade, 
            duracao=1500, 
            direcao_custom=direcao_spread, 
            rotacionar=True
        )

class BurstRifle(ProjetilUniversal):
    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread):
        super().__init__(posicao_inicial=posicao_inicial, 
            grupos=grupos, 
            game=game, 
            dono=dono, 
            sprite_key='ar', 
            tamanho=tamanho, 
            dano=dano, 
            velocidade=velocidade, 
            duracao=2000, 
            direcao_custom=direcao_spread, 
            rotacionar=True
        )

class LightBullet(ProjetilUniversal):
    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread):
        # Projétil de luz sólida: precisa de rotação para alinhar a "lâmina" de luz
        super().__init__(posicao_inicial=posicao_inicial, 
            grupos=grupos, 
            game=game, 
            dono=dono, 
            sprite_key='light_bullet', 
            tamanho=tamanho, 
            dano=dano, 
            velocidade=velocidade, 
            duracao=2000, 
            direcao_custom=direcao_spread, 
            rotacionar=True
            )
        
class AcidBreath(ProjetilUniversal):
    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread):
        # Ácido é fumaça/bolhas, rotacionar isso é desperdício de RAM
        super().__init__(posicao_inicial=posicao_inicial, 
            grupos=grupos, 
            game=game, 
            dono=dono, 
            sprite_key='acid_breath', 
            tamanho=tamanho, 
            dano=dano, 
            velocidade=velocidade, 
            duracao=3000, 
            direcao_custom=direcao_spread, 
            rotacionar=False
            )
        
class LaserBeam(ProjetilUniversal):
    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread, vai_rotacionar, color='red'):
        s_key = f"{color}_laser"
        super().__init__(posicao_inicial=posicao_inicial, 
            grupos          = grupos, 
            game            = game, 
            dono            = dono, 
            sprite_key      = s_key, 
            tamanho         = tamanho, 
            dano            = dano, 
            velocidade      = velocidade, 
            duracao         = 3000, 
            direcao_custom  = direcao_spread,
            rotacionar      = vai_rotacionar
        )
    

class Projetil_Lista(ProjetilUniversal):
    def __init__(self, posicao_inicial, grupos, game, dano, angulo_inicial, duracao, velocidade_rotacao, distancia_orbita):
        super().__init__(
            posicao_inicial=posicao_inicial, 
            grupos=grupos, 
            game=game, 
            dono='PLAYER', 
            sprite_key='lista', 
            tamanho=(45, 80), 
            dano=dano, 
            velocidade=0, # Ela orbita, não tem velocidade linear
            duracao=duracao, 
            piercing=float('inf')
        )
        self.jogador = game.player
        self.angulo = angulo_inicial  # Posição angular inicial no círculo
        self.distancia_orbita = distancia_orbita
        self.velocidade_rotacao = velocidade_rotacao #graus por segundo
        self.tempo_criacao = pygame.time.get_ticks()
        self.duracao = duracao
        
    def update(self, delta_time):
        # Calcula a rotação ao redor do jogador
        self.angulo += self.velocidade_rotacao * delta_time
        deslocamento = pygame.math.Vector2(
            math.cos(math.radians(self.angulo)), 
            math.sin(math.radians(self.angulo))
        ) * self.distancia_orbita

        self.posicao = self.jogador.posicao + deslocamento
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        if pygame.time.get_ticks() - self.tempo_criacao > self.duracao:
            self.kill()


