import pygame
import random
from enemies.enemies import *
from game import *
from player import *
from feats.items import *


class BossArbiter(InimigoBase):
    def __init__(self, posicao, game):
        valor_vida = 4500
        super().__init__(posicao, vida_base=valor_vida, dano_base=80, velocidade_base = 90, game=game)
        self.titulo = "THEL 'VADAM, O Comandante da Frota Covenant"
        
        self.game=game
        self.vida = valor_vida      # Vida atual (vai diminuir)
        self.vida_base = valor_vida
        self.velocidade = self.velocidade_base
        #sprites
        self.sprites = {}
        self.sprites['left'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'arbiter', 'abiboss.png')).convert_alpha(), (200,200)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'arbiter', 'abiboss2.png')).convert_alpha(), (200,200))
            ]
        self.sprites['right'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites['left']
        ]
        #framagem da sprite
        self.frame_atual = 0  
        self.estado_animacao = 'right'
        self.indice_animacao = 0
        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center=self.posicao)
        self.velocidade_animacao = 300
        self.ultimo_update_animacao = pygame.time.get_ticks()

        #hitbox
        nova_largura = self.rect.width / 2
        self.hitbox = pygame.Rect(0, 0, nova_largura, self.rect.height)
        self.hitbox.center = self.rect.center

        #invisibilidade 
        self.cooldown_invisibilidade = 8000
        self.duracao_invisi = 5000
        self.invisivel = False
        self.ultima_invisibi = pygame.time.get_ticks()
        self.duracao_falha = 30
        self.tempo_desde_falha = 0

        #burst carabin
        self.cooldown_carabin = 3000
        self.intervalo_carabina = 75
        self.cronometro_carabina = 0
        self.ultima_carabina = 0
        self.carabina_restante = 0
        self.contagem_carabina = 5

    @property
    def collision_rect(self):
        "Retorna a hitbox de Arbiter."
        return self.hitbox
    
    def carabin(self):
        Carabin(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites, entity_manager.projeteis_inimigos_grupo),
            jogador=self.jogador,
            game=self.game,
            dano=40,
            velocidade=600,
            tamanho=(16, 16)
        )

    def animar(self):
        agora = pygame.time.get_ticks()
        if self.invisivel:
            return 
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.posicao)

    def morrer(self, grupos):
        alvo_grupos = (entity_manager.all_sprites, entity_manager.item_group)
        chance= randint(1,1000)

        # Drop garantido de Shards grandes por ser Boss
        qtd_shards = 2
        if chance > 800: qtd_shards = 4
        elif chance > 600: qtd_shards = 3

        for _ in range(qtd_shards):
            pos_offset = self.posicao + pygame.math.Vector2(random.randint(-30, 30), random.randint(-30, 30))
            Items(posicao=pos_offset, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=alvo_grupos)
        self.kill()

    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        direcao = (self.jogador.posicao - self.posicao)
        if direcao.length() > 0:
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * delta_time
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))
            self.hitbox.center = self.rect.center

        if not self.invisivel:
            if agora - self.ultima_invisibi >= self.cooldown_invisibilidade:
                novo_cooldown = [8000, 10000, 11000, 12000]
                self.cooldown_invisibilidade = random.choice(novo_cooldown)
                self.invisivel = True
                self.ultima_invisibi = agora
                self.velocidade *= 4
                self.image.set_alpha(0)
        else:
            # Lógica para quando o boss está invisível
            if agora - self.ultima_invisibi >= self.duracao_invisi:
                # Desativa a invisibilidade e volta ao normal
                self.invisivel = False
                self.velocidade = self.velocidade_base
                self.image.set_alpha(255) # Torna a sprite completamente visível novamente
            else:
                #Falha na invisibilidade
                if self.hitbox.colliderect(self.jogador.hitbox):
                    self.tempo_desde_falha = pygame.time.get_ticks()
                    self.image.set_alpha(100)
                if agora - self.tempo_desde_falha >= self.duracao_falha:
                    self.image.set_alpha(0)
        #Ativa carabina
        if agora - self.ultima_carabina >= self.cooldown_carabin:
            self.carabina_restante = self.contagem_carabina
            novo_cooldown_carabina = [4000, 5000, 6000, 7000]
            self.cooldown_carabin = random.choice(novo_cooldown_carabina)
            self.ultima_carabina = agora
        #Atira carabina
        if self.carabina_restante > 0:
            self.cronometro_carabina += delta_time * 1000
            if self.cronometro_carabina >= self.intervalo_carabina:
                self.cronometro_carabina = 0
                self.carabina_restante -= 1
                self.carabin()
        if direcao.x < 0:
                self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'
        self.animar()
            
