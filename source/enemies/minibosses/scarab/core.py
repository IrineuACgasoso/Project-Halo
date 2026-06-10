import pygame
from source.enemies.base.enemy_base import BaseEnemy
from source.feats.items import Items

# Imports locais do pacote
from .setup import ScarabSetup
from .states import ScarabAI
from .attacks import ScarabAttacks

class Scarab(BaseEnemy, ScarabSetup, ScarabAI, ScarabAttacks):
    def __init__(self, posicao, game, **kwargs):
        super().__init__(posicao, vida_base=15000, dano_base=80, velocidade_base=35, 
                         game=game, sprite_key='scarab', flip_sprite=True)
        self.titulo = "SCARAB"
        
        self.setup_animation(
            estado_inicial='left',
            velocidade_animacao=700
        )        
        
        self.inicializar_sistemas()

    def receber_dano(self, quantidade):
        dano_final = quantidade

        # 1. FASE VULNERÁVEL (STUN) -> Dano direto na vida
        if self.estado_combate == 'STUNNED':
            player_x = self.jogador.posicao.x
            scarab_x = self.posicao.x
            
            # Checa o "Backstab" (x10 de dano nas costas)
            if self.estado_animacao == 'right' and player_x < scarab_x:
                dano_final *= 10
            elif self.estado_animacao == 'left' and player_x > scarab_x:
                dano_final *= 10
                
            super().receber_dano(dano_final)

        # 2. FASE DEFENSIVA -> Dano vai pro escudo
        else:
            # Checa o eixo Y: Se o player estiver "abaixo" do centro do Scarab (atirando nas pernas)
            if self.jogador.posicao.y > self.posicao.y:
                dano_final *= 5
                
            self.escudo_atual -= dano_final
            
            # Verifica se o escudo quebrou
            if self.escudo_atual <= 0:
                self.escudo_atual = 0
                self.iniciar_stun()

    def tomar_dano_direto(self, quantidade):
        self.receber_dano(quantidade)

    def iniciar_stun(self):
        """Congela o Scarab e o deixa vulnerável"""
        self.estado_combate = 'STUNNED'
        self.tempo_inicio_stun = pygame.time.get_ticks()

    def animar(self):
        # TRAVA DA ANIMAÇÃO: Não se mexe enquanto estiver atordoado
        if self.estado_combate == 'STUNNED':
            return

        agora = pygame.time.get_ticks()
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
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 5, 100)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 50)
        Items.spawn_drop(self.posicao, grupos, 'cafe', 1, 1)
        self.kill()

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()

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