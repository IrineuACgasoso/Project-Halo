import pygame
from os.path import join
from windows.settings import *
from systems.camera import Camera
from feats.assets import ASSETS
from player import *

class HUD:
    def __init__(self, game):
        self.game = game
        #seta fonte para o numero da hud
        self.font = pygame.font.Font(None, 36)

        # Controle de otimização para busca de boss
        self.ultimo_check_boss = 0
        self.intervalo_check_boss = 500

        #pega imagem e da scale para ficar menor
        #xp
        self.icone_exp_shard = ASSETS['items']['exp_shard']
        self.icone_exp_shard = pygame.transform.scale(self.icone_exp_shard, (30, 30))
        #big shard
        self.icone_big_shard = ASSETS['items']['big_shard']
        self.icone_big_shard = pygame.transform.scale(self.icone_big_shard, (30, 30))
        #life orb
        self.icone_life_orb = ASSETS['items']['life_orb']
        self.icone_life_orb = pygame.transform.scale(self.icone_life_orb, (30, 30))
        #cafe
        self.icone_cafe = ASSETS['items']['cafe']
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

        # Obtém o deslocamento da câmera 
        deslocamento = self.game.camera.offset + self.game.camera.shake_offset

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

        if not self.game.boss_atual:
            fonte = pygame.font.SysFont("Arial", 36, bold=True)
            superficie_texto = fonte.render(texto_tempo, True, (255, 255, 255))
            rect_texto = superficie_texto.get_rect(center=(largura_tela // 2, 45))
            tela.blit(superficie_texto, rect_texto)

    def atualizar_boss_foco(self):
        """Busca o Boss mais próximo do jogador para focar na HUD."""
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_check_boss < self.intervalo_check_boss:
            return

        self.ultimo_check_boss = agora
        
        # Filtra apenas inimigos que são bosses e estão vivos
        bosses = [sprite for sprite in self.game.inimigos_grupo if hasattr(sprite, 'titulo')]
        
        if bosses:
            # Encontra o boss com a menor distância Euclidiana até o jogador
            self.game.boss_atual = min(
                bosses, 
                key=lambda b: b.posicao.distance_to(self.game.player.posicao)
            )
        else:
            self.game.boss_atual = None


    def draw_boss_hud(self, tela):

        self.atualizar_boss_foco()

        boss = self.game.boss_atual
        if boss and hasattr(boss, 'vida') and not getattr(boss, 'is_animating_respawn', False):
            # Configurações de Dimensões
            largura_barra = largura_tela * 0.6
            altura_barra = 12 
            x = (largura_tela - largura_barra) // 2
            y = altura_tela - 80 

            # Cálculo de vida (Garante que não passe de 1 ou seja menor que 0)
            porcentagem = max(0, min(1, boss.vida / boss.vida_base))
            
            # --- DESENHO DO NOME ---
            nome_texto = boss.titulo
            self.font_path = join('assets', 'fonts', 'cinzel', 'Cinzel-Regular.otf')
            fonte_boss = pygame.font.Font(self.font_path, 25)
            surf_nome = fonte_boss.render(nome_texto, True, (215, 175, 65)) # Tom levemente dourado
            rect_nome = surf_nome.get_rect(center=(largura_tela // 2, y - 17))

            # Sombra no texto para dar destaque
            surf_sombra = fonte_boss.render(nome_texto, True, (10, 10, 10))
            rect_sombra = surf_sombra.get_rect(center=(largura_tela // 2 + 2, y - 15))
            tela.blit(surf_sombra, rect_sombra) # Desenha a sombra primeiro
            tela.blit(surf_nome, rect_nome)     # Desenha o texto principal por cima

            # --- DESENHO DAS BARRAS ---
            # Retângulo de Fundo (Sombra/Preto)
            fundo_rect = pygame.Rect(x, y, largura_barra, altura_barra)
            pygame.draw.rect(tela, (15, 15, 15), fundo_rect)
            
            # Cor da vida: Se for a forma final, podemos usar um roxo, senão vermelho
            cor_vida = (130, 0, 0) if not getattr(boss, 'is_final_form', False) else (100, 0, 150)

            # Retângulo de Vida (Vermelho escuro)
            vida_largura = largura_barra * porcentagem
            vida_rect = pygame.Rect(x, y, vida_largura, altura_barra)
            pygame.draw.rect(tela, cor_vida, vida_rect)
            
            if hasattr(boss, 'escudo_atual') and boss.escudo_atual > 0 and boss.escudo_maximo > 0:
                porcentagem_escudo = max(0, min(1, boss.escudo_atual / boss.escudo_maximo))
                escudo_largura = largura_barra * porcentagem_escudo
                escudo_rect = pygame.Rect(x, y, escudo_largura, altura_barra)
                # Uma cor azul brilhante para o escudo
                pygame.draw.rect(tela, (0, 120, 255), escudo_rect)

            # --- MOLDURA DECORADA ---
            # 1. Borda escura externa (Sombra da moldura)
            sombra_moldura = fundo_rect.inflate(6, 6)
            pygame.draw.rect(tela, (20, 15, 5), sombra_moldura, 3)

            # 2. Borda dourada principal
            moldura_rect = fundo_rect.inflate(4, 4) 
            pygame.draw.rect(tela, (215, 175, 60), moldura_rect, 2)

            # 3. Detalhes metálicos nos cantos (Pequenos quadrados dourados mais claros)
            tam_canto = 6
            cor_canto = (255, 230, 120)
            
            # Canto Superior Esquerdo
            pygame.draw.rect(tela, cor_canto, (moldura_rect.left - 2, moldura_rect.top - 2, tam_canto, tam_canto))
            # Canto Superior Direito
            pygame.draw.rect(tela, cor_canto, (moldura_rect.right - tam_canto + 2, moldura_rect.top - 2, tam_canto, tam_canto))
            # Canto Inferior Esquerdo
            pygame.draw.rect(tela, cor_canto, (moldura_rect.left - 2, moldura_rect.bottom - tam_canto + 2, tam_canto, tam_canto))
            # Canto Inferior Direito
            pygame.draw.rect(tela, cor_canto, (moldura_rect.right - tam_canto + 2, moldura_rect.bottom - tam_canto + 2, tam_canto, tam_canto))

            # DICA: Quando você tiver uma imagem de moldura, apague a parte "MOLDURA DECORADA" acima e use:
            # tela.blit(self.imagem_moldura_boss, (x - offset, y - offset))


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