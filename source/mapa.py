import pygame
import pytmx
from os.path import join
from settings import *

class Mapa:
    def __init__(self, all_sprites=None):
        self.all_sprites = all_sprites
        self.tmx_data = pytmx.load_pygame(join('assets', 'map', 'mapa_cin.tmx'))
        self.tilewidth = self.tmx_data.tilewidth
        self.tileheight = self.tmx_data.tileheight
        self.mapa_largura = self.tmx_data.width
        self.mapa_altura = self.tmx_data.height

        # Tamanho total do mapa em pixels
        self.largura_mapa_pixels = self.mapa_largura * self.tilewidth
        self.altura_mapa_pixels = self.mapa_altura * self.tileheight

    def draw(self, surface, camera_pos):
        largura_tela, altura_tela = surface.get_size()
        tiles_x = largura_tela // self.tilewidth + 2
        tiles_y = altura_tela // self.tileheight + 2

        start_x = int(camera_pos[0]) // self.tilewidth
        start_y = int(camera_pos[1]) // self.tileheight

        offset_x = int(camera_pos[0]) % self.tilewidth
        offset_y = int(camera_pos[1]) % self.tileheight

        for y in range(tiles_y):
            for x in range(tiles_x):
                for layer in self.tmx_data.visible_layers:
                    if isinstance(layer, pytmx.TiledTileLayer):
                        # Corrigido: módulo no tamanho do layer e acesso correto [linha][coluna]
                        map_x = (start_x + x) % layer.width
                        map_y = (start_y + y) % layer.height

                        # pytmx usa layer.data[linha][coluna] → [y][x]
                        gid = layer.data[map_y][map_x]
                        tile_image = self.tmx_data.get_tile_image_by_gid(gid)
                        if tile_image:
                            surface.blit(
                                tile_image,
                                (x * self.tilewidth - offset_x,
                                 y * self.tileheight - offset_y)
                            )

    def get_camera_offset(self, player_pos, screen_size):
        largura_tela, altura_tela = screen_size
        offset_x = player_pos.x - largura_tela / 2
        offset_y = player_pos.y - altura_tela / 2
        return (offset_x, offset_y)
