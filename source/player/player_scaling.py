import pygame
from .levelup import TelaDeUpgrade

class PlayerScaling:
    def coletar_item(self, item):
        houve_level_up = False
        
        if item.tipo in self.coletaveis:
            self.coletaveis[item.tipo] += 1

        # efeitos
        if item.tipo == 'exp_shard':
            if self.ganhar_xp(10): 
                houve_level_up = True
        elif item.tipo == 'big_shard':
            if self.ganhar_xp(50):
                houve_level_up = True
        elif item.tipo == 'life_orb':
            self.curar(self.vida_maxima)
        elif item.tipo == 'cafe':
            self.vida_atual = self.vida_maxima
            self.adicionar_tempo_buff(10)
        
        return houve_level_up
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