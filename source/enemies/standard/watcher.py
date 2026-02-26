import pygame
import random
from os.path import join
from enemies.enemies import InimigoBase
from player import *
from settings import *
from feats.items import *
from feats.effects import RaioEscudo
from entitymanager import entity_manager

class Watcher(InimigoBase):
    def __init__(self, posicao, game):
        # 1. A Base gerencia o cache e define self.posicao inicial
        super().__init__(posicao, vida_base=25, dano_base=5, velocidade_base=180, game=game, sprite_key='watcher')
        
        # 2. Busca os sprites já processados (Cache Global)
        self.sprites = self.get_sprites('default')

        # 3. Configuração de animação
        self.frame_atual = 0  
        self.estado_animacao = 'left'
        self.image = self.sprites[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))
        
        self.velocidade_animacao = 300
        self.ultimo_update_animacao = pygame.time.get_ticks()

        # --- NOVO: LÓGICA DE SUPORTE ---
        self.alvo_protegido = None
        self.distancia_ideal = 120 # Fica orbitando a esta distância do aliado
        
        # Balanceamento do Escudo
        self.ultimo_escudo = pygame.time.get_ticks()
        self.intervalo_escudo = 2000     # Aplica escudo a cada 2 segundos
        self.porcentagem_escudo = 0.05   # 5% da vida máxima do alvo
        self.min_escudo = 15             # Fluxo Mínimo (bom para Crawlers)
        self.max_escudo = 80             # Fluxo Máximo (impede o Guilty Spark de virar um deus)

    def buscar_novo_alvo(self):
        """Procura o inimigo mais próximo que AINDA PRECISE de escudo."""
        menor_distancia = float('inf')
        novo_alvo = None
        
        for inimigo in entity_manager.inimigos_grupo:
            # Não protege a si mesmo, não protege outros Watchers e o alvo deve estar vivo
            if inimigo != self and not isinstance(inimigo, Watcher) and inimigo.alive():
                
                # --- NOVO: Só foca no inimigo se ele tiver espaço para receber escudo ---
                escudo_atual = getattr(inimigo, 'escudo', 0)
                if escudo_atual < inimigo.vida_base:
                    distancia = (inimigo.posicao - self.posicao).length()
                    if distancia < menor_distancia:
                        menor_distancia = distancia
                        novo_alvo = inimigo
                    
        self.alvo_protegido = novo_alvo


    def aplicar_escudo(self):
        """Transfere o escudo para o alvo protegido respeitando o Min/Max, distância e cap total."""
        agora = pygame.time.get_ticks()
        
        if self.alvo_protegido and agora - self.ultimo_escudo >= self.intervalo_escudo:
            
            # --- NOVO 1: LIMITE DE DISTÂNCIA ---
            # Checa se o alvo está dentro da distância permitida (2x a distância ideal)
            distancia_atual = (self.alvo_protegido.posicao - self.posicao).length()
            if distancia_atual <= (self.distancia_ideal * 2):
                
                self.ultimo_escudo = agora
                
                # Garante que a variável 'escudo' existe no alvo
                if not hasattr(self.alvo_protegido, 'escudo'):
                    self.alvo_protegido.escudo = 0
                    
                # --- NOVO 2: LIMITE MÁXIMO DO ESCUDO TOTAL ---
                # Só calcula e aplica se o escudo atual for menor que a vida máxima do alvo
                if self.alvo_protegido.escudo < self.alvo_protegido.vida_base:
                    
                    # Calcula o fluxo base de transferência
                    valor_calculado = self.alvo_protegido.vida_base * self.porcentagem_escudo
                    transferencia = max(self.min_escudo, min(valor_calculado, self.max_escudo))
                    
                    # Trava final: garante que a transferência não faça o escudo passar da vida máxima
                    espaco_disponivel = self.alvo_protegido.vida_base - self.alvo_protegido.escudo
                    transferencia = min(transferencia, espaco_disponivel)
                    
                    # Entrega o escudo
                    self.alvo_protegido.escudo += transferencia
                    
                    # Invoca o efeito visual (apenas se realmente transferiu escudo)
                    if transferencia > 0:
                        RaioEscudo(
                            fonte=self, 
                            alvo=self.alvo_protegido, 
                            grupos=(entity_manager.all_sprites,), 
                            cor=(255, 40, 0) 
                        )

    def animar(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))

    def update(self, delta_time, paredes=None):
        # 1. Checa se precisa de um alvo novo (Se nasceu agora, morreu, ou se o ESCUDO ENCHEU)
        precisa_novo_alvo = False
        
        if self.alvo_protegido is None or not self.alvo_protegido.alive():
            precisa_novo_alvo = True
        else:
            # --- NOVO: Verifica se o alvo atual já chegou no limite do escudo ---
            escudo_atual = getattr(self.alvo_protegido, 'escudo', 0)
            if escudo_atual >= self.alvo_protegido.vida_base:
                precisa_novo_alvo = True
                
        if precisa_novo_alvo:
            self.buscar_novo_alvo()

        direcao_movimento = pygame.math.Vector2(0, 0)
        olhar_para_x = self.jogador.posicao.x # Por padrão, encara o jogador

        # 2. Movimentação (Segue o Aliado)
        if self.alvo_protegido:
            olhar_para_x = self.alvo_protegido.posicao.x
            vetor_para_alvo = self.alvo_protegido.posicao - self.posicao
            distancia = vetor_para_alvo.length()
            
            if distancia > 0:
                direcao_alvo = vetor_para_alvo.normalize()
                
                # Se está longe, chega mais perto. Se está colado, se afasta para manter a "órbita".
                if distancia > self.distancia_ideal + 15:
                    direcao_movimento = direcao_alvo
                elif distancia < self.distancia_ideal - 15:
                    direcao_movimento = -direcao_alvo
                    
        # 3. Movimentação (Se não tem aliados vivos, foge do jogador)
        else:
            vetor_fuga = self.posicao - self.jogador.posicao
            if vetor_fuga.length() > 0:
                direcao_movimento = vetor_fuga.normalize()

        # 4. Aplica o movimento 
        if direcao_movimento.length() > 0:
            direcao_movimento = direcao_movimento.normalize()
            nova_pos = self.posicao + direcao_movimento * self.velocidade * delta_time
            
            self.posicao = nova_pos

        # 5. Colisão com paredes
        if paredes:
            self.aplicar_colisao_mapa(paredes, self.raio_colisao_mapa)
            
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        # 6. Atualiza pra que lado o sprite está olhando
        if olhar_para_x < self.posicao.x:
            self.estado_animacao = 'left'
        elif olhar_para_x > self.posicao.x:
            self.estado_animacao = 'right'

        # 7. Dispara as ações finais
        self.aplicar_escudo()
        self.animar()