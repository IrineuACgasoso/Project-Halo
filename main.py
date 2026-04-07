import pygame
from source.windows.settings import *
from source.game import Game

def main():
    pygame.init()
    pygame.mixer.init()

    tela = pygame.display.set_mode((largura_tela, altura_tela))
    pygame.display.set_caption("Master Chief Edge")

    game = Game(tela)
    game.run()
    
    pygame.quit()

if __name__ == "__main__":
    main()
    