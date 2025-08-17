import pygame
from os.path import join

class Ranking:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(None, 48)
        self.scores = []

        self.input_mode = False 
        self.player_name = ""
        self.current_score = 0
        self.input_rect = pygame.Rect(400, 300, 400, 50)
        self.color_active = pygame.Color('lightskyblue3')
        self.color_inactive = pygame.Color('gray15')
        self.color = self.color_inactive
        self.active = False

        # --- Carregar background ---
        self.background = pygame.image.load(join('assets', 'img', 'ranking.jpg')).convert()
        # Opcional: ajustar para a tela
        self.background = pygame.transform.scale(self.background, (self.game.tela.get_width(), self.game.tela.get_height()))

    def start_name_input(self, score):
        self.input_mode = True
        self.active = True
        self.player_name = ""
        self.current_score = score
        self.color = self.color_active

    def add_score_and_finish_input(self):
        name_to_add = self.player_name if self.player_name.strip() != "" else "Player"
        self.scores.append({'name': name_to_add, 'score': self.current_score})
        self.scores = sorted(self.scores, key=lambda x: x['score'], reverse=True)[:10]
        self.input_mode = False
        self.active = False
        self.color = self.color_inactive

    def handle_event(self, event):
        if not self.input_mode:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return 'exit_to_menu'
            return None

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.add_score_and_finish_input()
            elif event.key == pygame.K_BACKSPACE:
                self.player_name = self.player_name[:-1]
            else:
                if self.font.size(self.player_name + event.unicode)[0] < self.input_rect.width - 10:
                    self.player_name += event.unicode
        return None

    def draw(self, tela):
        # --- Desenhar background ---
        tela.blit(self.background, (0, 0))

        if self.input_mode:
            title_text = self.font.render("Fim de Jogo!", True, (255, 255, 255))
            tela.blit(title_text, (title_text.get_rect(centerx=tela.get_width()/2).x, 100))

            score_text = self.font.render(f"Sua Pontuação Final: {self.current_score}", True, (255, 255, 255))
            tela.blit(score_text, (score_text.get_rect(centerx=tela.get_width()/2).x, 180))
            
            instruction_text = self.font.render("Digite seu nome:", True, (200, 200, 200))
            tela.blit(instruction_text, (instruction_text.get_rect(centerx=tela.get_width()/2).x, 250))

            pygame.draw.rect(tela, self.color, self.input_rect, 2)
            name_surface = self.font.render(self.player_name, True, (255, 255, 255))
            tela.blit(name_surface, (self.input_rect.x + 10, self.input_rect.y + 5))

            enter_text = self.font.render("Pressione ENTER para confirmar", True, (200, 200, 200))
            tela.blit(enter_text, (enter_text.get_rect(centerx=tela.get_width()/2).x, 400))
        else:
            title = self.font.render("Ranking", True, (255, 255, 255))
            tela.blit(title, (100, 50))

            if not self.scores:
                no_scores_text = self.font.render("Nenhuma pontuação registrada.", True, (255, 255, 255))
                tela.blit(no_scores_text, (100, 150))
            else:
                for i, score in enumerate(self.scores):
                    text = f"{i + 1}. {score['name']} - {score['score']}"
                    txt = self.font.render(text, True, (255, 255, 255))
                    tela.blit(txt, (100, 100 + i * 50))

            back_text = self.font.render("Pressione ESC para voltar ao menu", True, (255, 255, 255))
            tela.blit(back_text, (100, 650))
