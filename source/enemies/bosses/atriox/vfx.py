import pygame
from source.systems.entitymanager import entity_manager

class ProtocoloHalo(pygame.sprite.Sprite):
    def __init__(self, game, boss, tempo_limite_ms=180000):
        super().__init__(entity_manager.all_sprites) 
        
        self.game = game
        self.boss = boss
        
        # Controle de Tempo
        self.tempo_inicio = pygame.time.get_ticks()
        self.tempo_limite = tempo_limite_ms 
        
        # Controle Visual (Fade Branco)
        self.iniciou_disparo = False
        self.alpha_branco = 0.0

        # Dummy rect para não quebrar o Y-sort do Game.draw()
        self.image = pygame.Surface((0, 0)) 
        self.rect = self.image.get_rect(center=(0,0))
        
        # Superfície do clarão
        self.superficie_branca = pygame.Surface(game.tela.get_size(), pygame.SRCALPHA)
        
        # Fonte para o timer holográfico
        self.fonte_timer = pygame.font.SysFont("Consolas", 28, bold=True)

    def update(self, delta_time, *args, **kwargs):
        # 1. Checa se o boss morreu ou deixou de existir
        if not self.boss or not self.boss.alive() or getattr(self.boss, 'vida', 0) <= 0:
            self.kill()
            return

        agora = pygame.time.get_ticks()

        # 2. Lógica matemática do timer (sem blits!)
        if not self.iniciou_disparo:
            tempo_passado = agora - self.tempo_inicio
            if tempo_passado >= self.tempo_limite:
                self.iniciou_disparo = True

        # 3. Lógica matemática do fade
        if self.iniciou_disparo:
            self.alpha_branco += 70 * delta_time
            if self.alpha_branco >= 255:
                self.alpha_branco = 255
                # O player recebe dano letal quando o fade termina
                entity_manager.player.receber_dano(float('inf'))

    def hud_draw(self, surface):
        """Chamado exclusivamente pela HUD para desenhar UI e overlays"""
        agora = pygame.time.get_ticks()
        
        # Se disparou, pinta a tela
        if self.iniciou_disparo:
            self.superficie_branca.fill((255, 255, 255, int(self.alpha_branco)))
            surface.blit(self.superficie_branca, (0, 0))
            
        # Se não disparou, desenha o cronômetro
        else:
            tempo_passado = agora - self.tempo_inicio
            tempo_restante_seg = max(0, (self.tempo_limite - tempo_passado) // 1000)
            
            minutos = tempo_restante_seg // 60
            segundos = tempo_restante_seg % 60
            texto = f"ATIVAÇÃO DO HALO: {minutos:02d}:{segundos:02d}"
            
            # Pisca em vermelho se tiver menos de 30 segundos, senão fica azul
            if tempo_restante_seg <= 30 and (agora % 500 < 250):
                cor = (255, 50, 50)
            else:
                cor = (180, 220, 255)
                
            surf_texto = self.fonte_timer.render(texto, True, cor)
            rect_texto = surf_texto.get_rect(center=(surface.get_width() // 2, 80))
            
            # Sombrinha para dar contraste
            sombra = self.fonte_timer.render(texto, True, (0, 0, 0))
            surface.blit(sombra, rect_texto.move(2, 2))
            surface.blit(surf_texto, rect_texto)