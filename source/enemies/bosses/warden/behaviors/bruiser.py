import math
import pygame


class BruiserBehavior:
    """
    IA do Combatente — três modos de operação:

    1. MAIS PRÓXIMO (sem escudo)
       Persegue o player em linha reta na velocidade base.

    2. NÃO É O MAIS PRÓXIMO (sem escudo)
       Tenta se interpor entre o player e o Warden mais próximo,
       posicionando-se na linha que liga os dois.

    3. ESCUDO ATIVO (invulnerável)
       Velocidade reduzida a 60% em ambos os modos.
       Bônus anti-flanque: se detectar que o player está circundando
       (variação de ângulo > limiar), acompanha o arco em órbita,
       mantendo-se entre o player e os aliados mais frágeis.
    """

    # ------------------------------------------------------------------
    # Inicialização do estado interno — chame em inicializar_habilidades
    # ------------------------------------------------------------------
    def _inicializar_combatente(self):
        self._angulo_anterior_player = None   # ângulo do vetor self→player no frame anterior
        self._arco_acumulado = 0.0            # variação angular acumulada (rad)
        self._modo_arco_ativo = False         # True quando está acompanhando flanque

    # ------------------------------------------------------------------
    # Entry point chamado pelo roteador em functions.py
    # ------------------------------------------------------------------
    def _comportamento_combatente(self, delta_time):
        agora = pygame.time.get_ticks()

        # Desliga o pursuit nativo do BaseEnemy — movimento é 100% manual aqui
        self.velocidade = 0

        escudo_ativo = getattr(self, 'is_invulneravel', False)
        fator_velocidade = 0.6 if escudo_ativo else 1.0
        velocidade_base = self.velocidade_base * fator_velocidade

        if escudo_ativo:
            self._atualizar_deteccao_arco()

        if self.sou_o_mais_proximo():
            self._modo_mais_proximo(delta_time, velocidade_base, escudo_ativo)
        else:
            self._modo_interposicao(delta_time, velocidade_base)

    # ------------------------------------------------------------------
    # MODO 1 — perseguição direta (é o mais próximo)
    # ------------------------------------------------------------------
    def _modo_mais_proximo(self, delta_time, velocidade, escudo_ativo):
        direcao = self.jogador.posicao - self.posicao

        if direcao.length_squared() == 0:
            return

        direcao_norm = direcao.normalize()

        if escudo_ativo and self._modo_arco_ativo:
            # Combina vetor direto com vetor perpendicular de acompanhamento
            perp = self._vetor_perpendicular_arco(direcao_norm)
            # 60% pressão frontal + 40% acompanhamento lateral
            movimento = (direcao_norm * 0.6 + perp * 0.4)
            if movimento.length_squared() > 0:
                movimento = movimento.normalize()
        else:
            movimento = direcao_norm
            self._modo_arco_ativo = False

        self.posicao += movimento * velocidade * delta_time
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

    # ------------------------------------------------------------------
    # MODO 2 — interposição (não é o mais próximo)
    # ------------------------------------------------------------------
    def _modo_interposicao(self, delta_time, velocidade):
        """
        Calcula um ponto na linha entre o player e o Warden mais próximo,
        levemente deslocado em direção ao player para bloquear o acesso.
        """
        alvo_protegido = self._obter_warden_mais_proximo_do_player()
        if alvo_protegido is None or alvo_protegido is self:
            # Fallback: perseguição simples
            direcao = self.jogador.posicao - self.posicao
            if direcao.length_squared() > 0:
                direcao.normalize_ip()
                self.posicao += direcao * velocidade * delta_time
                self.rect.center = (round(self.posicao.x), round(self.posicao.y))
            return

        # Ponto de interposição: 35% do caminho entre o alvo protegido e o player
        # (mais próximo do player para bloquear ativamente)
        ponto_interposicao = alvo_protegido.posicao.lerp(self.jogador.posicao, 0.35)

        direcao = ponto_interposicao - self.posicao
        if direcao.length_squared() == 0:
            return

        # Se já está muito próximo do ponto de interposição, não precisa se mover
        if direcao.length() < 20:
            return

        direcao.normalize_ip()
        self.posicao += direcao * velocidade * delta_time
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

    # ------------------------------------------------------------------
    # DETECÇÃO DE FLANQUE — variação angular do player ao redor do combatente
    # ------------------------------------------------------------------
    def _atualizar_deteccao_arco(self):
        """
        Rastreia o ângulo do vetor self→player frame a frame.
        Se a variação acumulada ultrapassar o limiar, ativa o modo arco.
        """
        vetor = self.jogador.posicao - self.posicao
        if vetor.length_squared() == 0:
            return

        angulo_atual = math.atan2(vetor.y, vetor.x)

        if self._angulo_anterior_player is not None:
            # Diferença angular normalizada em [-π, π]
            delta = angulo_atual - self._angulo_anterior_player
            delta = (delta + math.pi) % (2 * math.pi) - math.pi

            # Decaimento mais lento (0.97) para que o acumulado sustente mais tempo
            # antes de ser apagado, permitindo detectar arcos suaves a 60fps
            self._arco_acumulado = self._arco_acumulado * 0.97 + delta

            # Limiar maior para não ativar com micro-movimentos laterais do player
            # ~0.35 rad acumulados = movimento circular perceptível por ~10 frames
            LIMIAR_FLANQUE = 0.35
            if abs(self._arco_acumulado) > LIMIAR_FLANQUE:
                self._modo_arco_ativo = True
            else:
                self._modo_arco_ativo = False

        self._angulo_anterior_player = angulo_atual

    def _vetor_perpendicular_arco(self, direcao_norm):
        """
        Retorna o vetor perpendicular na direção em que o player está circundando,
        para que o combatente acompanhe o arco do lado correto.
        """
        # Sinal do arco acumulado define para qual lado girar
        sinal = 1.0 if self._arco_acumulado > 0 else -1.0
        return pygame.math.Vector2(-direcao_norm.y * sinal, direcao_norm.x * sinal)

    # ------------------------------------------------------------------
    # UTILITÁRIO — Warden mais próximo do player (exceto self)
    # ------------------------------------------------------------------
    def _obter_warden_mais_proximo_do_player(self):
        corpos = self.obter_todos_os_corpos()
        min_dist = float('inf')
        mais_proximo = None

        for corpo in corpos:
            if corpo is self:
                continue
            dist = corpo.posicao.distance_squared_to(self.jogador.posicao)
            if dist < min_dist:
                min_dist = dist
                mais_proximo = corpo

        return mais_proximo