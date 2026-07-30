import pygame

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
    pygame.draw.rect(surface, (20, 25, 30), painel_rect, border_radius=10)
    pygame.draw.rect(surface, (90, 90, 100), painel_rect, 3, border_radius=10)

    titulo = "NOVO UPGRADE!" if tela_upgrade.modo_unico else "LEVEL UP!"
    desenhar_texto(surface, titulo, (painel_rect.x + 20, painel_rect.y + 15), tela_upgrade.fonte_grande)

    for i, opcao in enumerate(tela_upgrade.opcoes):
        esta_selecionada = (i == tela_upgrade.opcao_selecionada)
        draw_opcao(surface, opcao, esta_selecionada)


def draw_opcao(surface, opcao, esta_selecionada):
    COR_FUNDO = (15, 20, 30)
    COR_BORDA = (0, 150, 255)
    COR_SELECAO = (255, 200, 0)

    if esta_selecionada:
        pygame.draw.rect(surface, (25, 35, 50), opcao.rect, border_radius=10)
        cor_borda_atual = COR_SELECAO
        espessura = 4
    else:
        pygame.draw.rect(surface, COR_FUNDO, opcao.rect, border_radius=10)
        cor_borda_atual = COR_BORDA
        espessura = 2

    pygame.draw.rect(surface, cor_borda_atual, opcao.rect, espessura, border_radius=10)

    arma_adquirida = opcao.jogador.armas.get(opcao.id)

    if arma_adquirida:
        texto_titulo = f"{opcao.dados.nome} (Nv. {arma_adquirida.nivel + 1})"
        cor_titulo = (50, 255, 150)
    else:
        texto_titulo = f"{opcao.dados.nome} (NOVA!)"
        cor_titulo = (255, 255, 255)

    desenhar_texto(surface, texto_titulo, (opcao.rect.x + 15, opcao.rect.y + 15), opcao.fonte_titulo, cor_titulo)

    desenhar_texto_com_quebra(
        surface, opcao.dados.descricao,
        (opcao.rect.x + 15, opcao.rect.y + 55),
        opcao.rect.width - 30, opcao.fonte_texto, (200, 210, 220)
    )

    if arma_adquirida:
        pos_y = opcao.rect.y + 130
        for s in arma_adquirida.get_estatisticas_para_exibir():
            desenhar_texto(surface, f"> {s}", (opcao.rect.x + 15, pos_y), opcao.fonte_texto, (0, 200, 255))
            pos_y += 22