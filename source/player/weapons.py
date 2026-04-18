import pygame
import math
from source.windows.settings import *
from source.player.player import *
from source.feats.assets import ASSETS
from source.feats.baseweapon import *
from source.feats.projetil import ProjetilUniversal, BurstRifle, ProjetilNeedler, Projetil_Lista, Projetil_PingPong, Aura


class RifleAssalto(Arma):
    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = 'Rifle de Assalto'
        self.descricao = """Rifle UNSC de cadência elevada"""
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        
        # Status
        self.dano = 1
        self.cooldown = 500 
        self.projeteis_por_disparo = 1
        self.velocidade_projetil = 2000
        
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
        super().upgrade() # Aumenta self.nivel
        
        # Aumenta o dano a cada nível
        self.dano += 1
        
        # Reduz o cooldown a cada 2 níveis (disparos mais rápidos)
        if self.nivel % 2 == 0:
            self.cooldown = max(100, self.cooldown - 20)
        
        # Adiciona projéteis extras em níveis específicos
        if self.nivel in [3, 5, 7, 9]:
            self.projeteis_por_disparo += 1


    def ver_proximo_upgrade(self):
        prox_nivel = self.nivel + 1
        prox_dano = self.dano + 1
        
        # SÓ reduz o cooldown na interface se o próximo nível for par
        prox_cooldown = self.cooldown
        if prox_nivel % 2 == 0:
            prox_cooldown = max(100, self.cooldown - 20)
        
        # SÓ aumenta projéteis nos níveis exatos
        prox_projeteis = self.projeteis_por_disparo
        if prox_nivel in [3, 5, 7, 9]:
            prox_projeteis += 1
        
        return {
            'nivel': prox_nivel,
            'dano': prox_dano,
            'cooldown': prox_cooldown,
            'projeteis': prox_projeteis
        }

    def get_estatisticas_para_exibir(self):
        stats_futuros = self.ver_proximo_upgrade()
        res = [f"Dano: {self.dano} -> {stats_futuros['dano']}"]
        # Só adiciona os stats que de fato sofreram alteração
        if stats_futuros['cooldown'] != self.cooldown:
            res.append(f"Cadência de Tiro: {self.cooldown}ms -> {stats_futuros['cooldown']}ms")

        if stats_futuros['projeteis'] != self.projeteis_por_disparo:
            res.append(f"Projéteis: {self.projeteis_por_disparo} -> {stats_futuros['projeteis']}")
        
        return res
    

class Arma_Loop(Arma):
    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.all_sprites, self.grupo_projeteis, self.grupo_inimigos = grupos

        self.dano = 5
        self.velocidade = 1000
        self.cooldown = 1000
        self.rebatidas = 2
        self.nome = "Bola Calderânica"
        self.descricao = """Capaz de rebater nas paredes!"""
        
    def disparar(self):
        inimigo = self.encontrar_inimigo_mais_proximo(self.grupo_inimigos)        
        if inimigo:
            direcao_tiro = (inimigo.posicao - self.jogador.posicao).normalize()
            Projetil_PingPong(
                posicao_inicial=self.jogador.posicao,
                grupos=(self.all_sprites,), # A base vai adicionar o grupo de projéteis do player
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
        #a cada 3 niveis fica mais rapido

        self.rebatidas += 1
        self.dano += 2

    def ver_proximo_upgrade(self):
        prox_nivel = self.nivel + 1
        prox_dano = self.dano + 2
        prox_rebatidas = self.rebatidas + 1

        return {
            'nivel': prox_nivel,
            'dano': prox_dano,
            'rebatidas': prox_rebatidas,
        }
    
    def get_estatisticas_para_exibir(self):
        stats_futuros = self.ver_proximo_upgrade()


        stats_formatados = [
            f"Dano: {self.dano} -> {stats_futuros['dano']}",
            f"Rebotes: {self.rebatidas} -> {stats_futuros['rebatidas']}",
        ]

        return stats_formatados
    

class ArmaLista(Arma):
    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.game = game

        # Específicos da arma
        self.nome = "Ciclo de Lâminas"
        self.descricao = "Protegem o jogador!"
        self.num_listas = 1
        self.dano = 15
        self.cooldown = 6000
        self.duracao = 5000    
        self.velocidade_rotacao = 120 
        self.distancia_orbita = 140    

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

        self.velocidade_rotacao += 10
        self.distancia_orbita += 10
        self.dano += 5

        if self.nivel % 2 == 0:
            self.num_listas += 1

    def ver_proximo_upgrade(self):
        prox_nivel = self.nivel + 1
        # Só adiciona UMA lista a cada 2 níveis
        if prox_nivel % 2 == 0:
            prox_listas = self.num_listas + 1
        else:
            prox_listas = self.num_listas

        return {
            'nivel': prox_nivel,
            'dano': self.dano + 5,
            'velocidade_rotacao': self.velocidade_rotacao + 10,
            'num_listas': prox_listas,
            'orbita' : self.distancia_orbita + 10
        }
    
    def get_estatisticas_para_exibir(self):
        stats_futuros = self.ver_proximo_upgrade()

        res = [
            f"Dano: {self.dano} -> {stats_futuros['dano']}",
            f"Velocidade Angular: {self.velocidade_rotacao}°/s-> {stats_futuros['velocidade_rotacao']}°/s",
            f"Raio da Órbita: {self.distancia_orbita} -> {stats_futuros['orbita']}"
        ]
        # Só exibe stats alterados
        if stats_futuros['num_listas'] != self.num_listas:
            res.append(f"Num. Listas: {self.num_listas} -> {stats_futuros['num_listas']}")

        return res    


class Dicionario_Divino(Arma):
    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs) 
        self.all_sprites, self.auras_grupos, self.inimigos_grupo = grupos
        # Status Iniciais da Arma
        self.nome = "Dicionário Divino"
        self.descricao = "Causa dano por segundo"
        self.dano_por_segundo = 1
        self.raio = 120
        self.cooldown = float('inf') 
        self.area_de_dano = None

    def equipar(self):
        if self.area_de_dano is None:
            self.area_de_dano = Aura(
                jogador=self.jogador,
                raio=self.raio,
                dano_por_segundo=self.dano_por_segundo,
                grupos=(self.all_sprites, self.auras_grupos)
            )

    def disparar(self):
        return False
    
    def upgrade(self):
        super().upgrade() # Aumenta self.nivel

        if self.nivel % 2 == 0:
            self.dano_por_segundo += 1
            
        self.raio += 20

        if self.area_de_dano:
            self.area_de_dano.atualizar_stats(self.raio, self.dano_por_segundo)

    def ver_proximo_upgrade(self):
        prox_nivel = self.nivel + 1
        prox_dano = self.dano_por_segundo
        # Só aumenta o dano a cada 2 níveis
        if prox_nivel % 2 ==0:
            prox_dano += 1

        return {
            'nivel': prox_nivel,
            'dano_por_segundo': prox_dano,
            'raio': self.raio + 20
        }

    def get_estatisticas_para_exibir(self):
        prox = self.ver_proximo_upgrade()
        res = [f"Raio: {self.raio} -> {prox['raio']}"] 
        # Só exibe stats alterados
        if prox['dano_por_segundo'] != self.dano_por_segundo:
            res.append(f"Dano/s: {self.dano_por_segundo:.2f} -> {prox['dano_por_segundo']:.2f}",)

        return res
    
    

