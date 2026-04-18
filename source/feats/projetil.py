from source.systems.entitymanager import entity_manager
from source.enemies.enemies import *
from source.feats.items import *
from source.player.weapons import *
from source.feats.assets import *
from source.feats.assets import ASSETS
import math

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


class Aura(pygame.sprite.Sprite):
    def __init__(self, jogador, raio, dano_por_segundo, grupos):
        super().__init__(grupos)
        self.jogador = jogador
        
        # Atributos exigidos pelo seu CollisionManager (Item 5)
        self.dono = 'PLAYER'
        self.raio = raio
        self.radius = raio # Para collide_circle
        self.dano_por_segundo = dano_por_segundo
        
        # Visual: Criamos a superfície e a máscara de colisão radial
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.jogador.posicao)
        
        # O Pygame usa o atributo 'radius' para o collide_circle
        self.radius = self.raio 
        
        self.desenhar_aura()

    def desenhar_aura(self):
        """Desenha o efeito visual da aura"""
        self.image.fill((0, 0, 0, 0)) # Limpa
        # Desenha um círculo amarelo suave
        pygame.draw.circle(self.image, (255, 255, 0, 45), (self.raio, self.raio), self.raio)
        # Desenha uma borda leve para dar definição
        pygame.draw.circle(self.image, (255, 255, 0, 100), (self.raio, self.raio), self.raio, 2)

    def atualizar_stats(self, novo_raio, novo_dano):
        """Chamado pelo upgrade da Arma"""
        self.raio = novo_raio
        self.radius = self.raio # Atualiza para o motor de colisão
        self.dano_por_segundo = novo_dano
        
        # Redimensiona a imagem
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.jogador.posicao)
        self.desenhar_aura()

    def update(self, delta_time):
        # A aura apenas segue o jogador. 
        # O dano é aplicado pelo CollisionManager.update()
        self.rect.center = self.jogador.posicao


# --- CLASSES FILHAS SIMPLIFICADAS ---

class PlasmaGun(ProjetilUniversal):
    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread, vai_rotacionar):
        # Plasma é uma bola/glow, não precisa de rotação 360 (rotacionar=False)
        super().__init__(
            posicao_inicial=posicao_inicial, 
            grupos=grupos, 
            game=game, 
            dono=dono, 
            sprite_key='plasma', 
            tamanho=tamanho, 
            dano=dano, 
            velocidade=velocidade, 
            duracao=3000, 
            direcao_custom=direcao_spread, 
            rotacionar=vai_rotacionar
            )
        
class Carabin(ProjetilUniversal):
    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread, duracao=2000, is_Banished=False):
        s_key = 'bcarabin' if is_Banished else 'carabin'
        # Tiros de carabina são projéteis alongados, precisam de rotação
        super().__init__(
            posicao_inicial = posicao_inicial,
            grupos = grupos,
            game = game,
            dono=dono, 
            sprite_key = s_key,
            tamanho = tamanho,
            dano = dano,
            velocidade = velocidade,
            duracao = duracao,
            direcao_custom = direcao_spread, # Garanta que 'direcao' seja passado aqui
            rotacionar = True)
        
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
        
class Dizimator(ProjetilUniversal):
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

class LightRifle(ProjetilUniversal):
    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread):
        # Projétil de luz sólida: precisa de rotação para alinhar a "lâmina" de luz
        super().__init__(posicao_inicial=posicao_inicial, 
            grupos=grupos, 
            game=game, 
            dono=dono, 
            sprite_key='lightrifle', 
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

class ProjetilNeedler(ProjetilUniversal):
    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread, alvo):
        super().__init__(
            posicao_inicial=posicao_inicial, 
            grupos=grupos, 
            game=game, 
            dono=dono,  
            sprite_key='needler', 
            tamanho=tamanho, 
            dano=dano, 
            velocidade=velocidade, 
            duracao=3000, 
            direcao_custom=direcao_spread, 
            rotacionar=True
            )
        self.alvo_atual = alvo
        self.forca_curva = 0.18

    def update(self, delta_time):
        if self.alvo_atual and self.alvo_atual.alive():
            desejado = (self.alvo_atual.posicao - self.posicao).normalize()
            self.direcao = (self.direcao + desejado * self.forca_curva).normalize()
            if self.rotacionar:
                self.image = self.renderizar_com_rotacao()
                self.rect = self.image.get_rect(center=self.rect.center)
        super().update(delta_time)


    def ao_atingir_alvo(self, alvo):
        # 1. Checa invulnerabilidade antes de tudo
        if getattr(alvo, 'invulneravel', False):
            return # Atravessa sem contar agulha e sem morrer

        # 2. Lógica de Supercombine (Só executa se for vulnerável)
        if not hasattr(alvo, 'agulhas_presas'):
            alvo.agulhas_presas = 0
        
        alvo.agulhas_presas += 1
        alvo.receber_dano(self.dano)

        if alvo.agulhas_presas >= 7:
            # Efeito de explosão (Dano massivo)
            alvo.receber_dano(self.dano * 10) 
            alvo.agulhas_presas = 0
            # spawn_explosion_effect(alvo.posicao) # Dica para o futuro

        self.kill()
    

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


class Projetil_PingPong(ProjetilUniversal):
    def __init__(self, posicao_inicial, grupos, game, direcao, dano, velocidade, rebatidas):
        super().__init__super().__init__(
            posicao_inicial=posicao_inicial, 
            grupos=grupos, 
            game=game, 
            dono='PLAYER', 
            sprite_key='pingpong', 
            tamanho=(80,80), 
            dano=dano, 
            velocidade=velocidade, 
            direcao_custom=direcao, 
            piercing=float('inf'),
            rotacionar=False # Bola não precisa girar imagem
        ) 
        
        self.rebatidas = rebatidas
        self.inimigos_atingidos = set() # Para não dar dano múltiplo no mesmo frame

    def update(self, delta_time):
        super().update(delta_time)

        # Definimos as bordas
        margem = 10 # Pequena margem de segurança baseada no tamanho da sprite
        borda_esq = self.jogador.posicao.x - (largura_tela / 2) + margem
        borda_dir = self.jogador.posicao.x + (largura_tela / 2) - margem
        borda_topo = self.jogador.posicao.y - (altura_tela / 2) + margem
        borda_baixo = self.jogador.posicao.y + (altura_tela / 2) - margem

        # Checa colisão Eixo X
        if self.posicao.x <= borda_esq:
            self.posicao.x = borda_esq # FORÇA POSIÇÃO
            self.direcao.x *= -1
            self.rebatidas -= 1
            self.inimigos_atingidos.clear() # Limpa para dar dano de novo após rebater

        elif self.posicao.x >= borda_dir:
            self.posicao.x = borda_dir # FORÇA POSIÇÃO
            self.direcao.x *= -1
            self.rebatidas -= 1
            self.inimigos_atingidos.clear()

        # Checa colisão Eixo Y
        if self.posicao.y <= borda_topo:
            self.posicao.y = borda_topo # FORÇA POSIÇÃO
            self.direcao.y *= -1
            self.rebatidas -= 1
            self.inimigos_atingidos.clear()

        elif self.posicao.y >= borda_baixo:
            self.posicao.y = borda_baixo # FORÇA POSIÇÃO
            self.direcao.y *= -1
            self.rebatidas -= 1
            self.inimigos_atingidos.clear()

        if self.rebatidas < 0: # < 0 para garantir que a última rebatida ainda viaje
            self.kill()


