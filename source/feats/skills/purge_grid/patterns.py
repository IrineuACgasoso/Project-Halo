# source/feats/skills/purge_grid/patterns.py
import pygame
import math

def generate_grid_pattern(player_pos, modo, direcao_inicio, artilharias_por_eixo, espacamento, qtd_eixos, raio_artilharia, intervalo, agora):
    fila = []
    modos_para_processar = []
    
    # Se for grid, faremos varredura nos dois eixos (cruzamento)
    if modo in ('eixo_x', 'grid'):
        modos_para_processar.append('x')
    if modo in ('eixo_y', 'grid'):
        modos_para_processar.append('y')

    for _ in modos_para_processar:
        direcao = direcao_inicio.lower()
        
        # A MÁGICA ESTÁ AQUI: Baseamos tudo na bússola, ignorando o nome do eixo
        if direcao in ('north', 'south'):
            # Ataque superior/inferior: Move no eixo Y (Vertical)
            dir_avanco = pygame.math.Vector2(0, 1) if direcao == 'north' else pygame.math.Vector2(0, -1)
            dir_perpendicular = pygame.math.Vector2(1, 0) # Desenha a parede na horizontal
        else:
            # Ataque lateral (west/east): Move no eixo X (Horizontal)
            dir_avanco = pygame.math.Vector2(1, 0) if direcao == 'west' else pygame.math.Vector2(-1, 0)
            dir_perpendicular = pygame.math.Vector2(0, 1) # Desenha a parede na vertical

        # Se for o modo Grid (que ataca nas duas direções), invertemos a bússola para o segundo passe
        if modo == 'grid':
            direcao_inicio = 'west' if direcao in ('north', 'south') else 'north'

        distancia_inicial = 800 
        ponto_inicial = player_pos - dir_avanco * distancia_inicial

        for i in range(artilharias_por_eixo):
            pos_onda = ponto_inicial + dir_avanco * (i * espacamento)
            for j in range(qtd_eixos):
                offset_perpendicular = (j - (qtd_eixos - 1) / 2) * (raio_artilharia * 2)
                pos_artilharia = pos_onda + dir_perpendicular * offset_perpendicular
                
                tempo_spawn = agora + (i * intervalo)
                fila.append((tempo_spawn, pos_artilharia))
                
    return fila


def generate_radial_pattern(caster_pos, qtd_eixos, artilharias_por_eixo, espacamento, direcao, intervalo, agora, offset_angulo=0.0):
    fila = []
    for j in range(qtd_eixos):
        angulo = j * (2 * math.pi / qtd_eixos) + offset_angulo
        vetor_direcao = pygame.math.Vector2(math.cos(angulo), math.sin(angulo))

        for i in range(artilharias_por_eixo):
            distancia = (i + 1) * espacamento if direcao == 'exit' else (artilharias_por_eixo - i) * espacamento
            pos_artilharia = caster_pos + vetor_direcao * distancia
            
            tempo_spawn = agora + (i * intervalo) + (j * 25)
            fila.append((tempo_spawn, pos_artilharia))
    return fila


def generate_directional_pattern(caster_pos, player_pos, artilharias_por_eixo, espacamento, intervalo, agora):
    fila = []
    vetor_alvo = player_pos - caster_pos
    dir_alvo = vetor_alvo.normalize() if vetor_alvo.length() > 0 else pygame.math.Vector2(0, 1)

    for i in range(artilharias_por_eixo):
        pos_artilharia = caster_pos + dir_alvo * (i * espacamento)
        tempo_spawn = agora + (i * intervalo)
        fila.append((tempo_spawn, pos_artilharia))
    return fila