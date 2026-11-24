import pygame

from source.feats.skills.continuousbeam import ContinuousBeam
from source.systems.eventos import INIMIGO_MORREU, eventos
from source.systems.gameclock import relogio

from .config import CFG


class GuiltySetup:
    def inicializar_habilidades(self):
        """Estado só do Guilty (o do motor, cooldowns e anti-stuck é da BossBase)."""
        self.raio_colisao_mapa = CFG.raio_colisao_mapa
        self.permitir_spawns_normais = False   # lido pelo Game e pelo Spawner

        # Barreira
        self.barreira = None
        self.sentinelas_derrotadas = 0
        eventos.assinar(INIMIGO_MORREU, self.contar_sentinela)   # as assinaturas valem por partida

        # Feixes: um ContinuousBeam por tipo; `feixe_ativo` é o que está disparando (e é desenhado)
        self.feixe_proximidade = self._criar_feixe(CFG.proximidade)
        self.feixe_laser = self._criar_feixe(CFG.laser)
        self.feixe_fase3 = self._criar_feixe(CFG.laser_fase3)
        self.feixe_ativo = None

        # Invocações: quando cada uma pode sair (ms) e as que estão em andamento
        agora = relogio.agora()
        self.proxima_invocacao = {nome: agora + ms for nome, ms in CFG.intervalo_inicial.items()}
        self.sentinelas = []       # da chuva (fase 1)
        self.super_sentinelas = []
        self.floods = []
        self.avisos_chuva = 0      # artilharias que ainda vão virar sentinela
        self.armadilha = None
        self.luz = None

        # Ronda
        self.ronda_destino = pygame.math.Vector2(self.posicao)
        self.ronda_direcao = pygame.math.Vector2(1, 0)
        self.ronda_ate = 0         # 0: sorteia no primeiro frame
        self._pos_ronda = pygame.math.Vector2(self.posicao)
        self._travado_ms = 0.0

    def _criar_feixe(self, cfg):
        return ContinuousBeam(self, color=cfg.cor, largura_base=cfg.largura,
                              dano_por_segundo=cfg.dps, suavizacao=cfg.suavizacao)
