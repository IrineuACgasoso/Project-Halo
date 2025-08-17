import pygame
import random
from settings import *
from weapon import Arma, Arma_Loop, ArmaLista, Dicionario_Divino, ArmaByte

MAX_ARMAS = 6
TODAS_AS_ARMAS = {
    "Bola Calderânica": Arma_Loop,
    "Ciclo de Lâminas": ArmaLista,
    "Dicionário Divino": Dicionario_Divino,
    "Cão Byte": ArmaByte,
}

class TelaDeUpgrade:
    def __init__(self, tela, jogador, game):
        self.tela = tela
        self.jogador = jogador
        self.game = game

        self.fonte_grande = pygame.font.Font(None, 20)
        self.fonte_pequena = pygame.font.Font(None, 15)

        self.opcao_selecionada = 0
        

        #cálculo do layout
        largura_painel, altura_painel = 800, 350
        self.painel_rect = pygame.Rect((largura_tela - largura_painel) // 2, (altura_tela - altura_painel) // 2, largura_painel, altura_painel)
        
        self.opcoes = []
        padding = 20
        largura_opcao = (self.painel_rect.width - padding * 4) // 3
        altura_opcao = self.painel_rect.height - padding * 3 - 50 # Espaço para título


        self.nomes_das_opcoes = self.gerar_opcoes_aleatorias() 
        self.opcoes_de_armas_obj = []

        #card de cada arma
        for i, nome_arma in enumerate(self.nomes_das_opcoes):
            arma_para_exibir = None
            
            if nome_arma in self.jogador.armas:
                arma_para_exibir = self.jogador.armas[nome_arma]
            
            else:
                classe_arma = TODAS_AS_ARMAS[nome_arma]
                grupos = ()

                if classe_arma == Arma_Loop:
                    grupos = (self.game.all_sprites, self.game.projeteis_grupo, self.game.inimigos_grupo)
                
                elif classe_arma == ArmaLista:
                    grupos = (self.game.all_sprites, self.game.projeteis_grupo)
                
                elif classe_arma == Dicionario_Divino:
                    grupos = (self.game.all_sprites, self.game.auras_grupo)
                
                elif classe_arma == ArmaByte:
                    grupos = (self.game.all_sprites, self.game.inimigos_grupo, self.game.item_group)


                arma_para_exibir = classe_arma(self.jogador, grupos, self.game)
            
            self.opcoes_de_armas_obj.append(arma_para_exibir)

            # O resto da criação dos cards continua igual
            posicao_x = self.painel_rect.x + padding + i * (largura_opcao + padding)
            posicao_y = self.painel_rect.y + padding + 50
            retangulo_opcao = pygame.Rect(posicao_x, posicao_y, largura_opcao, altura_opcao)
            self.opcoes.append(OpcaoDeUpgrade(arma_para_exibir, retangulo_opcao))

    def gerar_opcoes_aleatorias(self):
        pool_de_nomes = []
        armas_do_jogador = list(self.jogador.armas.values())

        for arma in armas_do_jogador:
            pool_de_nomes.append(arma.nome)

        #armas novas
        if len(self.jogador.armas) < MAX_ARMAS:
            nomes_armas_possuidas = {arma.nome for arma in armas_do_jogador}
            for nome_arma in TODAS_AS_ARMAS.keys():
                if nome_arma not in nomes_armas_possuidas:
                    pool_de_nomes.append(nome_arma)
                    

        num_opcoes = min(3, len(pool_de_nomes))
        return random.sample(pool_de_nomes, num_opcoes) if num_opcoes > 0 else []


    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:
                self.opcao_selecionada = (self.opcao_selecionada + 1) % len(self.opcoes)
            elif event.key == pygame.K_a:
                self.opcao_selecionada = (self.opcao_selecionada - 1) % len(self.opcoes)
            elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                return self.opcao_selecionada #retorna o índice da escolha
        
        return None

    def draw(self, surface):
        #escurece o fundo
        overlay = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        #desenha o painel principal
        pygame.draw.rect(surface, (30, 30, 40), self.painel_rect, border_radius=10)
        pygame.draw.rect(surface, (90, 90, 100), self.painel_rect, 3, border_radius=10)
        desenhar_texto(surface, "LEVEL UP!", (self.painel_rect.x + 20, self.painel_rect.y + 15), self.fonte_grande)

        #,anda cada card de opção se desenhar
        for i, opcao in enumerate(self.opcoes):
            esta_selecionada = (i == self.opcao_selecionada)
            opcao.draw(surface, esta_selecionada)

class OpcaoDeUpgrade:
    def __init__(self, arma_prototipo, retangulo):
        self.arma = arma_prototipo
        self.rect = retangulo
        self.fonte_grande = pygame.font.Font(None, 24)
        self.fonte_pequena = pygame.font.Font(None, 20)


    def draw(self, surface, esta_selecionada):
        #desenha o fundo do card
        pygame.draw.rect(surface, (45, 45, 60), self.rect, border_radius=8)

        #desenha a borda de destaque
        cor_borda = (220, 200, 60) if esta_selecionada else (120, 120, 130)
        pygame.draw.rect(surface, cor_borda, self.rect, 3, border_radius=8)

        #exibe o nome e o nível da arma
        nome_arma = self.arma.nome
        nivel_atual = self.arma.nivel

        stats_futuros = self.arma.ver_proximo_upgrade()

        arma_ja_existe_no_inventario = nome_arma in self.arma.jogador.armas
        if arma_ja_existe_no_inventario:
            titulo = f"{nome_arma} - Nv. {nivel_atual} -> {stats_futuros['nivel']}"
        else:
            titulo = f"{nome_arma} - NOVA!"

        desenhar_texto(surface, titulo, (self.rect.x + 10, self.rect.y + 10), self.fonte_grande)

        descricao = self.arma.descricao
        desenhar_texto(surface, descricao, (self.rect.x + 10, self.rect.y + 40), self.fonte_pequena)

        #pega estatisticas da arma agora e futura
        lista_stats_formatada = self.arma.get_estatisticas_para_exibir()

        posicao_y_stats = self.rect.y + 80
        if arma_ja_existe_no_inventario:
            for texto_stat in lista_stats_formatada:
                desenhar_texto(surface, texto_stat, (self.rect.x + 10, posicao_y_stats), self.fonte_pequena)
                posicao_y_stats += 25 

def desenhar_texto(surface, texto, pos, fonte, cor='white'):
    """Função auxiliar para desenhar texto na tela."""
    text_surface = fonte.render(str(texto), True, cor)
    surface.blit(text_surface, pos)
