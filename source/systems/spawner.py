import pygame
import random
import math
from random import randint
from source.windows.settings import *
from source.systems.entitymanager import entity_manager
from source.systems.mapmanager import Mapa
from source.feats.assets import *

# Inimigos base
from source.enemies.standard.grunt import Grunt
from source.enemies.standard.jackal import Jackal
from source.enemies.standard.elite import Elite
from source.enemies.standard.brute import Brute
from source.enemies.standard.infection import Infection, FloodForms
from source.enemies.standard.sentinel import Sentinel
from source.enemies.standard.crawler import Crawler
from source.enemies.standard.watcher import Watcher
from source.enemies.standard.soldier import Soldier


# Bosses
from source.enemies.bosses.guilty import GuiltySpark
from source.enemies.bosses.arbiter import BossArbiter
from source.enemies.bosses.gravemind import FloodWarning
from source.enemies.bosses.didact import Didact
from source.enemies.bosses.warden import WardenEternal
from source.enemies.bosses.harbinger import Harbinger
from source.enemies.bosses.jega import Jega

# Minibosses
from source.enemies.minibosses.hunter import Hunter
from source.enemies.minibosses.zealot import Zealot
from source.enemies.minibosses.scarab import Scarab
from source.enemies.minibosses.knight import Knight

