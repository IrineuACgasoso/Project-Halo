import pygame
import math
import random

from .spawner_bosses import PHASE_BOSSES


class SpawnerUtils:

    def calcular_posicao_spawn(self):
        # DEBUG: Verifique no console se os pontos existem na nova fase
        # print(f"Pontos no mapa atual: {len(self.game.mapa.pontos_de_spawn)}")

        if not self.game.mapa.pontos_de_spawn:
            # Fallback total: spawnar em volta do player caso o JSON esteja bugado
            angulo = random.uniform(0, math.pi * 2)

            direcao = pygame.math.Vector2(
                math.cos(angulo),
                math.sin(angulo)
            )

            return self.game.player.posicao + (direcao * 800)

        player_pos = self.game.player.posicao

        # A distância mínima para 500 garante que spawne fora da visão mas ache pontos
        # 500*500 = 250.000 | 2000*2000 = 4.000.000
        pontos_validos = [
            p for p in self.game.mapa.pontos_de_spawn
            if 250000 < p.distance_squared_to(player_pos) < 4000000
        ]

        if pontos_validos:
            ponto_escolhido = random.choice(pontos_validos)

            variacao = pygame.math.Vector2(
                random.uniform(-30, 30),
                random.uniform(-30, 30)
            )
            return ponto_escolhido + variacao

        else:
            # Se não achou no raio ideal, pega QUALQUER ponto que não esteja "na cara" do player
            # Pega o ponto mais distante disponível
            ponto_distante = max(
                self.game.mapa.pontos_de_spawn,
                key=lambda p: p.distance_squared_to(player_pos)
            )

            return ponto_distante

    def forcar_proximo_boss(self):
        """DEBUG: Invoca o próximo boss pendente da fase atual imediatamente."""
        fase = self.game.fase_atual

        # Verifica se existe boss configurado para essa fase
        if fase in PHASE_BOSSES:

            for boss in PHASE_BOSSES[fase]:

                # Se o boss ainda não foi invocado (flag é False)
                if not self.boss_flags[boss]:
                    # 1. Marca como invocado para o timer normal não invocar de novo
                    self.boss_flags[boss] = True
                    # 2. Chama o spawn
                    self.spawnar(boss)
                    # 3. Retorna para não invocar todos de uma vez se tiver mais de um na lista
                    return