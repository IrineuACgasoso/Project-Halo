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

        # Flags de controle de Bosses (Movidos do Game para cá)
        self.boss_flags = {
            'hunter': False,
            'guilty': False,
            'arbiter': False,
            'gravemind': False,
            'didact': False,
            'warden': False,
            'harbinger': False
        }

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
        
        # Lógica de Bosses/Minibosses
        if tipo == 'hunter': Hunter(posicao=pos, game=self.game)
        elif tipo == 'knight': Knight(posicao=pos, game=self.game)
        elif tipo == 'guilty': GuiltySpark(posicao=pos, game=self.game)
        elif tipo == 'arbiter': BossArbiter(posicao=pos, game=self.game)
        elif tipo == 'gravemind': FloodWarning(posicao=entity_manager.player.posicao, game=self.game)
        elif tipo == 'didact': Didact(posicao=pos, game=self.game)
        elif tipo == 'warden': WardenEternal(posicao=pos, game=self.game)
        elif tipo == 'harbinger': Harbinger(posicao=pos, game=self.game)
        
        # Lógica de Inimigos Normais
        else:
            niveis = entity_manager.player.contador_niveis
            if niveis <= 10:
                pool = [Infection, Infection, Grunt, Grunt, Jackal, Elite]
            elif 10 < niveis <= 20:
                pool = [Grunt, Infection, Infection, Jackal, Elite, Brute]
            else:
                pool = [Infection, Grunt, Jackal, Brute, Brute, Elite]

            # Seleção por peso (simplificada)
            chance = randint(1, 1000)
            if chance < 225: inimigo_classe = pool[0]
            elif chance < 450: inimigo_classe = pool[1]
            elif chance < 675: inimigo_classe = pool[2]
            elif chance < 900: inimigo_classe = pool[3]
            elif chance < 950: inimigo_classe = pool[4]
            else: inimigo_classe = pool[5]
            
            inimigo_classe(posicao=pos, game=self.game)

    def update(self, delta_time):
        self.tempo_proximo_spawn += delta_time
        player = entity_manager.player

        if self.tempo_proximo_spawn >= self.intervalo_spawn_atual:
            self.tempo_proximo_spawn = 0
            self.hordas_contagem += 1
            
            # Spawn padrão (2 inimigos por ciclo)
            for _ in range(2):
                self.spawnar()

            # Gatilhos de Progressão (Bosses)
            lvl = player.contador_niveis
            if lvl >= 1 and not self.boss_flags['harbinger']:
                self.boss_flags['harbinger'] = True
                self.spawnar('harbinger')

            if lvl >= 20 and not self.boss_flags['arbiter']:
                self.boss_flags['arbiter'] = True
                self.spawnar('arbiter')
            
            if lvl >= 30 and not self.boss_flags['gravemind']:
                self.boss_flags['gravemind'] = True
                self.spawnar('gravemind')

            if lvl >= 40 and not self.boss_flags['didact']:
                self.boss_flags['didact'] = True
                self.spawnar('didact')

            if lvl >= 50 and not self.boss_flags['hunter']:
                self.boss_flags['hunter'] = True
                self.spawnar('hunter')
            
            # ... continue para os outros bosses

        # Aumenta dificuldade
        if self.intervalo_spawn_atual > self.intervalo_minimo:
            self.intervalo_spawn_atual -= self.fator_dificuldade * delta_time