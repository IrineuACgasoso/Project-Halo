import pygame
import random
from os.path import join
from source.player.player import *
from source.windows.settings import *
from source.feats.projetil import PlasmaGun, Dizimator, Carabin, M50
from source.feats.items import *
from source.feats.assets import ASSETS
from source.systems.entitymanager import entity_manager




class InimigoBase(pygame.sprite.Sprite):
    GLOBAL_SPRITE_CACHE = {}
    def __init__(self, posicao, vida_base, dano_base, velocidade_base, game, sprite_key, flip_sprite= False):
        super().__init__(entity_manager.all_sprites, entity_manager.inimigos_grupo)

        self.sprite_key = sprite_key
        # Gerencia o cache automaticamente para qualquer filho
        if self.sprite_key is not None:
            self._check_and_load_sprites(sprite_key, flip_sprite)

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

        # --- SISTEMA DE ESCUDO ---
        self.escudo_maximo = 0
        self.escudo_atual = 0

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

    def _check_and_load_sprites(self, key, flip_sprite):
        """Carrega e organiza o cache. Se flip_sprite for True, o arquivo de disco é 'left'."""
        if key not in InimigoBase.GLOBAL_SPRITE_CACHE:
            InimigoBase.GLOBAL_SPRITE_CACHE[key] = {}
            conteudo = ASSETS['enemies'][key]
            
            # Normaliza o conteúdo para um dicionário para facilitar o processamento
            if isinstance(conteudo, list):
                processar = {'default': conteudo}
            else:
                processar = conteudo

            for var_name, frames in processar.items():
                # Se 'frames' for apenas uma imagem solta, transforma ela em uma lista de 1 item
                if isinstance(frames, pygame.Surface):
                    frames = [frames]
                    
                frames_invertidos = [pygame.transform.flip(f, True, False) for f in frames]
                
                if flip_sprite:
                    # Se o original olha para a esquerda, o flipado olha para a direita
                    InimigoBase.GLOBAL_SPRITE_CACHE[key][var_name] = {
                        'left': frames,
                        'right': frames_invertidos
                    }
                else:
                    # Caso padrão: original olha para a direita, flipado para a esquerda
                    InimigoBase.GLOBAL_SPRITE_CACHE[key][var_name] = {
                        'right': frames,
                        'left': frames_invertidos
                    }
    
    def get_sprites(self, variante):
        """Busca as sprites no cache usando a chave do inimigo"""
        return InimigoBase.GLOBAL_SPRITE_CACHE[self.sprite_key][variante]

    def adicionar_escudo(self, valor):
        """Define o valor do escudo do inimigo."""
        self.escudo_maximo = valor
        self.escudo_atual = valor

    def receber_dano(self, quantidade):
        """Gerencia o dano, retirando do escudo primeiro e o restante da vida."""
        if self.escudo_atual > 0:
            self.escudo_atual -= quantidade
            if self.escudo_atual < 0:
                # Se o dano for maior que o escudo, o que sobra vai para a vida
                dano_restante = abs(self.escudo_atual)
                self.escudo_atual = 0
                self.vida -= dano_restante
        else:
            # Se não tem escudo, toma dano direto na vida
            self.vida -= quantidade

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
        Items.spawn_drop(self.posicao, grupos, 'exp_shard', 1, 100)
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 1, 2)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 1)
        self.kill()

    def update(self, delta_time, paredes = None):
        direcao = self.jogador.rect.center - self.posicao
        if direcao.length() > 0:
            direcao.normalize_ip()
        self.posicao += direcao * self.velocidade * delta_time

        if paredes:
            self.aplicar_colisao_mapa(paredes, self.raio_colisao_mapa)

        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

    @property
    def collision_rect(self):
        """Retorna o retângulo de colisão para este inimigo."""
        return self.rect






            



