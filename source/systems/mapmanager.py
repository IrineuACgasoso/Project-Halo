import pygame
from os.path import join
import json
from source.feats.assets import *

class Mapa:
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


    def carregar_json(self, caminho):
        with open(caminho, 'r') as f:
            dados = json.load(f)

        for camada in dados['layers']:

            # PAREDES 

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
            
            # ENEMIE SPAWNS
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
            
            # PLAYER SPAWN

            elif camada['type'] == 'objectgroup' and camada['name'] == 'SpawnPlayer':
                for obj in camada['objects']:
                    pos_x, pos_y = obj['x'], obj['y']
                    # Se for um retângulo/área, centraliza. Se for ponto, usa x,y direto.
                    if 'width' in obj and 'height' in obj and not obj.get('point'):
                        pos_x += obj['width'] / 2
                        pos_y += obj['height'] / 2
                    
                    # Salva apenas o primeiro ponto encontrado como o spawn oficial
                    self.player_spawn_manual = pygame.math.Vector2(pos_x, pos_y)
                    break # Só precisamos de um ponto para o player
            
            # PORTAL

            elif camada['type'] == 'objectgroup' and camada['name'] == 'Portal':
                for obj in camada['objects']:
                    self.portal_pos = pygame.math.Vector2(obj['x'], obj['y'])
                    if 'width' in obj: # Centraliza se for um retângulo
                        self.portal_pos.x += obj['width'] / 2
                        self.portal_pos.y += obj['height'] / 2

            # VOID (Rects de atração)

            elif camada['type'] == 'objectgroup' and camada['name'] == 'Void':
                for obj in camada['objects']:
                    rect = pygame.Rect(obj['x'], obj['y'], obj['width'], obj['height'])
                    self.zonas_void.append(rect)

            # VOID (Pontos de atração)

            elif camada['type'] == 'objectgroup' and camada['name'] == 'VoidPoint':
                for obj in camada['objects']:
                    # Pega o centro do ponto/objeto
                    ponto = pygame.math.Vector2(obj['x'], obj['y'])
                    if 'width' in obj:
                        ponto.x += obj['width'] / 2
                        ponto.y += obj['height'] / 2
                    self.void_points.append(ponto)

            # NAVIGATION

            elif camada['type'] == 'objectgroup' and camada['name'] == 'Navigation':
                for obj in camada['objects']:
                    rect = pygame.Rect(obj['x'], obj['y'], obj['width'], obj['height'])
                    self.navigation_zones.append(rect)
    

    def get_player_spawn_pos(self):
        """Retorna o ponto manual se existir, senão retorna o centro do mapa."""
        if self.player_spawn_manual:
            return self.player_spawn_manual
        return pygame.math.Vector2(self.largura_mapa_pixels / 2, self.altura_mapa_pixels / 2)


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
    
    def caminho_livre(self, ponto_a, ponto_b):
        """Verifica se uma linha entre A e B cruza alguma parede."""
        for p_dict in self.paredes:
            pontos = p_dict['pontos']
            # Checa cada segmento da polilinha
            for i in range(len(pontos) - 1):
                p1 = pontos[i]
                p2 = pontos[i+1]
                # Pygame clipline retorna os pontos de intersecção se houver colisão
                if pygame.draw.line(pygame.Surface((1,1)), (0,0,0), p1, p2, 1).clipline(ponto_a, ponto_b):
                    return False
        return True
    
    def posicao_e_valida(self, pos_vetor):
        """Verifica se uma posição está dentro de alguma área de navegação (chão)."""
        # Se não houver zonas de navegação definidas, aceita qualquer lugar (segurança)
        if not self.navigation_zones:
            return True
        
        for zone in self.navigation_zones:
            if zone.collidepoint(pos_vetor.x, pos_vetor.y):
                return True
        return False
    

    def calcular_puxo_void(self, player_pos):
        for i, zona in enumerate(self.zonas_void):
            if zona.collidepoint(player_pos):
                # Define o alvo (ponto de atração)
                ponto_alvo = self.void_points[i] if i < len(self.void_points) else self.void_points[0]
                
                direcao = (ponto_alvo - player_pos)
                distancia = direcao.length()
                
                if distancia > 0:
                    # Retorna (Vetor de Força, Ponto Alvo, Distância)
                    return direcao.normalize() * 2.5, ponto_alvo, distancia
                    
        # Se não estiver no vácuo, retorna valores nulos
        return pygame.math.Vector2(0, 0), None, 9999

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

        # Zonas de Navegação em Azul (Invisíveis no jogo, visíveis no debug)
        for zone in self.navigation_zones:
            debug_rect = zone.copy()
            debug_rect.x -= camera_offset.x
            debug_rect.y -= camera_offset.y
            pygame.draw.rect(surface, (0, 100, 255), debug_rect, 2)

        for sp in self.pontos_de_spawn:
            pos_tela = sp - camera_offset
            pygame.draw.circle(surface, "red", (int(pos_tela.x), int(pos_tela.y)), 5)