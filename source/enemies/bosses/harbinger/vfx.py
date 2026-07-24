# source/enemies/bosses/harbinger/vfx.py
import pygame
from source.feats.assets import ASSETS
from source.systems.entitymanager import entity_manager
from source.feats.projetil import ProjetilUniversal


class HarbingerTeleport(pygame.sprite.Sprite):
    """Efeito visual de portais/fendas temporais consumindo o gerenciador global ASSETS."""
    def __init__(self, posicao, ordem=1):
        super().__init__(entity_manager.all_sprites)
        self.posicao = pygame.math.Vector2(posicao) 
        self.ordem = ordem
        
        self.sprites = ASSETS['enemies']['harbinger']['teleport']

        if self.ordem == 1:
            self.frame_atual = 0
        else:
            self.frame_atual = len(self.sprites) - 1

        self.image = self.sprites[self.frame_atual]
        self.rect = self.image.get_rect(center=self.posicao)
        
        self.tempo_criacao = pygame.time.get_ticks()
        self.ultimo_update_animacao = pygame.time.get_ticks()
        self.velocidade_animacao = 35  
        self.duracao_aviso = 330
    
    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        if agora - self.tempo_criacao >= self.duracao_aviso:
            self.kill()
            return
        self.animar()

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + self.ordem) % len(self.sprites)
            self.image = self.sprites[self.frame_atual]
            self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))


class EnergyBlastShot(ProjetilUniversal):
    """'Carabin Maior' — herda toda a infraestrutura de ProjetilUniversal
    (cache global de imagem, colisão circular via CollisionManager, grupos
    corretos) igual aos outros projéteis do jogo. A única diferença de
    comportamento: em vez de morrer ao tocar o jogador ou por tempo, ela
    viaja em linha reta até a posição travada do alvo no instante do
    disparo e, ao chegar lá, se desfaz numa Artilharia de Aviso azul.

    O visual (glow azul) é gerado apenas UMA VEZ e fica no GLOBAL_CACHE,
    exatamente como as sprites dos demais projéteis — não recria Surface
    a cada instância.
    """

    def __init__(self, posicao_inicial, alvo, game, jogador=None,
                 dono='INIMIGO', tamanho=(46, 46), dano=140,
                 velocidade=750, duracao=4000):
        posicao_inicial = pygame.math.Vector2(posicao_inicial)
        alvo = pygame.math.Vector2(alvo)

        vetor_ate_alvo = alvo - posicao_inicial
        self.distancia_total = vetor_ate_alvo.length()
        direcao = (
            vetor_ate_alvo.normalize()
            if vetor_ate_alvo.length_squared() > 0
            else pygame.math.Vector2(1, 0)
        )

        super().__init__(
            posicao_inicial=posicao_inicial,
            grupos=(entity_manager.all_sprites,),
            game=game,
            dono=dono,
            sprite_key='energy_blast',
            tamanho=tamanho,
            dano=dano,
            velocidade=velocidade,
            duracao=duracao,
            direcao_custom=direcao,
            piercing=1,
            rotacionar=False,  # é um glow redondo, não precisa girar
        )

        self.percorrido = 0

    def obter_imagem_base(self, sprite_key, tamanho):
        """Desenha o glow azul em várias camadas concêntricas (uma única vez,
        cacheado no GLOBAL_CACHE compartilhado)."""
        base_key = f"base_{sprite_key}_{tamanho[0]}x{tamanho[1]}"
        if base_key not in ProjetilUniversal.GLOBAL_CACHE:
            surf = pygame.Surface(tamanho, pygame.SRCALPHA)
            centro = (tamanho[0] // 2, tamanho[1] // 2)
            raio_max = tamanho[0] // 2

            camadas = [
                (1.00, (40, 110, 255), 60),
                (0.85, (55, 130, 255), 90),
                (0.70, (70, 155, 255), 130),
                (0.55, (95, 180, 255), 170),
                (0.40, (140, 205, 255), 205),
                (0.25, (190, 225, 255), 235),
                (0.12, (255, 255, 255), 255),
            ]

            for fracao, cor, alpha in camadas:
                raio = max(1, int(raio_max * fracao))
                pygame.draw.circle(surf, (*cor, alpha), centro, raio)

            ProjetilUniversal.GLOBAL_CACHE[base_key] = surf
        return ProjetilUniversal.GLOBAL_CACHE[base_key]

    def ao_atingir_alvo(self, alvo):
        """O dano não vem de colisão direta — só da explosão da ArtilhariaAviso
        ao chegar no ponto travado. Atravessa o jogador sem efeito aqui."""
        return False

    def update(self, delta_time):
        deslocamento = self.velocidade * delta_time
        self.posicao += self.direcao * deslocamento
        self.percorrido += deslocamento
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        if self.percorrido >= self.distancia_total:
            self.explodir()
        elif pygame.time.get_ticks() - self.spawn_time > self.duracao:
            self.kill()

    def explodir(self):
        from source.feats.skills.artilharia.core import ArtilhariaAviso
        ArtilhariaAviso(
            posicao=self.posicao.copy(),
            grupos=(entity_manager.all_sprites,),
            game=self.game,
            dono='INIMIGO',
            preset='harbinger_energy_blast',
        )
        self.kill()


class TeleportBurstShot(ProjetilUniversal):
    """Disparo de impacto do TELEPORTE OFENSIVO ("Teleporte de Recomposição").

    Projétil dedicado, comportamento padrão de colisão (herdado de
    ProjetilUniversal). Paleta predominantemente azul — o branco só
    aparece bem no centro, num núcleo pequeno, para não competir
    visualmente com a personagem em tamanhos grandes.
    """

    def __init__(self, posicao_inicial, grupos, jogador, game, dono,
                 tamanho=(110, 110), dano=110, velocidade=850,
                 direcao_spread=None, duracao=2500):
        super().__init__(
            posicao_inicial=posicao_inicial,
            grupos=grupos,
            game=game,
            dono=dono,
            sprite_key='teleport_burst',
            tamanho=tamanho,
            dano=dano,
            velocidade=velocidade,
            duracao=duracao,
            direcao_custom=direcao_spread,
            rotacionar=False,
        )

    def obter_imagem_base(self, sprite_key, tamanho):
        """Desenha o glow em várias camadas concêntricas, predominantemente
        azuis, com um núcleo branco pequeno e tardio (cacheado uma única
        vez no GLOBAL_CACHE compartilhado)."""
        base_key = f"base_{sprite_key}_{tamanho[0]}x{tamanho[1]}"
        if base_key not in ProjetilUniversal.GLOBAL_CACHE:
            surf = pygame.Surface(tamanho, pygame.SRCALPHA)
            centro = (tamanho[0] // 2, tamanho[1] // 2)
            raio_max = tamanho[0] // 2

            # (fração_do_raio, cor_rgb, alpha) — azul dominando a maior
            # parte do raio; o branco só chega numa fração bem pequena (0.06)
            camadas = [
                (1.00, (20, 70, 200), 70),
                (0.85, (30, 90, 220), 110),
                (0.68, (45, 110, 240), 150),
                (0.50, (70, 140, 250), 195),
                (0.32, (110, 170, 255), 225),
                (0.16, (170, 205, 255), 245),
                (0.06, (255, 255, 255), 255),  # núcleo branco pequeno e tardio
            ]

            for fracao, cor, alpha in camadas:
                raio = max(1, int(raio_max * fracao))
                pygame.draw.circle(surf, (*cor, alpha), centro, raio)

            ProjetilUniversal.GLOBAL_CACHE[base_key] = surf
        return ProjetilUniversal.GLOBAL_CACHE[base_key]