class Spawner:
    def __init__(self, game):
        self.game = game
        self.tempo_proximo_spawn = 0
        self.intervalo_spawn_atual = 2.5
        self.intervalo_minimo = 1.8
        self.fator_dificuldade = 0.0001
        self.hordas_contagem = 0

        # OTIMIZAÇÃO COM PESOS: { fase: { "classes": [], "pesos": [] } }
        self.pools_por_fase = {
            0: {
                "classes": [Grunt, Jackal, Elite],
                "pesos": [60, 30, 10]  # 60% Grunt, 30% Jackal, 10% Elite
            },
            1: {
                "classes": [Infection, Grunt, Jackal, Elite],
                "pesos": [40, 30, 20, 10] # Muita Infection, pouco Elite
            },
            2: {
                "classes": [Infection, FloodForms, Grunt, Jackal, Elite, Sentinel],
                "pesos": [20, 20, 20, 20, 10, 10]
            },
            3: {
                "classes": [Grunt, Jackal, Elite, Brute],
                "pesos": [40, 20, 20, 20]
            },
            4: {
                "classes": [Infection, FloodForms, Grunt, Jackal, Elite, Brute],
                "pesos": [20, 25, 20, 15, 10, 10]
            }
            # Adicione as outras fases seguindo o padrão
        }
        
        # Fallback caso a fase não exista no dicionário
        self.default_pool = {"classes": [Grunt], "pesos": [100]}

        # Flags de controle de Bosses
        self.cronograma_bosses = {
            'hunter': 60,        # 1 minuto
            'zealot': 120,       #
            'guilty': 180,     # 2 minutos
            'scarab': 240,      # 4 minutos
            'arbiter': 300,    # 5 minutos (Início Fase 2)
            'gravemind': 500,  # 8 minutos
            'knight' : 600,    # 10 minutos
            'didact': 700,     # 12 minutos (Início Fase 3)
            'warden': 840,     # 14 minutos
            'jega': 1080,     # 15 minutos
            'harbinger': 1200  # 20 minutos
        }

        self.boss_flags = {key: False for key in self.cronograma_bosses.keys()}

    def calcular_posicao_spawn(self):
        # DEBUG: Verifique no console se os pontos existem na nova fase
        # print(f"Pontos no mapa atual: {len(self.game.mapa.pontos_de_spawn)}")

        if not self.game.mapa.pontos_de_spawn:
            # Fallback total: spawnar em volta do player caso o JSON esteja bugado
            ângulo = random.uniform(0, math.pi * 2)
            direcao = pygame.math.Vector2(math.cos(ângulo), math.sin(ângulo))
            return self.game.player.posicao + (direcao * 800)

        player_pos = self.game.player.posicao
        
        # Reduzi a distância mínima para 500 (garante que spawne fora da visão mas ache pontos)
        # 500*500 = 250.000 | 2000*2000 = 4.000.000
        pontos_validos = [
            p for p in self.game.mapa.pontos_de_spawn 
            if 250000 < p.distance_squared_to(player_pos) < 4000000
        ]

        if pontos_validos:
            ponto_escolhido = random.choice(pontos_validos)
            variacao = pygame.math.Vector2(random.uniform(-30, 30), random.uniform(-30, 30))
            return ponto_escolhido + variacao
        else:
            # Se não achou no raio ideal, pega QUALQUER ponto que não esteja "na cara" do player
            # Pega o ponto mais distante disponível
            ponto_distante = max(self.game.mapa.pontos_de_spawn, key=lambda p: p.distance_squared_to(player_pos))
            return ponto_distante
        
    def forcar_proximo_boss(self):
        """DEBUG: Invoca o próximo boss pendente da fase atual imediatamente."""
        
        bosses_por_fase = {
            0: ['hunter'],
            1: ['zealot'],
            2: ['guilty'], 
            3: ['scarab'],           
            4: ['arbiter'],
            5: ['gravemind'],
            6: ['knight'],
            7: ['didact'],
            8: ['jega'],
        }

        fase = self.game.fase_atual

        # Verifica se existe boss configurado para essa fase
        if fase in bosses_por_fase:
            for boss in bosses_por_fase[fase]:
                # Se o boss ainda não foi invocado (flag é False)
                if not self.boss_flags[boss]:
                    
                    # 1. Marca como invocado para o timer normal não invocar de novo
                    self.boss_flags[boss] = True 
                    
                    # 2. Chama o spawn
                    self.spawnar(boss)
                    
                    # 3. Retorna para não invocar todos de uma vez se tiver mais de um na lista
                    return 
            
    def spawnar(self, tipo='normal'):
        pos = self.calcular_posicao_spawn()
        
        # Mapeamento de classes para facilitar o código
        classes_bosses = {
            'hunter': Hunter, 'zealot': Zealot, 'guilty': GuiltySpark, 'scarab': Scarab, 'arbiter': BossArbiter,
            'gravemind': FloodWarning, 'knight' : Knight, 'didact': Didact, 'warden': WardenEternal,
            'harbinger': Harbinger, 'jega': Jega
        }
        if tipo in classes_bosses:
            # Criamos o boss e guardamos a referência no game
            novo_boss = classes_bosses[tipo](
                posicao=pos if tipo != 'gravemind' else entity_manager.player.posicao, 
                game=self.game, 
                grupos=entity_manager.all_sprites
            )
            self.game.boss_atual = novo_boss  # Envia para o Game quem é o boss
        else:
            # Pega os dados da fase atual ou o default
            dados_fase = self.pools_por_fase.get(self.game.fase_atual, self.default_pool)
            
            # OTIMIZAÇÃO: random.choices escolhe baseado nos pesos
            inimigo_classe = random.choices(
                population=dados_fase["classes"],
                weights=dados_fase["pesos"],
                k=1 # Queremos apenas 1 inimigo
            )[0]
            
            inimigo_classe(posicao=pos, game=self.game)

    def update(self, delta_time):
        self.tempo_proximo_spawn += delta_time
        tempo_atual = self.game.timer_jogo
        fase = self.game.fase_atual

        # 1. Inimigos Comuns (Dificuldade sempre sobe)
        if self.tempo_proximo_spawn >= self.intervalo_spawn_atual:
            self.tempo_proximo_spawn = 0
            # A dificuldade escala com o tempo acumulado de todas as fases
            qtd_spawn = 2 + fase 
            for _ in range(qtd_spawn):
                self.spawnar('normal')

        # 2. Escala de dificuldade baseada no tempo de horda acumulado
        self.intervalo_spawn_atual = max(0.5, 2.5 - (tempo_atual * 0.002))

        # 3. Bosses Relativos à Fase
        # Se o timer parou no boss anterior, ele volta a correr agora.
        bosses_por_fase = {
            0: ['hunter'],
            1: ['zealot'],
            2: ['guilty'],
            3: ['scarab'],            
            4: ['arbiter'],
            5: ['gravemind'],
            6: ['knight'],
            7: ['didact'],
            8: ['jega'],
        }

        if fase in bosses_por_fase:
            for boss in bosses_por_fase[fase]:
                tempo_alvo = self.cronograma_bosses[boss]
                
                # Se o player já passou do tempo desse boss (porque o timer é contínuo)
                # OU se o tempo acabou de chegar, ele spawna.
                if tempo_atual >= tempo_alvo and not self.boss_flags[boss]:
                    self.boss_flags[boss] = True
                    self.spawnar(boss)