import pygame

from source.feats.assets import *
from .map_loader import MapLoader
from .map_collision import MapCollision
from .map_utils import MapUtils
from .map_feats import MapFeats

class Mapa(
    MapLoader,
    MapCollision,
    MapUtils,
    MapFeats,
):
    def __init__(self, caminho_json, fase_atual, all_sprites=None):
        self.all_sprites = all_sprites
        
        # 1. Carrega a Imagem Única do Cenário
        self.background = ASSETS['maps'][f'{fase_atual}']
        self.rect_background = self.background.get_rect(topleft=(0,0))
        
        self.largura_mapa_pixels = self.rect_background.width
        self.altura_mapa_pixels = self.rect_background.height

        # 2. Estruturas de Dados
        self.paredes = []
        self.zonas_void = [] 
        self.void_points = []
        self.navigation_zones = []

        # 3. Carrega Pontos de Spawn e Loot
        self.portal_pos = pygame.math.Vector2(
            self.largura_mapa_pixels / 2, 
            self.altura_mapa_pixels / 2
        )
        self.player_spawn_manual = None
        self.pontos_de_spawn = [] 

        self.carregar_json(caminho_json)

    def get_player_spawn_pos(self):
        """Retorna o ponto manual se existir, senão retorna o centro do mapa."""
        if self.player_spawn_manual:
            return self.player_spawn_manual
        return pygame.math.Vector2(self.largura_mapa_pixels / 2, self.altura_mapa_pixels / 2)

    def draw(self, surface, camera_pos):
        area_visivel = pygame.Rect(camera_pos.x, camera_pos.y, surface.get_width(), surface.get_height())
        area_visivel = area_visivel.clip(self.rect_background)
        if area_visivel.width > 0 and area_visivel.height > 0:
            sub_imagem = self.background.subsurface(area_visivel)
            surface.blit(sub_imagem, (0, 0))

    