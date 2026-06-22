# enemies/didact/attacks.py
import pygame
import random
from source.feats.projetil import LaserBeam
from source.feats.skills.skills import OndaEMP
from source.feats.skills.artilharia import ArtilhariaAviso
from source.feats.effects import LaserWarning
from source.systems.entitymanager import entity_manager

class DidactAttacks:
    """Mixin responsável pela execução das habilidades e instanciamento de projéteis."""

    def ativar_laser(self):
        agora = pygame.time.get_ticks()
        self.velocidade = 0
        self.estado_habilidade = 'aviso_laser'
        self.tempo_inicio_laser = agora
        self.tempo_ultimo_laser = agora
        
        self.posicao_alvo_laser = self.jogador.posicao.copy()
        LaserWarning(
            owner=self, 
            alvo=self.jogador, 
            grupos=entity_manager.all_sprites, 
            game=self.game, 
            duracao=self.duracao_aviso_laser)

    def disparar_laser(self):
        direcao_tiro = self.calcular_direcao_tiro(0.0)

        LaserBeam(
            posicao_inicial = self.posicao.copy(), 
            grupos          = (entity_manager.all_sprites,),
            jogador         = self.jogador, 
            game            = self.game, 
            dono            = 'INIMIGO', 
            tamanho         = (128, 128),
            dano            = self.dano_base * 4, 
            velocidade      = 1500,
            direcao_spread  = direcao_tiro,
            vai_rotacionar  = False,
            color           = 'red')

    def puxar_jogador(self):
        agora = pygame.time.get_ticks()
        self.cooldown_pull = self.novo_cooldown(10000, 15000)
        self.estado_habilidade = 'ataque_pull'
        self.tempo_inicio_pull = agora
        self.tempo_ultimo_pull = agora

    def aplicar_efeito_pull(self, delta_time):
        direcao_puxao = self.posicao - self.jogador.posicao
        if direcao_puxao.length_squared() > 0:
            direcao_puxao.normalize_ip()
            
        self.jogador.posicao += direcao_puxao * self.velocidade_puxao * delta_time
        self.jogador.rect.center = self.jogador.posicao

    def ativar_cryptum(self):
        self.adicionar_escudo(self.cryptum_shield)
        self.velocidade = self.velocidade_cryptum
        self.estado_habilidade = 'crypt'
        self.ultima_cryptum = pygame.time.get_ticks()
        
        self.tempo_ultimo_emp = pygame.time.get_ticks()
        self.tempo_ultima_artilharia = pygame.time.get_ticks()

    def disparar_emp(self):
        OndaEMP(
            posicao=self.posicao.copy(), 
            grupos=self.game.all_sprites, 
            game=self.game, 
            atacante=self
            )

    def disparar_artilharia(self):
        self.cooldown_artilharia = self.novo_cooldown(600, 1200)
        
        offset = pygame.math.Vector2(random.randint(-150, 150), random.randint(-150, 150))
        alvo = self.jogador.posicao + offset

        ArtilhariaAviso(
            posicao=alvo,
            grupos=[entity_manager.all_sprites],
            game=self.game,
            dono='INIMIGO',    
            preset='didact_collapse'
            )