import pygame

from .constants import PALETA_RARIDADE, ARMAS_REGISTRO
from source.windows.settings import largura_tela, altura_tela


def desenhar_texto(surface, texto, pos, fonte, cor='white'):
    text_surface = fonte.render(str(texto), True, cor)
    surface.blit(text_surface, pos)


def desenhar_texto_com_quebra(surface, texto, pos, largura_max, fonte, cor='white'):
    palavras = texto.split(' ')
    linhas = []
    linha_atual = ""

    for palavra in palavras:
        test_line = linha_atual + palavra + " "
        if fonte.size(test_line)[0] < largura_max:
            linha_atual = test_line
        else:
            linhas.append(linha_atual)
            linha_atual = palavra + " "
    linhas.append(linha_atual)

    x, y = pos
    for linha in linhas:
        text_surface = fonte.render(linha, True, cor)
        surface.blit(text_surface, (x, y))
        y += fonte.get_linesize()


def draw_tela_upgrade(surface, tela_upgrade):
    overlay = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    painel_rect = tela_upgrade.painel_rect
    pygame.draw.rect(surface, (0, 5, 20), painel_rect, border_radius=10)
    pygame.draw.rect(surface, (150, 255, 255), painel_rect, 4, border_radius=10)

    titulo = "NOVO UPGRADE!" if tela_upgrade.modo_unico else "LEVEL UP!"
    desenhar_texto(surface, titulo, (painel_rect.centerx - 65, painel_rect.top + 15), tela_upgrade.fonte_grande, cor=(150, 255, 255))

    for i, opcao in enumerate(tela_upgrade.opcoes):
        esta_selecionada = (i == tela_upgrade.opcao_selecionada)
        draw_opcao(surface, opcao, esta_selecionada)


def draw_opcao(surface, opcao, esta_selecionada):
    
    # Coleta as especificações de dados estáticos da arma registrada
    dados_estaticos = ARMAS_REGISTRO.get(opcao.id)
    raridade = dados_estaticos.raridade if dados_estaticos else 'comum'
    cor_fundo = PALETA_RARIDADE[raridade]['fundo']
    cor_borda = PALETA_RARIDADE[raridade]['borda']
    cor_decoracao = PALETA_RARIDADE[raridade]['decoracao']
    COR_SELECAO = (255, 200, 0)
    COR_FUNDO = (0, 5, 30)
    COR_BORDA = (0, 150, 255)

    if esta_selecionada:
        pygame.draw.rect(surface, cor_fundo, opcao.rect, border_radius=15)
        cor_borda_atual = cor_borda
        espessura = 4
    else:
        pygame.draw.rect(surface, COR_FUNDO, opcao.rect, border_radius=12)
        cor_borda_atual = cor_borda
        espessura = 2

    pygame.draw.rect(surface, cor_borda_atual, opcao.rect, espessura, border_radius=10)

    arma_adquirida = opcao.jogador.armas.get(opcao.id)

    if arma_adquirida:
        texto_titulo = f"{opcao.dados.nome} (Nv. {arma_adquirida.nivel + 1})"
        cor_titulo = cor_decoracao
    else:
        texto_titulo = f"{opcao.dados.nome} (NOVA!)"
        cor_titulo = (255, 255, 0)

    corte = 12
    _draw_corner_ornaments(surface, opcao.rect, cor_decoracao, corte)

    desenhar_texto(surface, texto_titulo, (opcao.rect.x + 15, opcao.rect.y + 15), opcao.fonte_titulo, cor_titulo)

    desenhar_texto_com_quebra(
        surface, opcao.dados.descricao,
        (opcao.rect.x + 15, opcao.rect.y + 55),
        opcao.rect.width - 70, opcao.fonte_texto, (200, 210, 220)
    )

    if arma_adquirida:
        pos_y = opcao.rect.y + 130
        for s in arma_adquirida.get_estatisticas_para_exibir():
            desenhar_texto(surface, f"> {s}", (opcao.rect.x + 15, pos_y), opcao.fonte_texto, (0, 200, 255))
            pos_y += 22


def _draw_corner_ornaments(surface, rect, cor, corte):
    """Pequenos losangos/diamantes nos 4 cantos da barra."""
    size_vert = 9
    size_hori = 5
    pontos = [
        (rect.x, rect.centery, size_hori),            # Esquerda
        (rect.right, rect.centery, size_hori),        # Direita
        (rect.centerx, rect.y, size_vert),            # Cima
        (rect.centerx, rect.bottom, size_vert),       # Baixo
        (rect.left, rect.top, size_hori),
        (rect.right, rect.top, size_hori),
        (rect.left, rect.bottom, size_hori),
        (rect.right, rect.bottom, size_hori)
    ]
    for cx, cy, size in pontos:
        pts = [(cx, cy - size), (cx + size, cy), (cx, cy + size), (cx - size, cy)]
        pygame.draw.polygon(surface, cor, pts)
        pygame.draw.polygon(surface, (25, 30, 20), pts, 3)
