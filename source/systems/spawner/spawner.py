import random

from .spawner_utils import SpawnerUtils
from .spawner_pools import PHASE_POOLS, DEFAULT_POOL
from .spawner_bosses import CRONOGRAMA_BOSSES, BOSS_CLASSES, PHASE_BOSSES
from source.systems.entitymanager import entity_manager


class Spawner(SpawnerUtils):
    def __init__(self, game):
        self.game = game

        self.tempo_proximo_spawn = 0
        self.intervalo_spawn_atual = 2.5
        self.hordas_contagem = 0

        # Pools
        self.pools_por_fase = PHASE_POOLS
        self.default_pool = DEFAULT_POOL

        # Bosses
        self.boss_flags = {key: False for key in CRONOGRAMA_BOSSES.keys()}

    def spawnar(self, tipo='normal'):
        pos = self.calcular_posicao_spawn()
                
        if tipo in BOSS_CLASSES:
            # Criamos o boss e guardamos a referência no game
            novo_boss = BOSS_CLASSES[tipo](
                posicao=pos if tipo != 'gravemind' else entity_manager.player.posicao, 
                game=self.game, 
                grupos=entity_manager.all_sprites
            )
            self.game.boss_atual = novo_boss  # Envia para o Game quem é o boss
        # Inimigo comum
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

        # Inimigos Comuns (Dificuldade sempre sobe)
        if self.tempo_proximo_spawn >= self.intervalo_spawn_atual:
            self.tempo_proximo_spawn = 0
            # A dificuldade escala com o tempo acumulado de todas as fases
            qtd_spawn = 2 + fase 
            for _ in range(qtd_spawn):
                self.spawnar('normal')

        # 2. Escala de dificuldade baseada no tempo de horda acumulado
        self.intervalo_spawn_atual = max(0.5, 2.5 - (tempo_atual * 0.002))

        # 3. Bosses Relativos à Fase
        # Bosses
        if fase in PHASE_BOSSES:

            for boss in PHASE_BOSSES[fase]:

                tempo_alvo = CRONOGRAMA_BOSSES[boss]

                if (
                    tempo_atual >= tempo_alvo
                    and not self.boss_flags[boss]
                ):

                    self.boss_flags[boss] = True

                    self.spawnar(boss)