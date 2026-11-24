import pygame
import random

from source.feats.items import Items
from source.feats.skills.invisibilidade import Invisibilidade
from source.systems.eventos import eventos, DANO_CAUSADO
from source.systems.status import multiplicador_de_dano

class EnemyCombat:
    def adicionar_escudo(self, valor):
        """Define o valor do escudo do inimigo."""
        self.escudo_maximo = valor
        self.escudo_atual = valor

    def calcular_direcao_tiro(self, spread_range=0):
        """
        Calcula a direção para o jogador com spread opcional.
        spread_range: 0 para tiro preciso, ou um valor (ex: 0.05) para espalhamento.
        """
        direcao = self.jogador.posicao - self.posicao
        if direcao.length_squared() > 0:
            direcao = direcao.normalize()
        else:
            direcao = pygame.math.Vector2(1, 0)

        if spread_range > 0:
            spread = pygame.math.Vector2(
                random.uniform(-spread_range, spread_range),
                random.uniform(-spread_range, spread_range)
            )
            direcao = (direcao + spread)
            if direcao.length() > 0:
                direcao = direcao.normalize()
                
        return direcao

    def receber_dano(self, dano):
        """Contrato de dano dos inimigos (roteiro E1). A regra própria do alvo entra por
        `ajustar_dano_recebido`; o que o valor final tira do escudo e da vida, por `absorver_dano`."""
        valor = self.ajustar_dano_recebido(dano.valor * multiplicador_de_dano(dano, self), dano)
        if valor is None:
            return
        self.absorver_dano(valor)
        eventos.emitir(DANO_CAUSADO, alvo=self, dano=dano, valor=valor)

    def ajustar_dano_recebido(self, valor, dano):
        """Gancho da regra do próprio alvo (ex.: golpe pelas costas do Hunter, sentinelas do Guilty).
        Devolve o valor final, ou None para ignorar o golpe (sem dano e sem evento)."""
        return valor

    def absorver_dano(self, valor):
        """Tira do escudo primeiro e o restante da vida."""
        if self.escudo_atual > 0:
            self.escudo_atual = self.escudo_atual - valor
            if self.escudo_atual < 0:
                # Se o dano for maior que o escudo, o que sobra vai para a vida
                dano_restante = abs(self.escudo_atual)
                self.escudo_atual = 0
                self.vida = max(0, self.vida - dano_restante)
        else:
            # Se não tem escudo, toma dano direto na vida
            self.vida = max(0, self.vida - valor)

    def receber_cura(self, quantidade):
        """Só pelo sistema de status (`aplicar(alvo, Cura(...))`), que já descontou a queimadura."""
        self.vida = min(self.vida + quantidade, self.vida_maxima)

    def receber_escudo(self, quantidade):
        """Só pelo sistema de status (`aplicar(alvo, Escudo(...))`): até o escudo máximo."""
        if self.escudo_maximo > 0:
            self.escudo_atual = min(self.escudo_atual + quantidade, self.escudo_maximo)

    def novo_cooldown(self, minimal, maximum):
        updated_cooldown = random.randint(minimal, maximum)
        return updated_cooldown

    def morrer(self, grupos=None):
        Items.spawn_drop(self.posicao, grupos, **self.tabela_drop)
        self.kill()

    # ── Invisibilidade (skill em feats/skills/invisibilidade) ────────────────────
    def iniciar_invisibilidade(self, preset):
        self.invisibilidade = Invisibilidade(self, preset)

    def atualizar_invisibilidade(self, delta_time):
        """Um passo da camuflagem ativa (sem ela, não faz nada)."""
        if self.invisibilidade is not None and self.invisibilidade.atualizar(delta_time):
            self.invisibilidade = None

    def encerrar_invisibilidade(self):
        """Corta a camuflagem: começa a reaparecer agora."""
        if self.invisibilidade is not None:
            self.invisibilidade.encerrar()

    @property
    def fase_invisibilidade(self):
        """Fase da camuflagem (`FADE_OUT`, `OCULTO`, `FADE_IN`) ou None."""
        return None if self.invisibilidade is None else self.invisibilidade.fase

    def _aplicar_alpha(self, alpha):

        self.alpha_atual = int(alpha)

        if hasattr(self, "image"):
            self.image.set_alpha(self.alpha_atual)