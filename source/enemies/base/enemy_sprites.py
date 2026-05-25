import pygame

from source.feats.assets import ASSETS

class EnemySprites:
    GLOBAL_SPRITE_CACHE = {}
    #===================================================================================================
    #                               CACHE
    #===================================================================================================
    def _check_and_load_sprites(self, key, flip_sprite):
        """Carrega e organiza o cache. Se flip_sprite for True, o arquivo de disco é 'left'."""
        if key not in EnemySprites.GLOBAL_SPRITE_CACHE:
            EnemySprites.GLOBAL_SPRITE_CACHE[key] = {}
            conteudo = ASSETS['enemies'][key]
            
            # Normaliza o conteúdo para um dicionário para facilitar o processamento
            if isinstance(conteudo, pygame.Surface):
                processar = {
                    'default': [conteudo]
                }

            elif isinstance(conteudo, list):
                processar = {
                    'default': conteudo
                }

            else:
                processar = conteudo

            for var_name, frames in processar.items():
                # Se 'frames' for apenas uma imagem solta, transforma ela em uma lista de 1 item
                if isinstance(frames, pygame.Surface):
                    frames = [frames]
                    
                frames_invertidos = [pygame.transform.flip(f, True, False) for f in frames]
                
                if flip_sprite:
                    # Se o original olha para a esquerda, o flipado olha para a direita
                    EnemySprites.GLOBAL_SPRITE_CACHE[key][var_name] = {
                        'left': frames,
                        'right': frames_invertidos
                    }
                else:
                    # Caso padrão: original olha para a direita, flipado para a esquerda
                    EnemySprites.GLOBAL_SPRITE_CACHE[key][var_name] = {
                        'right': frames,
                        'left': frames_invertidos
                    }
    
    def get_sprites(self, variante=None):
        sprites_enemy = EnemySprites.GLOBAL_SPRITE_CACHE[self.sprite_key]
        # Se não passar variante
        if variante is None:
            # Tenta default
            if 'default' in sprites_enemy:
                return sprites_enemy['default']

            # Senão pega a primeira disponível
            primeira_variante = next(iter(sprites_enemy))
            return sprites_enemy[primeira_variante]

        # Variante explícita
        if variante not in sprites_enemy:
            raise KeyError(
                f"Variante '{variante}' não encontrada "
                f"para enemy '{self.sprite_key}'"
            )

        return sprites_enemy[variante]
        

    #======================================================================================
    #                               VISUAL
    #====================================================================================== 
    def setup_visual(self, posicao, variante=None):
        self.sprites = self.get_sprites(variante)
        self.set_image(self.get_current_sprite())
        self.rect.center = posicao
        self.posicao = pygame.Vector2(self.rect.center)

    def get_current_sprite(self):
        frames = self.sprites[self.estado_animacao]
        self.frame_atual %= len(frames)
        return frames[self.frame_atual].copy()
    
    def trocar_variante(self, variante):
        centro_antigo = self.rect.center
        self.sprites = self.get_sprites(variante)
        self.frame_atual = 0
        self.set_image(self.get_current_sprite())
        self.rect.center = centro_antigo
    
    def update_mask(self):
        self.mask = pygame.mask.from_surface(self.image)

    def sync_rect(self):
        self.rect.center = (
            round(self.posicao.x),
            round(self.posicao.y)
        )

    def set_image(self, image):
        alpha = getattr(self, "alpha_atual", 255)
        # Primeiro setup (sem rect ainda)
        if not hasattr(self, "rect"):
            self.image = image
            self.image.set_alpha(alpha)

            self.rect = self.image.get_rect()
            self.update_mask()
            return

        # Runtime normal
        centro_antigo = self.rect.center
        self.image = image
        self.image.set_alpha(alpha)
        self.rect = self.image.get_rect(center=centro_antigo)

        self.update_mask()