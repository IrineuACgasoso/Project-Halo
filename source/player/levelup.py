import pygame
import random
from source.windows.settings import *
from source.player.weapons import *
from source.feats.buddies import *


MAX_ARMAS = 6

# Metadados: Nome -> {Classe, Descrição, Ícone (opcional)}
DADOS_ARMAS = {
    "Rifle de Assalto": {
        "classe": RifleAssalto,
        "grupos": ["all_sprites", "projeteis_jogador_grupo", "inimigos_grupo"],
        "descricao": "Rifle padrão do UNSC de cadência elevada.",
    },
    "Bola Calderânica": {
        "classe": Arma_Loop,
        "grupos": ["all_sprites", "projeteis_jogador_grupo", "inimigos_grupo"],
        "descricao": "Uma esfera de energia que orbita o jogador.",
    },
    "Ciclo de Lâminas": {
        "classe": ArmaLista,
        "descricao": "Lâminas giratórias que cortam inimigos próximos.",
    },
    # TERMINE OS GRUPOS
    "Dicionário Divino": {
        "classe": Dicionario_Divino,
        "grupos": ["all_sprites", "auras_grupo", "inimigos_grupo"],
        "descricao": "Palavras sagradas que criam uma aura de proteção.",
    },
    "Árbitro": {
        "classe": Arbitro,
        "grupos": ["all_sprites", "inimigos_grupo", "items_grupo"],
        "descricao": "Um elite aliado que caça inimigos próximos.",
    },
    "Cortana": {
        "classe": Cortana,
        "grupos": ["all_sprites", "inimigos_grupo", "items_grupo"],
        "descricao": "Busca itens e XP próximos a você.",
    },
    "UNSC Marine": {
        "classe": Marine,
        "grupos": ["all_sprites", "inimigos_grupo", "items_grupo"],
        "descricao": "Leal soldado que auxilia coletando itens e atacando inimigos.",
    },
    "Needler": {
        "classe": Needler,
        "grupos": ["all_sprites", "projeteis_jogador_grupo", "inimigos_grupo"],
        "descricao": "Dispara agulhas teleguiadas que explodem ao acumular."
    }
}


