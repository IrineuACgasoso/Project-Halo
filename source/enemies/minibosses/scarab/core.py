import pygame
from source.systems.gameclock import relogio
from source.enemies.base.enemy_base import BaseEnemy
from source.feats.items import Items

# Imports locais do pacote
from .setup import ScarabSetup
from .states import ScarabAI
from .attacks import ScarabAttacks
from source.systems.status import IMUNIDADES_CHEFE

class Scarab(BaseEnemy, ScarabSetup, ScarabAI, ScarabAttacks):
    imunidades_status = IMUNIDADES_CHEFE   # sem stun nem lentidão de fora (roteiro §8, item 8)
    def __init__(self, posicao, game, **kwargs):
        super().__init__(posicao, vida_base=15000, dano_base=80, velocidade_base=35, 
                         game=game, sprite_key='scarab', flip_sprite=True)
        self.titulo = "SCARAB"
        self.is_boss = True
        
        self.setup_animation(
            estado_inicial='left',
            velocidade_animacao=700
        )        
        
        self.inicializar_sistemas()

    def ajustar_dano_recebido(self, valor, dano):
        # 1. FASE VULNERÁVEL (STUN): "Backstab" (x10 de dano nas costas)
        if self.estado_combate == 'STUNNED':
            player_x = self.jogador.posicao.x
            scarab_x = self.posicao.x
            if self.estado_animacao == 'right' and player_x < scarab_x:
                valor *= 10
            elif self.estado_animacao == 'left' and player_x > scarab_x:
                valor *= 10

        # 2. FASE DEFENSIVA: se o player estiver "abaixo" do centro do Scarab (atirando nas pernas)
        elif self.jogador.posicao.y > self.posicao.y:
            valor *= 5
        return valor

    def absorver_dano(self, valor):
        # Vulnerável (stun): escudo e vida, como qualquer inimigo
        if self.estado_combate == 'STUNNED':
            super().absorver_dano(valor)
            return

        # Defensivo: o dano vai só para o escudo (sem transbordo); escudo quebrado = stun
        self.escudo_atual -= valor
        if self.escudo_atual <= 0:
            self.escudo_atual = 0
            self.iniciar_stun()

    def iniciar_stun(self):
        """Congela o Scarab e o deixa vulnerável"""
        self.estado_combate = 'STUNNED'
        self.is_inofensivo = True
        self.tempo_inicio_stun = relogio.agora()

    def animar(self):
        # TRAVA DA ANIMAÇÃO: Não se mexe enquanto estiver atordoado
        if self.estado_combate == 'STUNNED':
            return

        agora = relogio.agora()
        if agora - getattr(self, 'ultimo_update_animacao', 0) > getattr(self, 'velocidade_animacao', 700):
            self.ultimo_update_animacao = agora
            frames = self.sprites[self.estado_animacao]
            self.frame_atual = (self.frame_atual + 1) % len(frames)
            self.image = frames[self.frame_atual]
            self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))

    def aplicar_camera_shake(self):
        if self.frame_atual in [0, 2]:
            self.game.camera.shake(intensidade=self.intensidade_shake)

    def morrer(self, grupos=None):
        Items.spawn_drop(
            self.posicao, 
            grupos, 
            big_shard=((5, 6, 8, 10), (70, 28, 1.5, 0.5), 100), 
            life_orb=(1, 100, 100),              
            upgrade=((1, 2), (99, 1), 100)       
        )
        self.kill()

    def update(self, delta_time, paredes=None):
        agora = relogio.agora()

        # Inteligência e Estados
        self.executar_ia(agora, delta_time)

        # Só se move se estiver ativamente em combate móvel
        if self.estado_combate == 'MOVENDO':
            super().update(delta_time, paredes)
            self.aplicar_camera_shake()

        # Só vira para o player se NÃO estiver atordoado
        if self.estado_combate != 'STUNNED':
            self.estado_animacao = 'left' if self.jogador.posicao.x < self.posicao.x else 'right'
        
        self.animar()