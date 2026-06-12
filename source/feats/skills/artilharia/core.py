# source/feats/skills/artilharia/core.py
import pygame
from source.systems.entitymanager import entity_manager
from .config import ARTILHARIA_PRESETS, ArtilhariaConfig

class ArtilhariaAviso(pygame.sprite.Sprite):
    def __init__(self, posicao, grupos, game, dono='BOSS', preset='padrao', custom_config: ArtilhariaConfig = None):
        super().__init__(grupos)
        self.game = game
        self.dono = dono
        self.posicao = pygame.math.Vector2(posicao)
        
        # Carrega a configuração (A customizada tem prioridade, útil para o PurgeGrid)
        self.cfg = custom_config if custom_config else ARTILHARIA_PRESETS.get(preset, ARTILHARIA_PRESETS['padrao'])
        
        self.tempo_criacao = pygame.time.get_ticks()
        self.explodiu = False

        # --- Requisito para o pygame.sprite lidar com desenho ---
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.posicao)
        
        # FIX: Atributo falso para enganar a física/colisão padrão da engine
        self.hitbox = self.rect.copy() 

    def ao_atingir_alvo(self, alvo):
        """ 
        FIX ANTI-CRASH: 
        O collision_manager chama isso se a artilharia estiver no grupo de projéteis.
        Retornamos False porque a artilharia lida com o próprio dano em área no update().
        """
        return False

    def draw(self, surface, offset):
        pos_ajustada = self.posicao - offset
        agora = pygame.time.get_ticks()
        
        # Otimização: Criar uma superfície do tamanho da explosão, e não da tela toda
        tamanho_surf = self.cfg.raio_explosao * 2
        temp_surface = pygame.Surface((tamanho_surf, tamanho_surf), pygame.SRCALPHA)
        centro_local = (self.cfg.raio_explosao, self.cfg.raio_explosao)
        
        if not self.explodiu:
            progresso = min((agora - self.tempo_criacao) / self.cfg.duracao, 1)
            raio_interno = int(self.cfg.raio_explosao * progresso)
            
            # Borda do círculo
            pygame.draw.circle(temp_surface, self.cfg.cor_borda, centro_local, self.cfg.raio_explosao, 4)
            # Preenchimento crescendo
            if raio_interno > 0:
                pygame.draw.circle(temp_surface, self.cfg.cor_preenchimento, centro_local, raio_interno)
        else:
            # Impacto da explosão
            pygame.draw.circle(temp_surface, self.cfg.cor_explosao, centro_local, self.cfg.raio_explosao)

        # Desenha a superfície temporária na tela, centralizada na posição real
        surface.blit(temp_surface, (pos_ajustada.x - self.cfg.raio_explosao, pos_ajustada.y - self.cfg.raio_explosao))

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()
        
        if not self.explodiu and agora - self.tempo_criacao >= self.cfg.duracao:
            self.explodiu = True
            self.tempo_criacao = agora 
            
            # --- Lógica de Dano em Área (AoE) ---
            alvos = entity_manager.inimigos_grupo.sprites() if self.dono == 'PLAYER' else [entity_manager.player]

            for alvo in alvos:
                distancia = (alvo.posicao - self.posicao).length()
                if distancia <= self.cfg.raio_explosao:
                    # Aplica o dano se o alvo estiver na área
                    if hasattr(alvo, 'tomar_dano_direto'):
                        alvo.tomar_dano_direto(self.cfg.dano)
                    elif hasattr(alvo, 'receber_dano'):
                        alvo.receber_dano(self.cfg.dano)
                
        elif self.explodiu and agora - self.tempo_criacao >= 150:
            self.kill()