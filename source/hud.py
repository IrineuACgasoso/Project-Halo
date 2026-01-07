import pygame
from os.path import join
from settings import *
from player import *

class HUD:
    def __init__(self, game):
        self.game = game
        #seta fonte para o numero da hud
        self.font = pygame.font.Font(None, 36)



        #pega imagem e da scale para ficar menor
        #xp
        self.icone_exp_shard = pygame.image.load(join('assets', 'img', 'expShard.png')).convert_alpha()
        self.icone_exp_shard = pygame.transform.scale(self.icone_exp_shard, (30, 30))
        #big shard
        self.icone_big_shard = pygame.image.load(join('assets', 'img', 'bigShard.png')).convert_alpha()
        self.icone_big_shard = pygame.transform.scale(self.icone_big_shard, (30, 30))
        #life orb
        self.icone_life_orb = pygame.image.load(join('assets', 'img', 'lifeOrb.png')).convert_alpha()
        self.icone_life_orb = pygame.transform.scale(self.icone_life_orb, (30, 30))
        #cafe
        self.icone_cafe = pygame.image.load(join('assets', 'img', 'cafe.png')). convert_alpha()
        self.icone_cafe = pygame.transform.scale(self.icone_cafe, (30, 30))

    def draw_barra_exp(self, tela):
        jogador = self.game.player
        #caracteristicas
        posicao_x = 10
        posicao_y = 5 

        largura_barra = largura_tela - 20
        altura_barra = 20
        porcentagem_xp = max(0, jogador.experiencia_atual / jogador.experiencia_level_up)
        #fundo
        fundo_rect = pygame.Rect(posicao_x, posicao_y, largura_barra, altura_barra)
        pygame.draw.rect(tela, 'black', fundo_rect)
        #frente
        frente_rect = pygame.Rect(posicao_x, posicao_y, largura_barra * porcentagem_xp, altura_barra)
        pygame.draw.rect(tela, 'blue', frente_rect)
        #borda
        pygame.draw.rect(tela, 'white', fundo_rect, 2)

    def draw_barra_vida(self, tela):
        jogador = self.game.player

        # Obtém o deslocamento da câmera através do mapa
        deslocamento = self.game.mapa.get_camera_offset(jogador.posicao, (largura_tela, altura_tela))

        posicao_x = jogador.rect.centerx - (jogador.rect.width / 2) - deslocamento[0]
        posicao_y = jogador.rect.bottom + 10 - deslocamento[1]

        largura_barra = jogador.rect.width
        altura_barra = 10
        porcentagem_vida = max(0, jogador.vida_atual / jogador.vida_maxima)

        #barra total
        fundo_rect = pygame.Rect(posicao_x, posicao_y, largura_barra, altura_barra)
        pygame.draw.rect(tela, 'dark red', fundo_rect)
        #vida
        frente_rect = pygame.Rect(posicao_x, posicao_y, largura_barra * porcentagem_vida, altura_barra)
        pygame.draw.rect(tela, 'dark blue', frente_rect)
        #borda
        pygame.draw.rect(tela, 'white', fundo_rect, 2)

    def desenhar_timer(self, tela):
        tempo_total = self.game.timer_jogo
        minutos = int(tempo_total // 60)
        segundos = int(tempo_total % 60)
        texto_tempo = f"{minutos:02d}:{segundos:02d}"
        
        fonte = pygame.font.SysFont("Arial", 36, bold=True)
        superficie_texto = fonte.render(texto_tempo, True, (255, 255, 255))
        rect_texto = superficie_texto.get_rect(center=(largura_tela // 2, 45))
        tela.blit(superficie_texto, rect_texto)

    
    def draw_boss_hud(self, tela):
        boss = self.game.boss_atual
        if boss and hasattr(boss, 'vida'):
            # Configurações de Dimensões
            largura_barra = largura_tela * 0.6
            altura_barra = 12 
            x = (largura_tela - largura_barra) // 2
            y = altura_tela - 80 

            # Cálculo de vida (Garante que não passe de 1 ou seja menor que 0)
            porcentagem = max(0, min(1, boss.vida / boss.vida_base))
            
            # --- DESENHO DO NOME ---
            nome_texto = boss.titulo
            fonte_boss = pygame.font.SysFont("Cinzel", 25)
            surf_nome = fonte_boss.render(nome_texto, True, (215, 175, 65)) # Tom levemente dourado
            
            # Centraliza o texto corretamente usando o rect
            rect_nome = surf_nome.get_rect(center=(largura_tela // 2, y - 15))
            tela.blit(surf_nome, rect_nome)

            # --- DESENHO DAS BARRAS ---
            # Retângulo de Fundo (Sombra/Preto)
            fundo_rect = pygame.Rect(x, y, largura_barra, altura_barra)
            pygame.draw.rect(tela, (15, 15, 15), fundo_rect)
            
            # Retângulo de Vida (Vermelho escuro)
            vida_largura = largura_barra * porcentagem
            vida_rect = pygame.Rect(x, y, vida_largura, altura_barra)
            pygame.draw.rect(tela, (130, 0, 0), vida_rect)
            
            # --- MOLDURA ---
            moldura_rect = fundo_rect.inflate(4, 4) # Aumenta 2px de cada lado
            
            pygame.draw.rect(tela, (215, 175, 60), moldura_rect, 2)


    def draw(self, tela):
        #pega quantidade de cada coletavel
        contagem_exp = self.game.player.coletaveis['exp_shard']
        contagem_big = self.game.player.coletaveis['big_shard']
        contagem_life = self.game.player.coletaveis['life_orb']
        contagem_cafe = self.game.player.coletaveis['cafe']

        #contador dos coletáveis
        life_surf = self.font.render(f'{contagem_life}', True, 'white')
        life_rect = life_surf.get_rect(midleft = (60, 40))

        exp_surf = self.font.render(f'{contagem_exp}', True, 'white')
        exp_rect = exp_surf.get_rect(midleft = (60, 90))

        big_surf = self.font.render(f'{contagem_big}', True, 'white')
        big_rect = big_surf.get_rect(midleft = (60, 140))

        cafe_surf = self.font.render(f'{contagem_cafe}', True, 'white')
        cafe_rect = cafe_surf.get_rect(midleft = (60, 190))


        #desenha os icones de cada coletáveis com a respectiva contagem
        tela.blit(self.icone_life_orb, (20, 25))
        tela.blit(life_surf, life_rect)


        tela.blit(self.icone_exp_shard, (20, 75))
        tela.blit(exp_surf, exp_rect)

        tela.blit(self.icone_big_shard, (20, 125))
        tela.blit(big_surf, big_rect)

        tela.blit(self.icone_cafe, (20, 175))
        tela.blit(cafe_surf, cafe_rect)

        # Desenha a base do HUD
        self.draw_barra_vida(tela)
        self.draw_barra_exp(tela)
        self.desenhar_timer(tela)
        self.draw_boss_hud(tela)