import math
import pygame


class JegaAI:
    def executar_estados(self, agora, delta_time, direcao_ao_jogador, distancia_sq):
        """Controla a movimentação e transições da máquina de estados do Jega.

        `distancia_sq` é sempre a distância ao QUADRADO até o jogador
        (evita sqrt desnecessário nas comparações de gatilho)."""

        # TRAVA GLOBAL (igual ao GuiltyAI): enquanto o wait não expirar, o Jega
        # não decide nem executa nenhuma lógica própria - nem a máquina de
        # estados, nem a invisibilidade. Só o básico do update() da BaseEnemy
        # (paredes, rects, animação) continua rodando normalmente.
        if agora < self.wait:
            return

        # Atualiza a máquina de invisibilidade da classe base (fade controlado por fases)
        if getattr(self, 'invis_phase', None) is not None:
            self.atualizar_invisibilidade(delta_time * 1000)

        if self.estado == 'perseguindo':
            if distancia_sq > 0:
                self.posicao += direcao_ao_jogador.normalize() * self.velocidade * delta_time

            # Condição de transição: Perseguindo -> Orbitando
            # Só entra em órbita se a distância atual estiver dentro da faixa permitida
            # E não houver burst de carabina em andamento (deixa ele terminar antes).
            dentro_da_faixa = self.orbita_distancia_min_sq <= distancia_sq <= self.orbita_distancia_max_sq
            if (agora - self.ultima_habilidade > self.cooldown_habilidade
                    and dentro_da_faixa
                    and self.carabina_restante == 0):
                distancia_atual = math.sqrt(distancia_sq)  # único sqrt, só ao ativar a órbita
                self.iniciar_orbita(distancia_atual)

        elif self.estado == 'orbitando':
            # Movimento Circular usando o raio dinâmico definido em iniciar_orbita
            self.angulo_orbita += self.sentido_orbita * self.velocidade_orbita * delta_time
            nova_x = self.jogador.posicao.x + math.cos(self.angulo_orbita) * self.raio_orbita
            nova_y = self.jogador.posicao.y + math.sin(self.angulo_orbita) * self.raio_orbita
            self.posicao = pygame.math.Vector2(nova_x, nova_y)

            # Condição de transição: Orbitando -> Bote
            if agora - self.tempo_inicio_estado > self.duracao_orbita:
                self.estado = 'bote'
                self.tempo_inicio_estado = agora

                # TRAVANDO A MIRA: Calcula a direção do jogador neste exato milissegundo
                vetor_mira = self.jogador.posicao - self.posicao
                if vetor_mira.length_squared() > 0:
                    self.direcao_bote = vetor_mira.normalize()
                else:
                    self.direcao_bote = pygame.math.Vector2(1, 0)  # Fallback de segurança

        elif self.estado == 'ilusao':
            # Movimento silencioso (invisível) até o ponto travado nas costas do jogador
            vetor_reposicionamento = self.ponto_reposicionamento - self.posicao
            if vetor_reposicionamento.length_squared() > 4:
                direcao = vetor_reposicionamento.normalize()
                self.posicao += direcao * self.velocidade_ilusao * delta_time

            # Condição de transição: Ilusão -> Bote (o golpe real, de surpresa)
            if agora - self.tempo_inicio_estado > self.duracao_ilusao:
                self.estado = 'bote'
                self.tempo_inicio_estado = agora

                vetor_mira = self.jogador.posicao - self.posicao
                if vetor_mira.length_squared() > 0:
                    self.direcao_bote = vetor_mira.normalize()
                else:
                    self.direcao_bote = pygame.math.Vector2(1, 0)

        elif self.estado == 'bote':
            self.velocidade_animacao = 100  # Animação acelerada no bote

            # Corrida do bote em LINHA RETA (usando a mira travada, ignora o jogador)
            self.posicao += self.direcao_bote * self.velocidade_bote * delta_time

            # Condição de transição: Bote -> Perseguindo
            if agora - self.tempo_inicio_estado > self.duracao_bote:
                self.velocidade_animacao = 180
                self.estado = 'perseguindo'
                self.ultima_habilidade = agora
                self.cooldown_habilidade = self.novo_cooldown(8000, 13000)
                self.wait = agora + 2000