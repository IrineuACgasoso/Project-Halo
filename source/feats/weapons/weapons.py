import pygame
import math
import random
from dataclasses import replace
from source.feats.skills.artilharia.config import ARTILHARIA_PRESETS
from source.windows.settings import *
from .baseweapon import *
from source.feats.projetil import (
    BurstRifle, ProjetilNeedler, Projetil_Lista, Brick, ProjetilShotgun, 
    LaserBlast, HeavyBurst, LightBullet, Carabin, DizimatorBullet)
from source.feats.auras import PlayerAura
from source.feats.grenades import PlasmaGrenade

class AssaultRifle(Arma):
    NOME_ASSET = 'assault_rifle'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = 'Rifle de Assalto'
        self.descricao = """Rifle UNSC de cadência elevada"""
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.inicializar_stats(self.NOME_ASSET)
        
    def disparar(self):
        inimigo_alvo = self.encontrar_inimigo_mais_proximo(self.inimigos_grupo, raio_maximo=700)
        if inimigo_alvo and inimigo_alvo.alive():
            direcao_vetor = (inimigo_alvo.posicao - self.jogador.posicao).normalize()
            
            for _ in range(self.projeteis_por_disparo):
                BurstRifle(
                    posicao_inicial = self.jogador.posicao,
                    grupos          = (self.all_sprites,), 
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
    

class BrickLauch(Arma):
    NOME_ASSET = 'brick' # Removido o acento perigoso

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = "Tijolo"
        self.descricao = """Arma canônicamente associada ao Master Chief."""
        self.all_sprites, self.grupo_projeteis, self.grupo_inimigos = grupos
        self.inicializar_stats(self.NOME_ASSET)

    def disparar(self):
        inimigo = self.encontrar_inimigo_mais_proximo(self.grupo_inimigos, raio_maximo=1200)        
        if inimigo:
            direcao_tiro = (inimigo.posicao - self.jogador.posicao).normalize()
            Brick(
                posicao_inicial=self.jogador.posicao,
                grupos=(self.all_sprites,),
                jogador=self.jogador,
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
        agora = pygame.time.get_ticks()
        if agora >= self.tempo_fim_ciclo:
            self.disparar()
            self.tempo_fim_ciclo = (agora + self.duracao + self.cooldown)

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


class MK2_Shield(Arma):
    NOME_ASSET = 'mk2_shield'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs) 
        self.all_sprites, self.auras_grupos, self.inimigos_grupo = grupos
        self.nome = "Escudo MK-2"
        self.descricao = "Gera um escudo e causa dano por segundo ao redor do jogador."
        self.area_de_dano = None
        self.inicializar_stats(self.NOME_ASSET)

    def equipar(self):
        self.jogador.adicionar_escudo(self.escudo)
        self.jogador.shield_regen = self.shield_regen
        self.jogador.velocidade_regen_escudo = self.velocidade_regen_escudo

        if self.area_de_dano is None:
            self.area_de_dano = PlayerAura(
                jogador=self.jogador,
                raio=self.raio,
                dano_por_segundo=self.dano_por_segundo,
                grupos=(self.all_sprites, self.auras_grupos)
            )

    def disparar(self): 
        return False
    
    def upgrade(self):
        super().upgrade()
        self.aplicar_upgrades(self.nivel, self.NOME_ASSET)
        if self.area_de_dano:
            self.area_de_dano.atualizar_stats(self.raio, self.dano_por_segundo)
        self.jogador.shield_regen = self.shield_regen
        self.jogador.velocidade_regen_escudo = self.velocidade_regen_escudo
        self.jogador.escudo_maximo = self.escudo

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


class CarabinRifle(Arma):
    NOME_ASSET = 'carabin_rifle'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.nome = "Carabin Rifle"
        self.descricao = "Dispara projéteis de plasma muito eficientes contra escudos."
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
                inimigo = self.encontrar_inimigo_mais_proximo(self.inimigos_grupo, raio_maximo=650)
                if inimigo:
                    self._spawn_carabin(inimigo)
                    self.tiros_restantes -= 1
                    self.ultimo_tiro_burst = agora
                else:
                    self.tiros_restantes = 0

    def _spawn_carabin(self, inimigo):
        if inimigo and inimigo.alive():
            direcao_vetor = (inimigo.posicao - self.jogador.posicao).normalize()
           
            # Movido para dentro do IF para evitar UnboundLocalError caso o inimigo morra
            Carabin(
                posicao_inicial = self.jogador.posicao,
                grupos          = (self.all_sprites,),
                jogador         = self.jogador,
                game            = self.game,
                dono            = 'PLAYER',
                tamanho         = (32, 32),
                dano            = self.dano,
                velocidade      = self.velocidade,
                direcao_spread  = direcao_vetor,
            )

    def upgrade(self):
        super().upgrade()
        self.aplicar_upgrades(self.nivel, self.NOME_ASSET)

    def ver_proximo_upgrade(self):
        return self.ver_proximos_upgrades(self.nivel + 1, self.NOME_ASSET)

    def get_estatisticas_para_exibir(self):
        return super().get_estatisticas_para_exibir(self.nivel + 1, self.NOME_ASSET)


class Shotgun(Arma):
    NOME_ASSET = 'shotgun'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = "Shotgun"
        self.descricao = "Dispara uma salva de estilhaços superaquecidos com leve dispersão."
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.inicializar_stats(self.NOME_ASSET)
        
    def disparar(self) -> bool:
        # Encontra alvos próximos (Shotguns operam melhor à queima-roupa)
        inimigo_alvo = self.encontrar_inimigo_mais_proximo(self.inimigos_grupo, raio_maximo=500)
        if inimigo_alvo and inimigo_alvo.alive():
            direcao_base = (inimigo_alvo.posicao - self.jogador.posicao).normalize()
            
            # Captura propriedades táticas seguras direto do dicionário de dados da arma
            qtd_estilhacos = getattr(self, 'projeteis_por_disparo', 6)
            angulo_espalhamento = getattr(self, 'espalhamento', 14)  # Limite angular do leque em graus
            vel_projetil = getattr(self, 'velocidade_projetil', getattr(self, 'velocidade', 750))
            
            for _ in range(qtd_estilhacos):
                # Rotaciona ligeiramente o vetor para criar o padrão fragmentado em leque
                variacao = random.uniform(-angulo_espalhamento, angulo_espalhamento)
                direcao_spread = direcao_base.rotate(variacao)
                
                ProjetilShotgun(
                    posicao_inicial = self.jogador.posicao,
                    grupos          = (self.all_sprites,), 
                    jogador         = self.jogador,
                    game            = self.game,
                    dono            = 'PLAYER',
                    tamanho         = (32, 14),  # Aspecto bem pontiagudo e fino
                    dano            = self.dano,
                    velocidade      = vel_projetil,
                    direcao_spread  = direcao_spread
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


class SpartanLaser(Arma):
    NOME_ASSET = 'spartan_laser'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = 'Spartan Laser'
        self.descricao = """Feixe de energia concentrada de altíssimo alcance"""
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.inicializar_stats(self.NOME_ASSET)

    def disparar(self):
        inimigo_alvo = self.encontrar_inimigo_mais_forte(self.inimigos_grupo, raio_maximo=self.raio_maximo)
        if inimigo_alvo and inimigo_alvo.alive():
            direcao_vetor = (inimigo_alvo.posicao - self.jogador.posicao).normalize()

            LaserBlast(
                posicao_inicial = self.jogador.posicao,
                grupos          = (self.all_sprites,),
                jogador         = self.jogador,
                game            = self.game,
                dono            = 'PLAYER',
                tamanho         = (260, 30),
                dano            = self.dano,
                velocidade      = self.velocidade_projetil,
                direcao_spread  = direcao_vetor,
                piercing        = self.piercing
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


class GrenadeLauncher(Arma):
    NOME_ASSET = 'grenade_launcher'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = "Lança-Granadas de Plasma"
        self.descricao = "Arremessa granadas de plasma que grudam no primeiro inimigo tocado."
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.inicializar_stats(self.NOME_ASSET)

    def disparar(self):
        inimigo_alvo = self.encontrar_inimigo_mais_proximo(self.inimigos_grupo, raio_maximo=self.raio_maximo)
        if inimigo_alvo and inimigo_alvo.alive():
            # Dano escala com upgrade: clona o preset base trocando só o dano
            config_escalado = replace(ARTILHARIA_PRESETS['plasma_grenade'], dano=self.dano)

            PlasmaGrenade(
                posicao_inicial = self.jogador.posicao,
                posicao_alvo    = inimigo_alvo.posicao,
                grupos          = (self.all_sprites,),
                game            = self.game,
                dono            = 'PLAYER',
                inimigos_grupo  = self.inimigos_grupo,
                custom_config   = config_escalado
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


class SniperRifle(Arma):
    NOME_ASSET = 'sniper_rifle'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = 'Sniper Rifle'
        self.descricao = """Rifle de precisão UNSC, cadência lenta e dano devastador"""
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.inicializar_stats(self.NOME_ASSET)

    def disparar(self):
        inimigo_alvo = self.encontrar_inimigo_mais_forte(self.inimigos_grupo, raio_maximo=1200)
        if inimigo_alvo and inimigo_alvo.alive():
            direcao_vetor = (inimigo_alvo.posicao - self.jogador.posicao).normalize()

            HeavyBurst(
                posicao_inicial = self.jogador.posicao,
                grupos          = (self.all_sprites,),
                jogador         = self.jogador,
                game            = self.game,
                dono            = 'PLAYER',
                tamanho         = (96, 28),
                dano            = self.dano,
                velocidade      = self.velocidade_projetil,
                direcao_spread  = direcao_vetor,
                piercing        = self.piercing
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


class SidekickPistol(Arma):
    NOME_ASSET = 'sidekick_pistol'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = 'Sidekick Pistol'
        self.descricao = """Pistola padrão de elite, causa um grande dano com uma frequência alta."""
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.inicializar_stats(self.NOME_ASSET)

    def disparar(self):
        inimigo_alvo = self.encontrar_inimigo_mais_proximo(self.inimigos_grupo, raio_maximo=600)
        if inimigo_alvo and inimigo_alvo.alive():
            direcao_vetor = (inimigo_alvo.posicao - self.jogador.posicao).normalize()

            HeavyBurst(
                posicao_inicial = self.jogador.posicao,
                grupos          = (self.all_sprites,),
                jogador         = self.jogador,
                game            = self.game,
                dono            = 'PLAYER',
                tamanho         = (48, 16),
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
        agora = pygame.time.get_ticks()
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
            direcao_vetor = (inimigo_alvo.posicao - self.jogador.posicao).normalize()

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


class MachineGun(Arma):
    NOME_ASSET = 'machine_gun'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.nome = "Machine Gun"
        self.descricao = "Altíssima cadência e um dano constante. Cuidado com o superaquecimento!"
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
                inimigo = self.encontrar_inimigo_mais_proximo(self.inimigos_grupo, raio_maximo=850)
                if inimigo:
                    self._spawn_bullet(inimigo)
                    self.tiros_restantes -= 1
                    self.ultimo_tiro_burst = agora
                else:
                    self.tiros_restantes = 0

    def _spawn_bullet(self, inimigo):
        if inimigo and inimigo.alive():
            direcao_vetor = (inimigo.posicao - self.jogador.posicao).normalize()
           
            # Movido para dentro do IF para evitar UnboundLocalError caso o inimigo morra
            BurstRifle(
                posicao_inicial = self.jogador.posicao,
                grupos          = (self.all_sprites,),
                jogador         = self.jogador,
                game            = self.game,
                dono            = 'PLAYER',
                tamanho         = (32, 36),
                dano            = self.dano,
                velocidade      = self.velocidade,
                direcao_spread  = direcao_vetor,
            )

    def upgrade(self):
        super().upgrade()
        self.aplicar_upgrades(self.nivel, self.NOME_ASSET)

    def ver_proximo_upgrade(self):
        return self.ver_proximos_upgrades(self.nivel + 1, self.NOME_ASSET)

    def get_estatisticas_para_exibir(self):
        return super().get_estatisticas_para_exibir(self.nivel + 1, self.NOME_ASSET)


class MjolnirPunch(Arma):
    NOME_ASSET = 'mjolnir_punch'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.nome = "Mjolnir Punch"
        self.descricao = "Contra-ataque Spartan rápido que neutraliza rapidamente pequenas ameaças."
        self.inicializar_stats(self.NOME_ASSET)
        self.ultimo_punch = 0

        if not hasattr(self.jogador, 'espinhos'):
            self.jogador.espinhos = self.espinhos

    def disparar(self):
        return False

    def update(self, delta_time):
        agora = pygame.time.get_ticks()

        if agora - self.ultimo_punch >= self.cooldown:
            self.jogador.espinho_disponivel = True
            self.ultimo_punch = agora
            
    def upgrade(self):
        super().upgrade()
        self.aplicar_upgrades(self.nivel, self.NOME_ASSET)
        self.jogador.espinhos = self.espinhos

    def ver_proximo_upgrade(self):
        return self.ver_proximos_upgrades(self.nivel + 1, self.NOME_ASSET)

    def get_estatisticas_para_exibir(self):
        return super().get_estatisticas_para_exibir(self.nivel + 1, self.NOME_ASSET)


class Dizimator(Arma):
    NOME_ASSET = 'dizimator'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = 'Dizimator'
        self.descricao = """Arma de alto calibre que atira rajadas poderosas a curtas distâncias."""
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
        agora = pygame.time.get_ticks()
        if self.tiros_restantes > 0:
            if agora - self.ultimo_tiro_burst > self.burst_interval:
                inimigo = self.encontrar_inimigo_mais_proximo(self.inimigos_grupo, raio_maximo=550)
                if inimigo:
                    self._spawn_light(inimigo)
                    self.tiros_restantes -= 1
                    self.ultimo_tiro_burst = agora
                else:
                    self.tiros_restantes = 0

    def _spawn_light(self, inimigo):
        if inimigo and inimigo.alive():
            direcao_vetor = (inimigo.posicao - self.jogador.posicao).normalize()

            DizimatorBullet(
                posicao_inicial = self.jogador.posicao,
                grupos          = (self.all_sprites,),
                jogador         = self.jogador,
                game            = self.game,
                dono            = 'PLAYER',
                tamanho         = (32, 32),
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

