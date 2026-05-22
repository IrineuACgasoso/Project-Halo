import pygame
import json


class MapLoader:
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
    