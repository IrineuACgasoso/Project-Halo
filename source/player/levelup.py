import pygame
import random
from source.windows.settings import *
from source.player.weapons import *
from source.feats.buddies import *

MAX_ARMAS = 6

DADOS_ARMAS = {
    "rifle_assalto": {
        "nome": "Rifle de Assalto",
        "classe": RifleAssalto,
        "grupos": ["all_sprites", "projeteis_jogador_grupo", "inimigos_grupo"],
        "descricao": "Rifle padrão do UNSC de cadência elevada.",
    },
    "bola_calderanica": {
        "nome": "Bola Calderânica",
        "classe": Arma_Loop,
        "grupos": ["all_sprites", "projeteis_jogador_grupo", "inimigos_grupo"],
        "descricao": "Uma esfera de energia que orbita o jogador.",
    },
    "ciclo_de_laminas": {
        "nome": "Ciclo de Lâminas",
        "classe": ArmaLista,
        "grupos": ["all_sprites", "projeteis_jogador_grupo", "inimigos_grupo"],
        "descricao": "Lâminas giratórias que cortam inimigos próximos.",
    },
    "mk2_shield": {
        "nome": "Escudo MK-2",
        "classe": MK2_Shield,
        "grupos": ["all_sprites", "auras_grupo", "inimigos_grupo"],
        "descricao": "Gera um escudo e causa dano por segundo ao redor do jogador.",
    },
    "arbiter": {
        "nome": "Árbitro",
        "classe": Arbitro,
        "grupos": ["all_sprites", "inimigos_grupo", "items_grupo"],
        "descricao": "Um elite aliado que caça inimigos próximos.",
    },
    "cortana": {
        "nome": "Cortana",
        "classe": Cortana,
        "grupos": ["all_sprites", "inimigos_grupo", "items_grupo"],
        "descricao": "Busca itens e XP próximos a você.",
    },
    "marine": {
        "nome": "UNSC Marine",
        "classe": Marine,
        "grupos": ["all_sprites", "inimigos_grupo", "items_grupo"],
        "descricao": "Leal soldado que auxilia coletando itens e atacando inimigos.",
    },
    "needler": {
        "nome": "Needler",
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

        self.fonte_grande = pygame.font.Font(None, 32) # Aumentado de 20 para 32 (20 fica ilegível em resoluções normais)
        self.fonte_pequena = pygame.font.Font(None, 18)

        largura_painel, altura_painel = 850, 400
        self.painel_rect = pygame.Rect((largura_tela - largura_painel) // 2, (altura_tela - altura_painel) // 2, largura_painel, altura_painel)
        
        # Agora retorna uma lista de IDs (ex: ['rifle_assalto', 'arbiter'])
        self.ids_das_opcoes = self.gerar_opcoes_aleatorias() 
        self.opcoes = []

        padding = 20
        largura_opcao = (self.painel_rect.width - padding * 4) // 3
        altura_opcao = self.painel_rect.height - padding * 3 - 50

        for i, id_arma in enumerate(self.ids_das_opcoes):
            pos_x = self.painel_rect.x + padding + i * (largura_opcao + padding)
            pos_y = self.painel_rect.y + 70
            rect = pygame.Rect(pos_x, pos_y, largura_opcao, altura_opcao)
            
            self.opcoes.append(OpcaoDeUpgrade(id_arma, rect, self.jogador))

    def gerar_opcoes_aleatorias(self):
        # Puxa os IDs das armas que o jogador já possui
        opcoes_upgrade = list(self.jogador.armas.keys())
        
        opcoes_novas = []
        if len(self.jogador.armas) < MAX_ARMAS:
            for id_total in DADOS_ARMAS.keys():
                if id_total not in self.jogador.armas:
                    opcoes_novas.append(id_total)

        pool_final = []

        # 1. Tenta pegar até 2 upgrades para priorizar a evolução do kit atual
        upgrades_escolhidos = random.sample(opcoes_upgrade, min(2, len(opcoes_upgrade)))
        pool_final.extend(upgrades_escolhidos)

        # 2. Preenche o restante das vagas disponíveis (almejando 3) com armas novas
        vagas_restantes = 3 - len(pool_final)
        novas_escolhidas = random.sample(opcoes_novas, min(vagas_restantes, len(opcoes_novas)))
        pool_final.extend(novas_escolhidas)

        # 3. Se ainda sobrarem vagas (ex: não há novas armas disponíveis), 
        # preenche com os upgrades que restaram na reserva
        vagas_restantes = 3 - len(pool_final)
        if vagas_restantes > 0:
            upgrades_restantes = [u for u in opcoes_upgrade if u not in pool_final]
            mais_upgrades = random.sample(upgrades_restantes, min(vagas_restantes, len(upgrades_restantes)))
            pool_final.extend(mais_upgrades)

        return pool_final

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:
                self.opcao_selecionada = (self.opcao_selecionada + 1) % len(self.opcoes)
            elif event.key == pygame.K_a:
                self.opcao_selecionada = (self.opcao_selecionada - 1) % len(self.opcoes)
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                # Importante: Retorna o ID da arma escolhida, não apenas o índice numérico!
                return self.ids_das_opcoes[self.opcao_selecionada]
        return None

    def draw(self, surface):
        overlay = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, (20, 25, 30), self.painel_rect, border_radius=10)
        pygame.draw.rect(surface, (90, 90, 100), self.painel_rect, 3, border_radius=10)
        desenhar_texto(surface, "LEVEL UP!", (self.painel_rect.x + 20, self.painel_rect.y + 15), self.fonte_grande)

        for i, opcao in enumerate(self.opcoes):
            esta_selecionada = (i == self.opcao_selecionada)
            opcao.draw(surface, esta_selecionada)


class OpcaoDeUpgrade:
    def __init__(self, id_arma, retangulo, jogador):
        self.id = id_arma
        self.rect = retangulo
        self.jogador = jogador
        self.dados = DADOS_ARMAS[id_arma]

        self.fonte_titulo = pygame.font.Font(None, 24)
        self.fonte_texto = pygame.font.Font(None, 18)

    def draw(self, surface, esta_selecionada):
        COR_FUNDO = (15, 20, 30)       
        COR_BORDA = (0, 150, 255)   
        COR_SELECAO = (255, 200, 0)    
        
        if esta_selecionada:
            pygame.draw.rect(surface, (25, 35, 50), self.rect, border_radius=10)
            cor_borda_atual = COR_SELECAO
            espessura = 4
        else:
            pygame.draw.rect(surface, COR_FUNDO, self.rect, border_radius=10)
            cor_borda_atual = COR_BORDA
            espessura = 2

        pygame.draw.rect(surface, cor_borda_atual, self.rect, espessura, border_radius=10)

        # Busca a arma usando o ID estável
        arma_adquirida = self.jogador.armas.get(self.id)
        
        if arma_adquirida:
            texto_titulo = f"{self.dados['nome']} (Nv. {arma_adquirida.nivel + 1})" # Mostra o PRÓXIMO nível
            cor_titulo = (50, 255, 150) # Verde claro (comentário dizia roxo, altere a tupla se quiser roxo)
        else:
            texto_titulo = f"{self.dados['nome']} (NOVA!)"
            cor_titulo = (255, 255, 255)

        desenhar_texto(surface, texto_titulo, (self.rect.x + 15, self.rect.y + 15), self.fonte_titulo, cor_titulo)

        # Descrição
        desenhar_texto_com_quebra(
            surface, 
            self.dados["descricao"], 
            (self.rect.x + 15, self.rect.y + 55), 
            self.rect.width - 30, 
            self.fonte_texto, 
            (200, 210, 220)
        )

        # Exibição dos Upgrades matemáticos vindos das Dataclasses
        if arma_adquirida:
            pos_y = self.rect.y + 130
            # Método que criaremos na classe da arma para listar as mudanças em string
            stats = arma_adquirida.get_estatisticas_para_exibir()
            for s in stats:
                desenhar_texto(surface, f"> {s}", (self.rect.x + 15, pos_y), self.fonte_texto, (0, 200, 255))
                pos_y += 22


def desenhar_texto(surface, texto, pos, fonte, cor='white'):
    text_surface = fonte.render(str(texto), True, cor)
    surface.blit(text_surface, pos)

def desenhar_texto_com_quebra(surface, texto, pos, largura_max, fonte, cor='white'):
    palavras = texto.split(' ')
    linhas = []
    linha_atual = ""
    
    for palabra in palavras:
        test_line = linha_atual + palabra + " "
        if fonte.size(test_line)[0] < largura_max:
            box = test_line
            linha_atual = test_line
        else:
            linhas.append(linha_atual)
            linha_atual = palabra + " "
    linhas.append(linha_atual)

    x, y = pos
    for linha in linhas:
        text_surface = fonte.render(linha, True, cor)
        surface.blit(text_surface, (x, y))
        y += fonte.get_linesize()