import pygame
import random
from os.path import join
from player import *
from settings import *
from feats.projetil import PlasmaGun, Dizimator, Carabin, M50
from feats.items import *
from entitymanager import entity_manager




class InimigoBase(pygame.sprite.Sprite):
    def __init__(self, posicao, vida_base, dano_base, velocidade_base, game):
        super().__init__(entity_manager.all_sprites, entity_manager.inimigos_grupo)

        # Nome
        self.nome_completo = "INIMIGO"
        # Reference to player
        self.jogador = entity_manager.player

        # Reference to game
        self.game = game

        #stats base
        self.vida_base = vida_base
        self.dano_base = dano_base
        self.velocidade_base = velocidade_base

        #setting true stats
        self.vida = self.vida_base
        self.dano = self.dano_base
        self.velocidade = self.velocidade_base

        #sprite
        self.image = pygame.Surface((40, 40))
        self.image.fill('white')
        self.rect = self.image.get_rect(center=posicao)
        self.posicao = pygame.math.Vector2(self.rect.center)
        self.raio_colisao_mapa = 15 # Valor pequeno para deslizar fácil
        
        #based on player level
        self.aplicar_dificuldade()

        #garantia de spawn
        self.invencivel = False
        self.tempo_criacao = pygame.time.get_ticks() # Adicionado para uso futuro, se necessário
        self.tempo_invencibilidade = 0

        
    def aplicar_dificuldade(self):
        self.vida *= 1 + self.jogador.contador_niveis / 10
        self.dano *= 1 + self.jogador.contador_niveis / 10
        self.velocidade *= 1 + self.jogador.contador_niveis / 100

    def aplicar_colisao_mapa(self, paredes_ativas, raio):
        # A mesma lógica de iteração que usamos no Player
        for _ in range(2): # Inimigos podem usar 2 iterações para poupar processamento
            for p in paredes_ativas:
                pontos = p['pontos']
                for i in range(len(pontos) - 1):
                    p1 = pontos[i]
                    p2 = pontos[i+1]
                    
                    # Chamamos a mesma função de projeção que você colocou no Player
                    # Dica: mova 'projetar_fora_da_linha' para um arquivo util.py
                    push = self.jogador.projetar_fora_da_linha(self.posicao, p1, p2, raio)
                    if push:
                        self.posicao += push


    def morrer(self, grupos = None):
        alvo_grupos = (entity_manager.all_sprites, entity_manager.item_group)
        dado = randint(0, 1000)
        if dado == 1000:
            Items(posicao=self.posicao, sheet_item=join('assets', 'img', 'cafe.png'), tipo='cafe', grupos=alvo_grupos)
        elif dado >= 990:
            Items(posicao=self.posicao, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=alvo_grupos)
        elif dado >= 970:
            Items(posicao=self.posicao, sheet_item=join('assets', 'img', 'lifeOrb.png'), tipo='life_orb', grupos=alvo_grupos)
        else:
            Items(posicao=self.posicao, sheet_item=join('assets', 'img', 'expShard.png'), tipo='exp_shard', grupos=alvo_grupos)
        self.kill()

    def update(self, delta_time, paredes = None):
        direcao = self.jogador.rect.center - self.posicao
        if direcao.length() > 0:
            direcao.normalize_ip()
        self.posicao += direcao * self.velocidade * delta_time

        if paredes:
            self.aplicar_colisao_mapa(paredes, self.raio_colisao_mapa)

        self.rect.center = self.posicao

    @property
    def collision_rect(self):
        """Retorna o retângulo de colisão para este inimigo."""
        return self.rect






            



