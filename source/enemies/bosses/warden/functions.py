import pygame

from .behaviors import SniperBehavior, BruiserBehavior, AssassinBehavior


class WardenFunctions(SniperBehavior, BruiserBehavior, AssassinBehavior):

    # =========================================================================
    # UTILITÁRIOS COMPARTILHADOS
    # =========================================================================

    def obter_todos_os_corpos(self):
        """Coleta todos os corpos físicos ativos através do manager da consciência."""
        if hasattr(self, 'manager') and self.manager:
            return [w for w in self.manager.wardens_vivos if w.alive()]
        return [self]

    def sou_o_mais_proximo(self):
        """Verifica se este corpo é o alvo mais fácil para o jogador alcançar."""
        corpos = self.obter_todos_os_corpos()
        if not corpos:
            return False

        min_dist = float('inf')
        mais_proximo = None

        for corpo in corpos:
            dist = corpo.posicao.distance_squared_to(self.jogador.posicao)
            if dist < min_dist:
                min_dist = dist
                mais_proximo = corpo

        return mais_proximo == self

    def processar_reposicionamento(self, delta_time):
        """Move o Warden até o ponto de reposicionamento tático."""
        if not hasattr(self, 'alvo_reposicionamento') or self.alvo_reposicionamento is None:
            self.estado_habilidade = 'idle'
            return

        direcao = self.alvo_reposicionamento - self.posicao
        distancia = direcao.length()

        if distancia < 10:
            self.estado_habilidade = 'idle'
            self.alvo_reposicionamento = None
        else:
            direcao.normalize_ip()
            self.posicao += direcao * 80 * delta_time
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))

    # =========================================================================
    # ROTEADOR DE COMPORTAMENTO
    # =========================================================================

    def aplicar_comportamento_da_funcao(self, delta_time):
        """Despacha para o behavior correto baseado na função atual."""
        agora = pygame.time.get_ticks()

        if self.funcao_atual == 'ATIRADOR':
            self._comportamento_atirador(delta_time)
        elif self.funcao_atual == 'COMBATENTE':
            self._comportamento_combatente(delta_time)
        elif self.funcao_atual == 'ASSASSINO':
            self._comportamento_assassino(delta_time, agora)