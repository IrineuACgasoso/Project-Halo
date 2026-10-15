import pygame
from source.systems.gameclock import relogio

class LaserWarning(pygame.sprite.Sprite):
    def __init__(self, owner, alvo, grupos, game, 
                 cor_laser=(250, 0, 0, 30), 
                 largura=300, duracao=1500):
        
        super().__init__(grupos)
        self.game = game
        self.owner = owner  # Inimigo que está mirando
        self.alvo = alvo    # Geralmente o jogador
        
        self.duracao = duracao
        self.largura = largura
        self.cor_laser = cor_laser
        self.tempo_criacao = relogio.agora()

        # Posições iniciais
        self.start_pos = pygame.math.Vector2(owner.posicao)
        self.end_pos = pygame.math.Vector2(alvo.posicao)
        
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect()

    def update(self, delta_time):
        agora = relogio.agora()
        
        # Se o tempo acabou ou quem disparou morreu, remove o aviso
        if agora - self.tempo_criacao >= self.duracao or not self.owner.alive():
            self.kill()
            return

        # 1. Atualiza a posição de origem (caso o inimigo se mova)
        self.start_pos = pygame.math.Vector2(self.owner.posicao)

        # 2. Calcula a direção em direção ao alvo
        direcao = self.alvo.posicao - self.start_pos
        
        if direcao.length() > 0:
            direcao = direcao.normalize()
        else:
            direcao = pygame.math.Vector2(1, 0)

        # 3. Projeta o laser para bem longe na direção do alvo (ex: 3000 pixels)
        self.end_pos = self.start_pos + direcao * 3000

    def draw(self, surface, offset):
        # O desenho acontece em uma surface temporária para suportar o Alpha da linha
        temp_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        
        start_pos_ajustada = self.start_pos - offset
        end_pos_ajustada = self.end_pos - offset
        
        # Efeito opcional: fazer o laser "piscar" ou ficar mais forte perto do disparo
        tempo_passado = relogio.agora() - self.tempo_criacao
        progresso = tempo_passado / self.duracao
        alpha = int(30 + (progresso * 90)) # Fica levemente mais visível com o tempo
        
        cor_com_alpha = (*self.cor_laser[:3], alpha)

        # Desenha a linha de aviso
        pygame.draw.line(temp_surface, cor_com_alpha, start_pos_ajustada, end_pos_ajustada, self.largura)
        
        # Cola na superfície principal
        surface.blit(temp_surface, (0, 0))