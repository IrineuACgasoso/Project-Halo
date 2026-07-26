import math
import random

import pygame

from source.feats.projetil import Carabin, Spike
from source.systems.entitymanager import entity_manager

from .vfx import JegaClone


class JegaAttacks:
    # ------------------------------------------------------------------
    # Órbita Invisível (dinâmica)
    # ------------------------------------------------------------------
    def iniciar_orbita(self, distancia_atual):
        """Ativa a órbita usando a distância REAL até o jogador como raio,
        evitando qualquer teleporte para encaixar em um raio fixo."""
        self.estado = 'orbitando'
        self.tempo_inicio_estado = pygame.time.get_ticks()

        self.sentido_orbita = random.choice([1, -1])
        self.raio_orbita = distancia_atual
        self.angulo_orbita = math.atan2(self.posicao.y - self.jogador.posicao.y,
                                        self.posicao.x - self.jogador.posicao.x)

        # Ativa a invisibilidade oficial da classe base durante a órbita inteira
        self.iniciar_invisibilidade(
            alpha_alvo=0,
            fade_out=400,
            fade_in=400,
            duracao=self.duracao_orbita,
            flashing=False
        )

    # ------------------------------------------------------------------
    # Carabina
    # ------------------------------------------------------------------
    def carabin(self):
        direcao_tiro = self.calcular_direcao_tiro(0.05)

        self.trigger_flash(duracao=35, bonus_alpha=60)
        Carabin(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites,),
            jogador=self.jogador,
            game=self.game,
            dono='INIMIGO',
            tamanho=(24, 24),
            dano=40,
            velocidade=650,
            direcao_spread=direcao_tiro,
            is_Banished=True
        )

    def processar_carabina(self, agora, delta_time):
        """Controla o disparo do burst de carabina, respeitando o cooldown randomizado."""
        if agora - self.ultima_carabina >= self.cooldown_carabin and self.estado == 'perseguindo':
            self.carabina_restante = self.contagem_carabina
            self.cooldown_carabin = self.novo_cooldown(6000, 11000)
            self.ultima_carabina = agora

        if self.carabina_restante > 0:
            self.cronometro_carabina += delta_time * 1000
            if self.cronometro_carabina >= self.intervalo_carabina:
                self.cronometro_carabina = 0
                self.carabina_restante -= 1
                self.carabin()

                # Só trava o "wait" UMA VEZ, no exato frame em que o burst termina
                if self.carabina_restante == 0:
                    self.wait = agora + 1500

    # ------------------------------------------------------------------
    # Spike (leque triplo, grudento, parabólico)
    # ------------------------------------------------------------------
    def lancar_spike(self, agora):
        """Lança 3 Spikes em leque: o do meio mira direto no jogador, os outros
        dois saem com +-30° de desvio em torno do mesmo vetor/distância."""
        vetor_base = self.jogador.posicao - self.posicao
        distancia = vetor_base.length()

        if distancia == 0:
            vetor_base = pygame.math.Vector2(1, 0)
            distancia = 1

        # -30° (esquerda), 0° (centro, direto no jogador), +30° (direita)
        for angulo_offset in (-30, 0, 30):
            direcao = vetor_base.rotate(angulo_offset)
            if direcao.length_squared() > 0:
                direcao = direcao.normalize()

            posicao_alvo = self.posicao + direcao * distancia

            Spike(
                posicao_inicial=self.posicao,
                posicao_alvo=posicao_alvo,
                grupos=(entity_manager.all_sprites,),
                jogador=self.jogador,
                game=self.game,
                dono='INIMIGO',
                preset='jega_spike'
            )

        self.wait = agora + 1000

    def processar_spike(self, agora, delta_time):
        """Dispara o leque de Spikes periodicamente, exceto durante a órbita invisível."""
        if agora - self.ultimo_spike >= self.cooldown_spike and self.estado == 'perseguindo':
            self.lancar_spike(agora)
            self.ultimo_spike = agora
            self.cooldown_spike = self.novo_cooldown(7500, 12000)

    # Ilusões Sombrias (clones + backstab)
    def _invocar_clones(self, direcao_base):
        """Invoca 2 ou 3 JegaClone em leque, correndo em linha reta na
        direção geral do jogador (com pequenas variações de ângulo pra não
        saírem todos idênticos)."""
        quantidade = random.choice([2, 3])
        espalhamento = 18  # graus entre cada clone
        inicio = -(espalhamento * (quantidade - 1)) / 2

        for i in range(quantidade):
            angulo = inicio + i * espalhamento
            direcao_clone = direcao_base.rotate(angulo)

            clone = JegaClone(
                posicao=self.posicao,
                game=self.game,
                jogador=self.jogador,
                direcao=direcao_clone
            )
            entity_manager.all_sprites.add(clone)
            entity_manager.inimigos_grupo.add(clone)

    def iniciar_ilusao(self, agora):
        """Entra em modo furtivo, invoca os clones distraindo o jogador, e
        trava um ponto às costas dele pra onde o Jega real vai se
        reposicionar em silêncio, enquanto invisível."""
        self.estado = 'ilusao'
        self.tempo_inicio_estado = agora

        vetor_para_jogador = self.jogador.posicao - self.posicao
        if vetor_para_jogador.length_squared() > 0:
            direcao_base = vetor_para_jogador.normalize()
        else:
            direcao_base = pygame.math.Vector2(1, 0)

        # Ponto travado do outro lado do jogador (o "backstab")
        self.ponto_reposicionamento = pygame.math.Vector2(self.jogador.posicao) \
            + direcao_base * self.distancia_backstab

        self._invocar_clones(direcao_base)

        self.iniciar_invisibilidade(
            alpha_alvo=0,
            fade_out=350,
            fade_in=350,
            duracao=self.duracao_ilusao,
            flashing=False
        )

    def processar_ilusao(self, agora, delta_time):
        """Dispara a Ilusão Sombria periodicamente, só durante a perseguição."""
        if agora - self.ultima_ilusao >= self.cooldown_ilusao and self.estado == 'perseguindo':
            self.iniciar_ilusao(agora)
            self.ultima_ilusao = agora
            self.cooldown_ilusao = self.novo_cooldown(12000, 18000)