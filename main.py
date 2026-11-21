import pygame
from source.windows.settings import *
from source.feats.assets import carregar_assets
from source.game import Game

def main():
    pygame.init()
    pygame.mixer.init()

    tela = pygame.display.set_mode((largura_tela, altura_tela))
    pygame.display.set_caption("Master Chief Edge")
    carregar_assets()   # depois da janela: convert_alpha usa o formato dela

    game = Game(tela)
    game.run()
    
    pygame.quit()

if __name__ == "__main__":
    main()
    