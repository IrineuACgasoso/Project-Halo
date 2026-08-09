import pygame
from ..baseweapon import Arma
from ...projetil import ProjetilNeedler

class Needler(Arma):
    NOME_ASSET = 'needler'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.nome = "Needler"
        self.descricao = "Dispara agulhas teleguiadas que explodem ao acumular."
        self.inicializar_stats(self.NOME_ASSET)
        self.tiros_restantes = 0
        self.ultimo_tiro_burst = 0

    def disparar(self) -> bool:
        if self.tiros_restantes <= 0:
            self.tiros_restantes = self.burst_count
            return True 
        return False
    
    def update(self, delta_time):
        super().update(delta_time)
        agora = pygame.time.get_ticks()
        if self.tiros_restantes > 0:
            if agora - self.ultimo_tiro_burst > self.burst_interval:
                inimigo = self.encontrar_inimigo_mais_proximo(self.inimigos_grupo, raio_maximo=500)
                if inimigo:
                    self._spawn_agulha(inimigo)
                    self.tiros_restantes -= 1
                    self.ultimo_tiro_burst = agora
                else:
                    self.tiros_restantes = 0

    def _spawn_agulha(self, inimigo):
        if inimigo and inimigo.alive():
            direcao_vetor = (inimigo.posicao - self.jogador.posicao).normalize()
           
            # Movido para dentro do IF para evitar UnboundLocalError caso o inimigo morra
            ProjetilNeedler(
                posicao_inicial = self.jogador.posicao,
                grupos          = (self.all_sprites,),
                jogador         = self.jogador,
                game            = self.game,
                dono            = 'PLAYER',
                tamanho         = (64, 32),
                dano            = self.dano,
                velocidade      = self.velocidade,
                direcao_spread  = direcao_vetor,
                alvo            = inimigo
            )

    def upgrade(self):
        super().upgrade()
        self.aplicar_upgrades(self.nivel, self.NOME_ASSET)

    def ver_proximo_upgrade(self):
        return self.ver_proximos_upgrades(self.nivel + 1, self.NOME_ASSET)

    def get_estatisticas_para_exibir(self):
        return super().get_estatisticas_para_exibir(self.nivel + 1, self.NOME_ASSET)

