import pygame
import random

from source.enemies.base.enemy_base import BaseEnemy
from source.feats.projetil import PlasmaGun, M50
from source.systems.entitymanager import entity_manager


class Jackal(BaseEnemy): 
    def __init__(self, posicao, game, tipo=None):
        # Se um tipo não for forçado pela subclasse, sorteia os padrões
        self.tipo = tipo if tipo else random.choice(['blue', 'red'])
        
        super().__init__(
            posicao, 
            vida_base=15, 
            dano_base=10, 
            velocidade_base=50, 
            game=game, 
            sprite_key='jackal', 
            flip_sprite=True, 
            variante=self.tipo
        )

        self.setup_animation(
            estado_inicial='right',
            velocidade_animacao=150
        )

        # Habilidades
        self.plasma_cooldown = self.novo_cooldown(4500, 6000)
        self.escudo_quebrado = False
        self.ultimo_tiro = pygame.time.get_ticks()

    def deve_mover(self):
        direcao = self.jogador.posicao - self.posicao
        return direcao.length() > 150

    def executar_ataque(self):
        """Dispara a arma padrão da classe (PlasmaGun)."""
        direcao_tiro = self.jogador.posicao - self.posicao
        if direcao_tiro.length() > 0:
            direcao_tiro = direcao_tiro.normalize()
        else:
            direcao_tiro = pygame.math.Vector2(1, 0)
            
        PlasmaGun(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites,),
            jogador=self.jogador,
            game=self.game,
            dono='INIMIGO',
            tamanho=(28, 28),
            dano=4,
            velocidade=250,
            direcao_spread=direcao_tiro,
            vai_rotacionar=False
        )

    def checar_quebra_escudo(self):
        """Verifica e aplica a quebra visual do escudo (exclusivo para as variantes com escudo)."""
        if self.tipo in ['blue', 'red'] and self.vida < 0.3 * self.vida_base and not self.escudo_quebrado:
            self.tipo = f"{self.tipo}_broken"
            self.trocar_variante(self.tipo)
            self.escudo_quebrado = True

    def update(self, delta_time, paredes=None):
        # Verifica a regra de movimentação específica da classe
        if self.deve_mover():
            self.mover(delta_time)
            if paredes:
                self.aplicar_colisao_mapa(paredes)

        # Orientação do Sprite
        direcao_x = self.jogador.posicao.x - self.posicao.x
        self.set_sprite_direction(direcao_x)

        # Controle de Cadência de Tiro
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro >= self.plasma_cooldown:
            self.plasma_cooldown = self.novo_cooldown(6000, 11000)
            self.executar_ataque()
            self.ultimo_tiro = agora
        
        self.checar_quebra_escudo()
        self.sync_rect()
        self.animar()


class JackalSniper(Jackal):
    def __init__(self, posicao, game):
        # Inicia a classe mãe já fixando a variante 'sniper'
        super().__init__(posicao, game, tipo='sniper')

    def deve_mover(self):
        """Sobrescreve a movimentação: O Sniper só anda se o jogador estiver longe."""
        direcao = self.jogador.posicao - self.posicao
        return direcao.length() > 400

    def executar_ataque(self):
        """Sobrescreve o ataque: Dispara o rifle M50 em vez da pistola de plasma."""
        direcao_tiro = self.jogador.posicao - self.posicao
        
        M50(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites,),
            jogador=self.jogador,
            game=self.game,
            dono='INIMIGO',
            tamanho=(45, 45),
            dano=50,
            velocidade=750,
            direcao_spread=direcao_tiro
        )