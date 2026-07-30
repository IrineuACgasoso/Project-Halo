import random
import pygame
from source.systems.levelup import TelaDeUpgrade

class PlayerScaling:
    def ganhar_xp(self, quantidade):
        self.experiencia_atual += quantidade
        if self.experiencia_atual >= self.experiencia_level_up:
            self.level_up()

    def level_up(self):
        self.experiencia_atual -= self.experiencia_level_up
        self.contador_niveis += 1
        self.vida_maxima += 25
        self.velocidade += 10
        self.pontuacao += 100
        self.curar(self.vida_maxima / 4)
        self.escudo_atual = self.escudo_maximo

        self.game.estado_do_jogo = 'level_up'
        self.game.tela_de_upgrade_ativa = TelaDeUpgrade(self.game.tela, self, self.game)

        self.experiencia_level_up = self.experiencia_level_up_base + 10 * self.contador_niveis

    def ativar_upgrade_forcado(self, id_forcado=None):
        """Abre a tela de upgrade mostrando UMA única arma. Se `id_forcado`
        vier preenchido (o item já sabia qual arma era desde o spawn), usa
        ele direto. Caso contrário, sorteia entre as armas já possuídas
        (fallback pra drops antigos/manuais sem id definido)."""
        if not self.armas:
            self.level_up()
            return

        id_escolhido = id_forcado if id_forcado in self.armas else random.choice(sorted(self.armas.keys()))

        self.game.estado_do_jogo = 'level_up'
        self.game.tela_de_upgrade_ativa = TelaDeUpgrade(
            self.game.tela, self, self.game, id_arma_forcada=id_escolhido
        )

    def adicionar_tempo_buff(self, segundos):
        self.buff_timer += segundos

    def atualizar_buff(self, delta_time):
        if self.buff_timer > 0:
            self.buff_timer -= delta_time
            if not self.buff_cooldown_ativo:
                self.buff_cooldown_ativo = True
                for arma in self.armas.values():
                    if hasattr(arma, 'cooldown') and arma.cooldown != float('inf'):
                        arma.cooldown_original = arma.cooldown
                        arma.cooldown /= 2

        elif self.buff_timer <= 0 and self.buff_cooldown_ativo:
            self.buff_timer = 0
            self.buff_cooldown_ativo = False
            for arma in self.armas.values():
                if hasattr(arma, 'cooldown_original'):
                    arma.cooldown = arma.cooldown_original