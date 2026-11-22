import pygame

from source.systems.status import aplicar

from .config import CFG, DEFESA


class HunterSetup:
    def inicializar_habilidades(self):
        agora = self._agora
        self.rotina = None
        self.estado_habilidade = 'idle'
        self.ultima_habilidade = None
        self.livre_em = agora                  # pausa entre ataques
        self.cd = {nome: agora + ms for nome, ms in CFG.cooldown_inicial.items()}

        # Movimentação livre
        self.movimento_livre = True
        self.modo_movimento = 'avancar'        # 'avancar' | 'lateral'
        self.sentido_lateral = 1
        self.troca_movimento_em = agora

        # Orientação com atraso
        self.lado = 1 if self.estado_animacao == 'right' else -1
        self.virar_em = None                   # ms em que o timer de virar vence (None = parado)

        # Recuperação do dash: parado, inofensivo, sem animar
        self.is_inofensivo = False
        self.animacao_congelada = False

        # Armadura: começa protegido
        self.vulneravel = False
        aplicar(self, DEFESA, chave=self)

        self._dt = 0.0
        self._paredes = None
        self._direcao_mov = pygame.math.Vector2()