class TelaDeUpgrade:
    def __init__(self, tela, jogador, game):
        self.tela = tela
        self.jogador = jogador
        self.game = game
        self.opcao_selecionada = 0

        # Fontes maiores para melhor leitura
        self.fonte_grande = pygame.font.Font(None, 20)
        self.fonte_pequena = pygame.font.Font(None, 15)

        # Cálculo do layout
        largura_painel, altura_painel = 850, 400
        self.painel_rect = pygame.Rect((largura_tela - largura_painel) // 2, (altura_tela - altura_painel) // 2, largura_painel, altura_painel)
        
        self.nomes_das_opcoes = self.gerar_opcoes_aleatorias() 
        self.opcoes = []

        padding = 20
        largura_opcao = (self.painel_rect.width - padding * 4) // 3
        altura_opcao = self.painel_rect.height - padding * 3 - 50 # Espaço para título

        # Criação dos cards
        for i, nome_arma in enumerate(self.nomes_das_opcoes):
            pos_x = self.painel_rect.x + padding + i * (largura_opcao + padding)
            pos_y = self.painel_rect.y + 70
            rect = pygame.Rect(pos_x, pos_y, largura_opcao, altura_opcao)
            
            # Passamos o NOME da arma, não o OBJETO instanciado
            self.opcoes.append(OpcaoDeUpgrade(nome_arma, rect, self.jogador))


    def gerar_opcoes_aleatorias(self):
        opcoes_de_upgrade = []
        opcoes_de_armas_novas = []

        # 1. Popula as opções de upgrade com as armas que o jogador já possui
        for arma_obj in self.jogador.armas.values():
            opcoes_de_upgrade.append(arma_obj.nome)

        # 2. Popula as opções de novas armas com as que o jogador AINDA NÃO possui
        if len(self.jogador.armas) < MAX_ARMAS:
            nomes_armas_possuidas = {arma.nome for arma in self.jogador.armas.values()}
            for nome_arma_total in DADOS_ARMAS.keys():
                if nome_arma_total not in nomes_armas_possuidas:
                    opcoes_de_armas_novas.append(nome_arma_total)

        # 3. Combina e seleciona as 3 opções finais
        pool_de_nomes = []
        
        # Adiciona aleatoriamente opções de upgrade primeiro (se houver)
        num_upgrades = min(2, len(opcoes_de_upgrade)) # Prioriza 2 upgrades
        if len(opcoes_de_armas_novas) > 0: # Se houver novas armas, deixa uma vaga
            num_upgrades = min(3, len(opcoes_de_upgrade))
        
        # Pega um subconjunto de upgrades aleatórios
        nomes_para_upgrade = random.sample(opcoes_de_upgrade, num_upgrades)
        pool_de_nomes.extend(nomes_para_upgrade)
        
        # Preenche o resto com novas armas, se houver
        while len(pool_de_nomes) < 3 and len(opcoes_de_armas_novas) > 0:
            nova_arma_escolhida = random.choice(opcoes_de_armas_novas)
            pool_de_nomes.append(nova_arma_escolhida)
            opcoes_de_armas_novas.remove(nova_arma_escolhida) # Remove para não pegar duas vezes
            
        return pool_de_nomes

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:
                self.opcao_selecionada = (self.opcao_selecionada + 1) % len(self.opcoes)
            elif event.key == pygame.K_a:
                self.opcao_selecionada = (self.opcao_selecionada - 1) % len(self.opcoes)
            elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                return self.opcao_selecionada # Retorna o índice da escolha
        
        return None

    def draw(self, surface):
        # Fade-Out leve no fundo
        overlay = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Painel Principal
        pygame.draw.rect(surface, (20, 25, 30), self.painel_rect, border_radius=10)
        pygame.draw.rect(surface, (90, 90, 100), self.painel_rect, 3, border_radius=10)
        desenhar_texto(surface, "LEVEL UP!", (self.painel_rect.x + 20, self.painel_rect.y + 15), self.fonte_grande)

        # Desenha a borda de seleção da escolha atual
        for i, opcao in enumerate(self.opcoes):
            esta_selecionada = (i == self.opcao_selecionada)
            opcao.draw(surface, esta_selecionada)

class OpcaoDeUpgrade:
    def __init__(self, nome_arma, retangulo, jogador):
        self.nome = nome_arma
        self.rect = retangulo
        self.jogador = jogador
        self.dados = DADOS_ARMAS[nome_arma] # Busca metadados estáticos

        self.fonte_titulo = pygame.font.Font(None, 26)
        self.fonte_texto = pygame.font.Font(None, 20)


    def draw(self, surface, esta_selecionada):
        # CORES TEMÁTICAS
        COR_FUNDO = (15, 20, 30)       
        COR_BORDA = (0, 150, 255)   
        COR_SELECAO = (255, 200, 0)    
        
        if esta_selecionada:
            pygame.draw.rect(surface, (25, 35, 50), self.rect, border_radius=10) # Fundo levemente mais claro
            cor_borda_atual = COR_SELECAO
            espessura = 4
        else:
            pygame.draw.rect(surface, COR_FUNDO, self.rect, border_radius=10)
            cor_borda_atual = COR_BORDA
            espessura = 2

        # Borda externa
        pygame.draw.rect(surface, cor_borda_atual, self.rect, espessura, border_radius=10)

        # Título e nível
        arma_adquirida = self.jogador.armas.get(self.nome)
        if arma_adquirida:
            texto_titulo = f"{self.nome} (Nv. {arma_adquirida.nivel})"
            cor_titulo = (50, 255, 150) # Roxo para upgrade
        else:
            texto_titulo = f"{self.nome} (NOVA!)"
            cor_titulo = (255, 255, 255)

        desenhar_texto(surface, texto_titulo, (self.rect.x + 15, self.rect.y + 15), self.fonte_titulo, cor_titulo)

        # Descrição com Quebra de Linha
        desenhar_texto_com_quebra(
            surface, 
            self.dados["descricao"], 
            (self.rect.x + 15, self.rect.y + 55), 
            self.rect.width - 30, 
            self.fonte_texto, 
            (200, 210, 220)
        )

        # Stats (Só mostra se a arma já existir)
        if arma_adquirida:
            pos_y = self.rect.y + 120
            stats = arma_adquirida.get_estatisticas_para_exibir()
            for s in stats:
                # # Exibir o > entre stats
                texto_stat = f"> {s}"
                desenhar_texto(surface, texto_stat, (self.rect.x + 10, pos_y), self.fonte_texto, (0, 200, 255))
                pos_y += 22

def desenhar_texto(surface, texto, pos, fonte, cor='white'):
    """Função auxiliar para desenhar texto na tela."""
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
        y += fonte.get_linesize() # Pula para a linha de baixo

