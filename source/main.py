import pygame
from settings import *
from game import Game

def main():
    pygame.init()
    pygame.mixer.init()

    tela = pygame.display.set_mode((largura_tela, altura_tela))
    pygame.display.set_caption("IP-ocalipse Cin-vivors")

    game = Game(tela)
    game.run()
    
    pygame.quit()

if __name__ == "__main__":
    main()
