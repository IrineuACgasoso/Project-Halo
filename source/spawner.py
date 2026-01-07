import pygame
import random
from random import randint
from settings import *
from entitymanager import entity_manager
# Inimigos base
from enemies.standard.grunt import Grunt
from enemies.standard.jackal import Jackal
from enemies.standard.elite import Elite
from enemies.standard.brute import Brute
from enemies.standard.infection import Infection


# Bosses
from enemies.bosses.guilty import GuiltySpark
from enemies.bosses.arbiter import BossArbiter
from enemies.bosses.gravemind import FloodWarning
from enemies.bosses.didact import Didact
from enemies.bosses.warden import WardenEternal
from enemies.bosses.harbinger import Harbinger
from enemies.bosses.jega import Jega

# Minibosses
from enemies.minibosses.hunter import Hunter
from enemies.minibosses.knight import Knight

class Spawner:
    def __init__(self, game):
        self.game = game
        self.tempo_proximo_spawn = 0
        self.intervalo_spawn_atual = 2.5
        self.intervalo_minimo = 1.8
        self.fator_dificuldade = 0.0001
        self.hordas_contagem = 0

        # Flags de controle de Bosses
        self.cronograma_bosses = {
            'hunter': 60,        # 1 minuto
            'guilty': 180,     # 3 minutos
            'arbiter': 300,    # 5 minutos (Início Fase 2)
            'gravemind': 1,  # 8 minutos
            'didact': 600,     # 10 minutos (Início Fase 3)
            'warden': 720,     # 12 minutos
            'jega': 1080,     # 15 minutos
            'harbinger': 1200  # 20 minutos
        }

        self.boss_flags = {key: False for key in self.cronograma_bosses.keys()}

    def calcular_posicao_spawn(self):
        player = entity_manager.player
        # Define as bordas fora da visão da câmera
        camera_center_x, camera_center_y = player.posicao.x, player.posicao.y
        
        borda_esquerda = camera_center_x - largura_tela / 2
        borda_direita = camera_center_x + largura_tela / 2
        borda_topo = camera_center_y - altura_tela / 2
        borda_baixo = camera_center_y + altura_tela / 2

        lado = random.choice(['top', 'bottom', 'left', 'right'])
        if lado == 'top':
            return (random.uniform(borda_esquerda, borda_direita), borda_topo - 50)
        elif lado == 'bottom':
            return (random.uniform(borda_esquerda, borda_direita), borda_baixo + 50)
        elif lado == 'left':
            return (borda_esquerda - 50, random.uniform(borda_topo, borda_baixo))
        else:
            return (borda_direita + 50, random.uniform(borda_topo, borda_baixo))

    def spawnar(self, tipo='normal'):
        pos = self.calcular_posicao_spawn()
        
        # Mapeamento de classes para facilitar o código
        classes_bosses = {
            'hunter': Hunter, 'guilty': GuiltySpark, 'arbiter': BossArbiter,
            'gravemind': FloodWarning, 'didact': Didact, 'warden': WardenEternal,
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
            # Seleção de inimigos baseada na FASE do jogo
            fase = self.game.fase_atual
            if fase == 1:
                pool = [Grunt, Grunt, Grunt, Grunt, Grunt, Grunt, Jackal, Jackal, Jackal, Elite]
            elif fase == 2:
                pool = [Infection, Infection, Grunt, Jackal, Elite]
            elif fase == 3:
                pool = [Infection, Infection, Grunt, Grunt, Jackal, Jackal, Elite, Brute]
            else:
                pool = [Grunt, Grunt]

            inimigo_classe = random.choice(pool)
            inimigo_classe(posicao=pos, game=self.game)

    def update(self, delta_time):
        self.tempo_proximo_spawn += delta_time
        tempo_atual = self.game.timer_jogo
        player = entity_manager.player

        # Spawn de Inimigos Comuns
        if self.tempo_proximo_spawn >= self.intervalo_spawn_atual:
            self.tempo_proximo_spawn = 0
            # Aumenta a quantidade de inimigos baseada na fase
            qtd_spawn = 2 + self.game.fase_atual 
            for _ in range(qtd_spawn):
                self.spawnar('normal')


        # Spawn de Bosses por Cronômetro
        for boss, tempo_alvo in self.cronograma_bosses.items():
            if tempo_atual >= tempo_alvo and not self.boss_flags[boss]:
                self.boss_flags[boss] = True
                self.spawnar(boss)
            
            # ... continue para os outros bosses

        # Aumenta dificuldade
        self.intervalo_spawn_atual = max(0.5, 2.5 - (tempo_atual * 0.002))