import pygame
import math
from source.windows.settings import *
from source.player.player import *
from source.feats.assets import ASSETS
from source.feats.data import WEAPON_DATA
from source.feats.baseweapon import *
from source.feats.projetil import ProjetilUniversal, BurstRifle, ProjetilNeedler, Projetil_Lista, Projetil_PingPong, Aura


class RifleAssalto(Arma):
    NOME_ASSET = 'rifle_assalto'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = 'Rifle de Assalto'
        self.descricao = """Rifle UNSC de cadência elevada"""
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        # Status
        self.inicializar_stats(self.NOME_ASSET)
        
    def disparar(self):
        inimigo_alvo = self.encontrar_inimigo_mais_proximo(self.inimigos_grupo)
        if inimigo_alvo and inimigo_alvo.alive():
            direcao_vetor = (inimigo_alvo.posicao - self.jogador.posicao).normalize()
            
            # Dispara projéteis múltiplos, se o nível permitir
            for _ in range(self.projeteis_por_disparo):
                BurstRifle(
                    posicao_inicial = self.jogador.posicao,
                    grupos          = (self.all_sprites,), # Apenas o grupo visual
                    jogador         = self.jogador,
                    game            = self.game,
                    dono            ='PLAYER',
                    tamanho         = (24, 24),
                    dano            = self.dano,
                    velocidade      = self.velocidade_projetil,
                    direcao_spread  = direcao_vetor
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
    

class Arma_Loop(Arma):
    NOME_ASSET = 'bola_calderânica'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = "Bola Calderânica"
        self.descricao = """Capaz de rebater nas paredes!"""
        self.all_sprites, self.grupo_projeteis, self.grupo_inimigos = grupos
        self.inicializar_stats(self.NOME_ASSET)

    def disparar(self):
        inimigo = self.encontrar_inimigo_mais_proximo(self.grupo_inimigos)        
        if inimigo:
            direcao_tiro = (inimigo.posicao - self.jogador.posicao).normalize()
            Projetil_PingPong(
                posicao_inicial=self.jogador.posicao,
                grupos=(self.all_sprites,),
                game=self.game,
                direcao=direcao_tiro,
                dano=self.dano,
                velocidade=self.velocidade,
                rebatidas=self.rebatidas
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
    

class ArmaLista(Arma):
    NOME_ASSET = 'ciclo_de_laminas'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = "Ciclo de Lâminas"
        self.descricao = "Protegem o jogador!"
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.inicializar_stats(self.NOME_ASSET)

    def disparar(self):
        angulo_step = 360 / self.num_listas
        for i in range(self.num_listas):
            Projetil_Lista(
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


class Dicionario_Divino(Arma):
    NOME_ASSET = 'dicionario_divino'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs) 
        self.all_sprites, self.auras_grupos, self.inimigos_grupo = grupos
        self.nome = "Dicionário Divino"
        self.descricao = "Causa dano por segundo ao redor do jogador."
        self.area_de_dano = None
        self.inicializar_stats(self.NOME_ASSET)


    def equipar(self):
        if self.area_de_dano is None:
            self.area_de_dano = Aura(
                jogador=self.jogador,
                raio=self.raio,
                dano_por_segundo=self.dano_por_segundo,
                grupos=(self.all_sprites, self.auras_grupos)
            )

    def disparar(self): return False
    
    def upgrade(self):
        super().upgrade()
        self.aplicar_upgrades(self.nivel, self.NOME_ASSET)
        if self.area_de_dano:
            self.area_de_dano.atualizar_stats(self.raio, self.dano_por_segundo)

    def ver_proximo_upgrade(self):
        return self.ver_proximos_upgrades(self.nivel + 1, self.NOME_ASSET)

    def get_estatisticas_para_exibir(self):
        return super().get_estatisticas_para_exibir(self.nivel + 1, self.NOME_ASSET)
    

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
        # Se não houver rajada em curso, inicia uma
        if self.tiros_restantes <= 0:
            self.tiros_restantes = self.burst_count
            return True # Retorna True para resetar o cooldown principal da Arma
        return False
    
    def update(self, delta_time):
        # Se o cooldown principal passou, ele chama disparar() que ativa a munição da rajada
        super().update(delta_time)

        # Lógica da Rajada (Burst)
        agora = pygame.time.get_ticks()
        if self.tiros_restantes > 0:
            if agora - self.ultimo_tiro_burst > self.burst_interval:
                inimigo = self.encontrar_inimigo_mais_proximo(self.inimigos_grupo)
                if inimigo:
                    self._spawn_agulha(inimigo)
                    self.tiros_restantes -= 1
                    self.ultimo_tiro_burst = agora
                else:
                    # Se não há inimigos, cancela a rajada para não atirar no nada
                    self.tiros_restantes = 0

    def _spawn_agulha(self, inimigo):
        if inimigo and inimigo.alive():
            direcao_vetor = (inimigo.posicao - self.jogador.posicao).normalize()
           
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

