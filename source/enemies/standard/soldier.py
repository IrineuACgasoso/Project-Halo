import pygame
import random
import math
from os.path import join
from enemies.enemies import InimigoBase
from player import *
from settings import *
from feats.items import *
from feats.projetil import LightRifle
from feats.effects import PrometheanTeleport
from systems.entitymanager import entity_manager

# (Aviso: certifique-se de que a classe PrometheanTeleport está importada aqui!)

class Soldier(InimigoBase):
    def __init__(self, posicao, game):
        super().__init__(posicao, vida_base=10, dano_base=10, velocidade_base=90, game=game, sprite_key='soldier')
        
        # Sorteio do tipo
        escolhido = random.randint(1, 10)
        if escolhido > 5:
            self.tipo = 'sniper'
            self.distancia_ideal = 600
            self.pente_rajada = 1
            self.tamanho = (48, 48)
            self.dano_rifle = 40
            self.velocidade_rifle = 850
        else:
            self.tipo = 'default'
            self.distancia_ideal = 350
            self.pente_rajada = 5
            self.tamanho = (24, 24)
            self.dano_rifle = 5
            self.velocidade_rifle = 600
        
        # Animação e Estados
        self.sprites = self.get_sprites(self.tipo)
        self.frame_atual = 0  
        self.estado_animacao = 'left'
        self.image = self.sprites[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center=self.posicao)
        
        self.velocidade_animacao = 250
        self.ultimo_update_animacao = pygame.time.get_ticks()
        
        # --- NOVO: ESTADO DO TELEPORTE ---
        self.estado = 'normal' # Pode ser 'normal' ou 'teleportando'
        self.particula_teleporte = None
        self.alvo_teleporte = None
        self.ultimo_teleporte = pygame.time.get_ticks()
        # Cooldown gigante para imersão e performance (entre 12 e 20 segundos)
        self.cooldown_teleporte = random.randint(12000, 20000) 

        # Combate (Rajada Tripla e Cooldown)
        self.opcoes_cooldown = (7000, 9000, 11000, 13000)
        self.cooldown_rifle = random.choice(self.opcoes_cooldown)
        self.ultimo_tiro_principal = pygame.time.get_ticks()
        
        self.tiros_restantes_rajada = 0
        self.delay_entre_tiros = 150 
        self.ultimo_tiro_rajada = 0

    @property
    def invulneravel(self):
        return self.estado == 'teleportando'
    

    def animar(self):
        agora = pygame.time.get_ticks()
        # Só anima se estiver no estado normal
        if self.estado == 'normal': 
            if agora - self.ultimo_update_animacao > self.velocidade_animacao:
                self.ultimo_update_animacao = agora
                self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
                
                # Puxa a imagem limpa do cache sem mexer em alpha
                self.image = self.sprites[self.estado_animacao][self.frame_atual]
                self.rect = self.image.get_rect(center=self.posicao)
    
    def gerenciar_rifle(self):
        agora = pygame.time.get_ticks()
        
        if self.tiros_restantes_rajada > 0:
            if agora - self.ultimo_tiro_rajada >= self.delay_entre_tiros:
                self.atirar_lightrifle()
                self.tiros_restantes_rajada -= 1
                self.ultimo_tiro_rajada = agora
        else:
            if agora - self.ultimo_tiro_principal >= self.cooldown_rifle:
                self.tiros_restantes_rajada = self.pente_rajada
                self.cooldown_rifle = random.choice(self.opcoes_cooldown)
                self.ultimo_tiro_principal = agora

    def atirar_lightrifle(self):
        direcao_tiro = self.jogador.posicao - self.posicao
        if direcao_tiro.length() > 0:
            direcao_tiro = direcao_tiro.normalize()
        else:
            direcao_tiro = pygame.math.Vector2(1, 0)
            
        LightRifle(
            posicao_inicial=self.posicao.copy(),
            grupos=(entity_manager.all_sprites, entity_manager.projeteis_inimigos_grupo),
            jogador=self.jogador,
            game=self.game,
            tamanho=self.tamanho,
            dano=self.dano_rifle,
            velocidade=self.velocidade_rifle,
            direcao_spread=direcao_tiro
        ) 

    def iniciar_teleporte(self):
        """Calcula um ponto de flanco e dispara o efeito de teleporte com Failsafe."""
        self.estado = 'teleportando'
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        
        posicao_valida = False
        tentativas = 0
        alvo_teste = pygame.math.Vector2(0, 0)
        
        # Tenta achar uma posição válida até 15 vezes
        while not posicao_valida and tentativas < 15:
            tentativas += 1
            angulo = random.uniform(0, 2 * math.pi)
            
            offset_x = math.cos(angulo) * self.distancia_ideal
            offset_y = math.sin(angulo) * self.distancia_ideal
            alvo_teste.update(self.jogador.posicao.x + offset_x, self.jogador.posicao.y + offset_y)
            
            if self.game.mapa.posicao_e_valida(alvo_teste):
                posicao_valida = True
                
        # Se achou um lugar seguro, marca o alvo. Se não (corredor apertado), não sai do lugar.
        if posicao_valida:
            self.alvo_teleporte = alvo_teste
        else:
            self.alvo_teleporte = self.posicao.copy()
        
        # Instancia a sua partícula de teleporte
        self.particula_teleporte = PrometheanTeleport(
            start_pos=self.posicao, 
            target_pos=self.alvo_teleporte, 
            pixel_size=(6, 8), # Você pode ajustar esses valores do seu efeito
            offset_xy=50, 
            num_quad=(15, 25), 
            grupos=(entity_manager.all_sprites,), 
            game=self.game
        )

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()

        # --- LÓGICA DO TELEPORTE (SEQUESTRANDO O UPDATE) ---
        if self.estado == 'teleportando':
            if not self.particula_teleporte.alive():
                self.posicao = self.alvo_teleporte.copy()
                
                # Reseta tudo e volta ao normal
                self.estado = 'normal'
                
                # Devolve a imagem correta pro Soldier reaparecer
                self.image = self.sprites[self.estado_animacao][self.frame_atual]
                self.rect = self.image.get_rect(center=self.posicao)
                
                self.ultimo_teleporte = agora
                self.cooldown_teleporte = random.randint(12000, 20000)
            return
        
        # Inicia o teleporte se o cooldown acabou e ele não está atirando a rajada
        if agora - self.ultimo_teleporte >= self.cooldown_teleporte and self.tiros_restantes_rajada == 0:
            self.iniciar_teleporte()
            return

        # --- INTELIGÊNCIA ARTIFICIAL: BANDO E DISTÂNCIA (Normal) ---
        vetor_para_jogador = self.jogador.posicao - self.posicao
        distancia = vetor_para_jogador.length()
        direcao_final = pygame.math.Vector2(0, 0)
        
        if distancia > 0:
            direcao_alvo = vetor_para_jogador.normalize()
            
            if distancia > self.distancia_ideal:
                direcao_final += direcao_alvo
            elif distancia < self.distancia_ideal - 50:
                direcao_final -= direcao_alvo
                
            vetor_separacao = pygame.math.Vector2(0, 0)
            vizinhos = 0
            for outro in entity_manager.inimigos_grupo:
                if outro != self and hasattr(outro, 'estado') and outro.estado == 'normal': # Ignora aliados que estão teleportando
                    vetor_outro = self.posicao - outro.posicao
                    dist_outro = vetor_outro.length()
                    if 0 < dist_outro < 90: 
                        vetor_separacao += vetor_outro.normalize() / dist_outro
                        vizinhos += 1
            
            if vizinhos > 0:
                direcao_final += vetor_separacao * 30 
                
            if direcao_final.length() > 0:
                direcao_final = direcao_final.normalize()
                
            self.posicao += direcao_final * self.velocidade * delta_time

        if paredes:
            self.aplicar_colisao_mapa(paredes, self.raio_colisao_mapa)
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        if vetor_para_jogador.x < 0:
            self.estado_animacao = 'left'
        elif vetor_para_jogador.x > 0:
            self.estado_animacao = 'right'

        self.gerenciar_rifle()
        self.animar()