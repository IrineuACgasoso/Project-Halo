import pygame
from source.systems.gameclock import relogio
from source.systems.entitymanager import entity_manager
from source.data.enemy_data import DROP_PADRAO
from source.systems.status import StatusEntidade

class EnemySetup:
    imunidades_status = frozenset()   # bosses e minibosses: IMUNIDADES_CHEFE (systems/status)

    def setup_core(self, game, sprite_key, variante):
        self.game = game
        self.sprite_key = sprite_key
        self.variante = variante
        self.jogador = self.game.player
        self.nome_completo = "INIMIGO"
        self.is_boss = False
        self.tabela_drop = DROP_PADRAO   # kwargs de Items.spawn_drop; os comuns trocam pela do perfil
        # Buffs e debuffs (systems/status); bosses declaram `imunidades_status` na classe
        self.status = StatusEntidade(self, imunidades=self.imunidades_status)

    def setup_stats(self, vida_base, dano_base, velocidade_base):
        # Base
        self.vida_base = vida_base
        self.dano_base = dano_base
        self.velocidade_base = velocidade_base

        # Stats atuais
        self.vida_maxima = vida_base
        self.vida = self.vida_base
        self.dano = self.dano_base
        self.velocidade = self.velocidade_base
    
    def setup_shield(self):
        self.escudo_maximo = 0
        self.escudo_atual = 0

    def setup_sprite_placeholder(self, posicao):
        self.image = pygame.Surface((40, 40))
        self.image.fill('white')
        self.rect = self.image.get_rect(center=posicao)
        self.posicao = pygame.math.Vector2(self.rect.center)

    def setup_collision(self):
        self.raio_colisao_mapa = 15
        self.iteracoes_colisao_mapa = 2

    def setup_spawn_protection(self):
        self.invencivel = False
        self.tempo_criacao = relogio.agora()
        self.tempo_invencibilidade = 0
    
    def setup_invisibility(self):
        self.invisibilidade = None     # skill ativa (feats/skills/invisibilidade) ou None
        self.alpha_atual = 255
    