class Needler(Arma):
    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.nome = "Needler"
        self.descricao = "Dispara agulhas teleguiadas que explodem ao acumular."
        self.game = game

        # Status iniciais
        self.dano = 1
        self.cooldown = 2000      # Tempo entre rajadas
        self.burst_interval = 100     # Delay rápido entre agulhas (tiro rápido)
        self.burst_count = 3        # 3 tiros por rajada
        self.velocidade = 650
        
        # Estado Interno
        self.tiros_restantes = 0
        self.ultimo_tiro_burst = 0

    def disparar(self) -> bool:
        # Se não houver rajada em curso, inicia uma
        if self.tiros_restantes <= 0:
            self.tiros_restantes = self.burst_count
            return True # Retorna True para resetar o cooldown principal da Arma
        return False
    
    def update(self, delta_time):
        # 1. Lógica do Cooldown Principal (Herdada da Arma)
        # Se o cooldown principal passou, ele chama disparar() que ativa a munição da rajada
        super().update(delta_time)

        # 2. Lógica da Rajada (Burst)
        agora = pygame.time.get_ticks()
        if self.tiros_restantes > 0:
            if agora - self.ultimo_tiro_burst > self.burst_interval:
                inimigo = self.encontrar_inimigo_mais_proximo(self.inimigos_grupo)
                if inimigo:
                    self.spawn_agulha(inimigo)
                    self.tiros_restantes -= 1
                    self.ultimo_tiro_burst = agora
                else:
                    # Se não há inimigos, cancela a rajada para não atirar no nada
                    self.tiros_restantes = 0

    def spawn_agulha(self, inimigo):
        if inimigo and inimigo.alive():
            direcao_vetor = (inimigo.posicao - self.jogador.posicao).normalize()
           
        ProjetilNeedler(
            posicao_inicial=self.jogador.posicao,
            grupos=(self.all_sprites,),
            jogador=self.jogador,
            game=self.game,
            dono= 'PLAYER',
            tamanho=(64, 32),
            dano=self.dano,
            velocidade=self.velocidade,
            direcao_spread=direcao_vetor,
            alvo=inimigo
        )

    def upgrade(self):
        super().upgrade()
        self.dano += 1
        if self.nivel % 3 == 0:
            self.burst_count += 1 # Aumenta o tamanho da rajada

    def ver_proximo_upgrade(self):
        prox_nivel = self.nivel + 1
        prox_dano = self.dano + 1
        # Rajada maior a cada 3 níveis
        prox_burst = self.burst_count + 1 if prox_nivel % 3 == 0 else self.burst_count

        return {"nivel": prox_nivel, "dano": prox_dano, "burst": prox_burst}

    def get_estatisticas_para_exibir(self):
        prox = self.ver_proximo_upgrade()
        res = [f"Dano: {self.dano} -> {prox['dano']}"]
        # Só exibe stats alterados
        if prox['burst'] != self.burst_count:
            res.append(f"Rajada: {self.burst_count} -> {prox['burst']}")

        return res

