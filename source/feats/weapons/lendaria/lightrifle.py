from ..baseweapon import Arma
from ...projetil import LightBullet
import pygame
from source.systems.gameclock import relogio

class LightRifle(Arma):
    NOME_ASSET = 'light_rifle'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = 'Light Rifle'
        self.descricao = """Rifle de supressão contínua, perfeito para destruir inimigos fortes."""
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
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
        agora = relogio.agora()
        if self.tiros_restantes > 0:
            if agora - self.ultimo_tiro_burst > self.burst_interval:
                inimigo = self.encontrar_inimigo_mais_forte(self.inimigos_grupo, raio_maximo=1000)
                if inimigo:
                    self._spawn_light()
                    self.tiros_restantes -= 1
                    self.ultimo_tiro_burst = agora
                else:
                    self.tiros_restantes = 0

    def _spawn_light(self):
        inimigo_alvo = self.encontrar_inimigo_mais_forte(self.inimigos_grupo, raio_maximo=1000)
        if inimigo_alvo and inimigo_alvo.alive():
            direcao_vetor = self.direcao_para(inimigo_alvo)

            LightBullet(
                posicao_inicial = self.jogador.posicao,
                grupos          = (self.all_sprites,),
                jogador         = self.jogador,
                game            = self.game,
                dono            = 'PLAYER',
                tamanho         = (48, 24),
                dano            = self.dano,
                velocidade      = self.velocidade_projetil,
                direcao_spread  = direcao_vetor,
            )
            return True
        return False

    def upgrade(self):
        super().upgrade()
        self.aplicar_upgrades(self.nivel, self.NOME_ASSET)

    def ver_proximo_upgrade(self):
        return self.ver_proximos_upgrades(self.nivel + 1, self.NOME_ASSET)

    def get_estatisticas_para_exibir(self):
        return super().get_estatisticas_para_exibir(self.nivel + 1, self.NOME_ASSET)
