import pygame
from source.systems.gameclock import relogio
from ..baseweapon import Arma
from ...projetil import EnergySwordProj


class EnergySword(Arma):
    NOME_ASSET = 'energy_sword'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = "Energy Sword"
        self.descricao = "Lâminas de energia para ataques de curta distância."
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.inicializar_stats(self.NOME_ASSET)
        self.tempo_fim_ciclo = 0

    def update(self, delta_time):
        agora = relogio.agora()
        if agora >= self.tempo_fim_ciclo:
            self.disparar()
            self.tempo_fim_ciclo = (agora + self.duracao + self.cooldown)

    def disparar(self):
        angulo_step = 360 / self.num_listas
        for i in range(self.num_listas):
            EnergySwordProj(
                posicao_inicial=self.jogador.posicao,
                grupos=(self.all_sprites,),
                game=self.game,
                dano=self.dano,
                angulo_inicial=i * angulo_step,
                duracao=self.duracao,
                velocidade_rotacao=self.velocidade_rotacao, 
                distancia_orbita=self.distancia_orbita
            )
        return True
    
    def upgrade(self):
        super().upgrade()
        self.aplicar_upgrades(self.nivel, self.NOME_ASSET)

    def ver_proximo_upgrade(self):
        return self.ver_proximos_upgrades(self.nivel + 1, self.NOME_ASSET)
    
    def get_estatisticas_para_exibir(self):
        return super().get_estatisticas_para_exibir(self.nivel + 1, self.NOME_ASSET)
