import pygame

class EntityManager:
    """Armazena todos os grupos de sprite."""
    def __init__(self):
        self.all_sprites = pygame.sprite.Group() # Ou sua classe AllSprites()
        self.inimigos_grupo = pygame.sprite.Group()
        self.projeteis_jogador_grupo = pygame.sprite.Group()
        self.projeteis_inimigos_grupo = pygame.sprite.Group()
        self.items_grupo = pygame.sprite.Group()
        self.auras_grupo = pygame.sprite.Group()
        self.player = None

# Cria uma instância única que será importada por todos
entity_manager = EntityManager()