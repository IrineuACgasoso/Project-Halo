import pygame
from source.systems.gameclock import relogio

from source.enemies.base.enemy_base import BaseEnemy
from source.feats.items import Items

from .setup import JegaSetup
from .ia import JegaAI
from .attacks import JegaAttacks
from source.systems.status import IMUNIDADES_CHEFE


class Jega(BaseEnemy, JegaSetup, JegaAI, JegaAttacks):
    imunidades_status = IMUNIDADES_CHEFE   # sem stun nem lentidão de fora (roteiro §8, item 8)
    def __init__(self, posicao, game, **kwargs):
        super().__init__(posicao, vida_base=5000, dano_base=100, velocidade_base=50,
                          game=game, sprite_key='jega', flip_sprite=True)

        self.titulo = "JEGA 'RDOMNAI, O Matador de Spartans"
        self.is_boss = True

        self.setup_animation(estado_inicial='right', velocidade_animacao=200)

        # Hitbox
        nova_largura = self.rect.width / 1.3
        self.hitbox = pygame.Rect(0, 0, nova_largura, self.rect.height)
        self.hitbox.center = self.rect.center

        # Máquina de Estados e Habilidades
        self.inicializar_habilidades()

    @property
    def collision_rect(self):
        return self.hitbox

    @property
    def inofensivo(self):
        """Na órbita e na ilusão ele atravessa o mapa (e o jogador): sem dano de contato.
        Invisível, pode ser atingido, só não mirado (regra geral)."""
        return super().inofensivo or self.estado in ('orbitando', 'ilusao')

    def morrer(self, grupos=None):
        Items.spawn_drop(
            self.posicao, 
            grupos, 
            big_shard=((6, 8, 10), (70, 28, 2), 100), 
            life_orb=(1, 100, 100),              
            upgrade=((1, 2), (99, 1), 100)       
        )
        self.kill()

    def animar(self):
        agora = relogio.agora()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            # O rect precisa ser atualizado na troca de frame
            self.rect = self.image.get_rect(center=self.posicao)

        # Reaplica a transparência atual (a máquina de invisibilidade da base já calcula o valor)
        self.image.set_alpha(int(self.alpha_atual))

    def update(self, delta_time, paredes=None):
        agora = relogio.agora()

        # Cálculos de Vetor (sempre ao quadrado nas comparações de gatilho)
        direcao_ao_jogador = (self.jogador.posicao - self.posicao)
        distancia_sq = direcao_ao_jogador.length_squared()

        # 1. Máquina de Estados e Movimentação Principal (inclui invisibilidade da base)
        self.executar_estados(agora, delta_time, direcao_ao_jogador, distancia_sq)

        # 2. Habilidades Extras: Burst de Carabina, Spike e Ilusão Sombria
        self.processar_carabina(agora, delta_time)
        self.processar_spike(agora, delta_time)
        self.processar_ilusao(agora, delta_time)

        # 3. Colisão com o Mapa (não se aplica orbitando nem durante a ilusão,
        if paredes and self.estado not in ('orbitando', 'ilusao'):
            self.aplicar_colisao_mapa(paredes)

        # Atualiza Retângulos
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        self.hitbox.center = self.rect.center

        # 4. Animação
        if direcao_ao_jogador.x < 0:
            self.estado_animacao = 'left'
        elif direcao_ao_jogador.x > 0:
            self.estado_animacao = 'right'

        self.animar()