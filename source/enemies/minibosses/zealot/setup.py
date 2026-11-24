import pygame

from .config import CFG


class ZealotSetup:
    def inicializar_habilidades(self):
        """Estado só do Zealot (o do motor, cooldowns e anti-stuck é da BossBase)."""
        # Nasce com o escudo cheio, na mesma escala de dificuldade da vida
        self.adicionar_escudo(CFG.escudo * self.vida_maxima / CFG.vida)

        self.is_inofensivo = False         # parado golpeando: sem dano de contato
        self._olhar_x = None               # lado forçado no frame (dash, fuga); None = olha para o jogador
        self._buff = None                  # bônus de velocidade ativo (só invisível)

        # Perseguição camuflada: contorna paredes
        self._pos_perseguicao = pygame.math.Vector2(self.posicao)
        self._travado_ms = 0.0
        self._contornar_ate = 0
        self._lado_contorno = 1

        # Fuga
        self._ponto_fuga = pygame.math.Vector2(self.posicao)
        self._troca_fuga_em = 0
