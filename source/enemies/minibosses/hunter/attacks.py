import pygame
import math
from source.feats.projetil import ProjetilUniversal, PlasmaGun
from source.feats.skills.artilharia import ArtilhariaAviso 
from source.feats.skills.mortar import CanhaoParabolico
from source.systems.entitymanager import entity_manager

class HunterMortarProjectile(ProjetilUniversal):
    def __init__(self, start_pos, target_pos, game, dono):
        # Calcula a direção para o alvo
        dir_vec = target_pos - start_pos
        if dir_vec.length() > 0:
            direcao = dir_vec.normalize()
        else:
            direcao = pygame.math.Vector2(1, 0)
            
        super().__init__(
            posicao_inicial=start_pos,
            grupos=(entity_manager.all_sprites,),
            game=game,
            dono=dono,
            sprite_key='green_laser', 
            tamanho=(96, 96),
            velocidade=400, 
            dano=0, 
            duracao=5000,
            direcao_custom=direcao,
            piercing=float('inf'),    # Passa varando todos os alvos sem morrer
            rotacionar=True
        )
        self.start_pos = pygame.math.Vector2(start_pos)
        self.target_pos = pygame.math.Vector2(target_pos)
        self.total_dist = self.start_pos.distance_to(self.target_pos)
        self.max_height = 250 # Altura máxima do arco parabólico

    def update(self, delta_time):
        # Movimentação "plana" 2D normal
        self.posicao += self.direcao * self.velocidade * delta_time
        distancia_percorrida = self.start_pos.distance_to(self.posicao)
        
        # Verifica se chegou no ponto exato (ou passou dele)
        if distancia_percorrida >= self.total_dist:
            self.detonar_artilharia()
            return

        # Progresso vai de 0.0 (início) a 1.0 (fim)
        progresso = distancia_percorrida / self.total_dist
        # math.sin(progresso * pi) cria um arco perfeito: sobe e depois desce!
        altura = math.sin(progresso * math.pi) * self.max_height
        
        # Subtrai a altura apenas na representação da TELA (eixo Y inverte pra cima)
        self.rect.center = (round(self.posicao.x), round(self.posicao.y - altura))

    def detonar_artilharia(self):
        aviso = ArtilhariaAviso(
            posicao=self.target_pos, 
            grupos=(entity_manager.all_sprites,), 
            game=self.game,
            dono=self.dono,
            preset='hunter_cannon'
        )
        entity_manager.all_sprites.add(aviso)
        self.kill() 


class HunterAttacks:
    def iniciar_run(self, agora):
        self.estado_habilidade = 'run'
        self.tempo_inicio_run = agora
        self.tempo_ultima_run = agora
        self.velocidade_animacao = 250 
        self.velocidade = self.velocidade_corrida
        
        # Calcula e TRAVA o vetor da investida baseada na posição atual do jogador
        vetor_alvo = self.jogador.posicao - self.posicao
        if vetor_alvo.length() > 0:
            self.vetor_investida = vetor_alvo.normalize()
        else:
            self.vetor_investida = pygame.math.Vector2(1, 0)

    def processar_run(self, agora, delta_time, paredes=None):
        self.direcao = self.vetor_investida

        self.posicao += self.vetor_investida * self.velocidade_corrida * delta_time
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        if paredes:
            self.aplicar_colisao_mapa(paredes)
        
        if agora - self.tempo_inicio_run >= self.duracao_run:
            self.estado_habilidade = 'stun'
            self.tempo_inicio_stun = agora
            self.velocidade_animacao = 900 
            self.velocidade = 0 

    def processar_stun(self, agora):
        self.velocidade = 0 # Fica estático
        
        if agora - getattr(self, 'tempo_inicio_stun', 0) >= self.duracao_stun:
            self.estado_habilidade = 'idle'
            self.velocidade = self.velocidade_base
            self.cooldown_run = self.novo_cooldown(8000, 14000)
            self.trava_global = agora + 1000 # Dá meio segundo antes de emendar outro golpe

    def processar_burst(self, agora, delta_time):
        if self.burst_restante > 0:
            self.cronometro_burst += delta_time * 1000
            if self.cronometro_burst >= self.intervalo_burst:
                self.cronometro_burst = 0
                self.burst_restante -= 1
                
                direcao_com_spread = self.calcular_direcao_tiro(0.15)
                PlasmaGun(
                    posicao_inicial=self.posicao,
                    grupos          = (entity_manager.all_sprites,),
                    jogador         = self.jogador,
                    game            = self.game,
                    dono            = 'INIMIGO',
                    dano            = 15,
                    velocidade      = 500,
                    tamanho         = (36, 36),
                    direcao_spread  = direcao_com_spread,
                    vai_rotacionar  = False
                )
        else:
            self.estado_habilidade = 'idle'
            self.cooldown_burst = self.novo_cooldown(4000, 9000)
            self.trava_global = agora + 1000 # <- A trava de 1000ms antes do próximo ataque!

    def processar_cannon(self, agora):
        # Dispara o morteiro parabólico passando a posição atual dele e onde o player está
        CanhaoParabolico(
            start_pos=self.posicao.copy(), 
            target_pos=self.jogador.posicao.copy(), 
            game=self.game, 
            dono='INIMIGO',
            preset_artilharia='hunter_cannon'
        )
        
        self.estado_habilidade = 'idle'
        self.cooldown_cannon = self.novo_cooldown(6000, 12000)
        self.trava_global = agora + 1000 # Trava de 1000ms antes do próximo ataque