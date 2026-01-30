import pygame
from os.path import join
import json

class Mapa:
    def __init__(self, caminho_json, all_sprites=None):
        self.all_sprites = all_sprites
        
        # 1. Carrega a Imagem Única do Cenário
        self.background = pygame.image.load(join('assets', 'map', 'map1.jpg')).convert()
        self.rect_background = self.background.get_rect(topleft=(0,0))
        
        self.largura_mapa_pixels = self.rect_background.width
        self.altura_mapa_pixels = self.rect_background.height

        # 2. Carrega as colisões
        self.paredes = []

        # 3. Carrega Pontos de Spawn e Loot
        self.pontos_de_spawn = [] 

        self.carregar_json(caminho_json)


    def get_camera_offset(self, player_pos, screen_size):
        largura_tela, altura_tela = screen_size
        # Centraliza no player
        offset_x = player_pos.x - largura_tela / 2
        offset_y = player_pos.y - altura_tela / 2
        
        # Trava a câmera nas bordas do mapa
        offset_x = max(0, min(offset_x, self.largura_mapa_pixels - largura_tela))
        offset_y = max(0, min(offset_y, self.altura_mapa_pixels - altura_tela))
        
        return pygame.math.Vector2(offset_x, offset_y)

    def carregar_json(self, caminho):
        with open(caminho, 'r') as f:
            dados = json.load(f)

        for camada in dados['layers']:
            # Verifique se o nome da camada no Tiled é exatamente 'Colisoes'
            if camada['type'] == 'objectgroup' and camada['name'] == 'Colisoes':
                for obj in camada['objects']:
                    base_x = obj['x']
                    base_y = obj['y']

                    # CASO A: Polilinhas ou Polígonos
                    # No JSON, polilinhas usam a chave 'polyline' e polígonos 'polygon'
                    if 'polyline' in obj or 'polygon' in obj:
                        pontos_relativos = obj.get('polyline') or obj.get('polygon')
                        pontos = [pygame.math.Vector2(p['x'] + base_x, p['y'] + base_y) for p in pontos_relativos]
                        
                        # Se for polígono, fechamos a forma conectando o último ponto ao primeiro
                        if 'polygon' in obj:
                            pontos.append(pontos[0])
                            
                        self.paredes.append({'tipo': 'linha', 'pontos': pontos})

                    # CASO B: Retângulos normais
                    # Convertemos retângulos em uma polinha fechada de 4 segmentos
                    else:
                        w = obj['width']
                        h = obj['height']
                        pontos = [
                            pygame.math.Vector2(base_x, base_y),         # Topo-Esquerda
                            pygame.math.Vector2(base_x + w, base_y),     # Topo-Direita
                            pygame.math.Vector2(base_x + w, base_y + h), # Baixo-Direita
                            pygame.math.Vector2(base_x, base_y + h),     # Baixo-Esquerda
                            pygame.math.Vector2(base_x, base_y)          # Fecha no Topo-Esquerda
                        ]
                        self.paredes.append({'tipo': 'linha', 'pontos': pontos})
            
            elif camada['type'] == 'objectgroup' and camada['name'] == 'SpawnPoints':
                for obj in camada['objects']:
                    # Captura a posição X e Y do objeto Ponto ou Retângulo
                    pos_x = obj['x']
                    pos_y = obj['y']
                    
                    # Se for um retângulo, vamos pegar o centro dele para o spawn
                    if 'width' in obj and 'height' in obj and not obj.get('point'):
                        pos_x += obj['width'] / 2
                        pos_y += obj['height'] / 2
                    
                    self.pontos_de_spawn.append(pygame.math.Vector2(pos_x, pos_y))

    def get_paredes_proximas(self, entidade_pos, raio=1000):
        paredes_proximas = []
        for p_dict in self.paredes:
            # Criamos um retângulo que envolve toda a polilinha (Bounding Box)
            pontos = p_dict['pontos']
            min_x = min(p.x for p in pontos)
            max_x = max(p.x for p in pontos)
            min_y = min(p.y for p in pontos)
            max_y = max(p.y for p in pontos)
            
            # Criamos um Rect temporário para facilitar a checagem
            rect_da_parede = pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
            
            # Inflamos o rect para o filtro ser "generoso"
            rect_da_parede.inflate_ip(raio, raio)

            if rect_da_parede.collidepoint(entidade_pos):
                paredes_proximas.append(p_dict)
                
        return paredes_proximas

    def draw(self, surface, camera_pos):
        area_visivel = pygame.Rect(camera_pos.x, camera_pos.y, surface.get_width(), surface.get_height())
        area_visivel = area_visivel.clip(self.rect_background)
        if area_visivel.width > 0 and area_visivel.height > 0:
            sub_imagem = self.background.subsurface(area_visivel)
            surface.blit(sub_imagem, (0, 0))

    # Função extra para você testar se as linhas e pontos estão no lugar certo
    def draw_debug(self, surface, camera_offset):
        for p in self.paredes:
            pts = [p_vec - camera_offset for p_vec in p['pontos']]
            if len(pts) > 1:
                pygame.draw.lines(surface, "green", False, pts, 2)

        for sp in self.pontos_de_spawn:
            pos_tela = sp - camera_offset
            pygame.draw.circle(surface, "red", (int(pos_tela.x), int(pos_tela.y)), 5)