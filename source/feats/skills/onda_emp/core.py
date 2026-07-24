# source/feats/skills/onda_emp/core.py
import pygame
from source.systems.entitymanager import entity_manager
from .config import EMP_PRESETS, EMPConfig

class OndaEMP(pygame.sprite.Sprite):
    def __init__(self, posicao, grupos, game, atacante, preset='padrao', custom_config: EMPConfig = None):
        super().__init__(grupos)
        self.game = game
        self.atacante = atacante
        self.posicao = pygame.math.Vector2(posicao)
        
        # Seleção de Configuração
        self.cfg = custom_config if custom_config else EMP_PRESETS.get(preset, EMP_PRESETS['padrao'])
        
        self.raio_atual = 10.0
        self.atingiu_jogador = False
        
        # Elementos padrão para a engine de Sprites do pygame
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.posicao)
        self.hitbox = self.rect.copy()

    def update(self, delta_time, paredes=None):
        # Expansão linear por frame
        self.raio_atual += self.cfg.velocidade_expansao * delta_time
        
        # Condição de término
        if self.raio_atual >= self.cfg.raio_maximo:
            self.kill()
            return

        # LÓGICA DE COLISÃO ULTRA OTIMIZADA: LENGTH_SQUARED (Sem raiz quadrada!)
        if not self.atingiu_jogador:
            jogador = self.atacante.jogador if hasattr(self.atacante, 'jogador') else entity_manager.player
            
            # Distância ao quadrado entre a onda e o jogador
            distancia_sq = self.posicao.distance_squared_to(jogador.posicao)
            
            # Criamos uma margem de detecção ao quadrado para evitar que o frame "pule" a colisão
            largura_colisao = self.cfg.velocidade_expansao * delta_time * 1.5
            raio_min_sq = (self.raio_atual - largura_colisao) ** 2
            raio_max_sq = (self.raio_atual + largura_colisao) ** 2
            
            # Se a distância ao quadrado estiver dentro da coroa circular da borda
            if raio_min_sq <= distancia_sq <= raio_max_sq:
                self.atingiu_jogador = True
                
                # Efeito mecânico de quebra de escudo
                if self.cfg.derrete_escudo and hasattr(jogador, 'escudo_atual') and jogador.escudo_atual > 0:
                    jogador.escudo_atual = 0
                
                # Aplicação do dano nativo
                if hasattr(jogador, 'receber_dano'):
                    jogador.receber_dano(self.cfg.dano)
                elif hasattr(jogador, 'tomar_dano_direto'):
                    jogador.tomar_dano_direto(self.cfg.dano)

    def draw(self, surface, deslocamento=None):
        """
        Renderização com Surfaces locais dinâmicas para evitar memory leaks.
        Aceita o parâmetro de deslocamento/câmera nativo do laço do jogo.
        """
        tamanho_aba = int(self.raio_atual + 25)
        raio_int = int(self.raio_atual)
        
        if raio_int <= 0:
            return
            
        temp_surface = pygame.Surface((tamanho_aba * 2, tamanho_aba * 2), pygame.SRCALPHA)
        centro_local = (tamanho_aba, tamanho_aba)
        
        # Camada Externa (Brilho Alpha)
        pygame.draw.circle(temp_surface, self.cfg.cor_externa, centro_local, raio_int + 10, 20)
        
        # Camada Central (Linha de Choque)
        pygame.draw.circle(temp_surface, self.cfg.cor_central, centro_local, raio_int, self.cfg.espessura_borda)
        
        # Camada Interna (Vácuo Residual)
        if raio_int > 20:
            pygame.draw.circle(temp_surface, self.cfg.cor_interna, centro_local, raio_int - 10, 15)
            
        # Aplicação de Câmera/Deslocamento baseada no motor do seu jogo
        if deslocamento is not None:
            # Se o seu jogo passa o vetor de deslocamento diretamente no draw
            pos_ajustada = self.posicao - deslocamento
        else:
            # Fallback caso use o sistema interno de câmera
            pos_ajustada = self.game.camera.aplicar_posicao(self.posicao) if hasattr(self.game, 'camera') else self.posicao
        
        surface.blit(temp_surface, (pos_ajustada.x - tamanho_aba, pos_ajustada.y - tamanho_aba))