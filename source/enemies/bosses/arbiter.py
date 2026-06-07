import pygame
import random
from source.enemies.base.enemy_base import *
from source.feats.items import *
from source.feats.projetil import Carabin
from source.systems.entitymanager import entity_manager



class BossArbiter(BaseEnemy):
    def __init__(self, posicao, game):
        valor_vida = 4500
        super().__init__(posicao, vida_base=valor_vida, dano_base=80, velocidade_base=90, game=game, sprite_key='arbiter', flip_sprite=True)
        self.titulo = "THEL 'VADAM, O Comandante da Frota Covenant"
        
        self.setup_animation(
            estado_inicial='right',
            velocidade_animacao=200
        )

        # Hitbox
        nova_largura = self.rect.width / 2
        self.hitbox = pygame.Rect(0, 0, nova_largura, self.rect.height)
        self.hitbox.center = self.rect.center

        # Habilidade: Invisibilidade
        self.cooldown_invisibilidade = 8000
        self.duracao_invisi = 3500
        self.ultima_invisibi = pygame.time.get_ticks()
        
        # Habilidade: Burst Carabina
        self.cooldown_carabin = 3000
        self.intervalo_carabina = 75
        self.cronometro_carabina = 0
        self.ultima_carabina = 0
        self.carabina_restante = 0
        self.contagem_carabina = 5

    @property
    def collision_rect(self):
        # Reutiliza o alpha_atual que o EnemyCombat calcula dinamicamente
        if getattr(self, 'alpha_atual', 255) <= 0:
            return pygame.Rect(-1000, -1000, 0, 0)
        return self.hitbox
    
    @property
    def invulneravel(self):
        return getattr(self, 'alpha_atual', 255) < 200
    
    def carabin(self):
        direcao_tiro = self.calcular_direcao_tiro(0.02)

        self.trigger_flash(duracao=35, bonus_alpha=60)

        Carabin(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites,),
            jogador=self.jogador,
            game=self.game,
            dono='INIMIGO',
            tamanho=(16, 16),
            dano=40,
            velocidade=750,
            direcao_spread=direcao_tiro
        )

    def morrer(self, grupos = None):
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 6, 100)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 75)
        Items.spawn_drop(self.posicao, grupos, 'cafe', 1, 1)
        self.kill()

    # --- FUNÇÕES FATORADAS DAS HABILIDADES ---

    def _gerenciar_invisibilidade(self, agora, dt_ms):
        # Se não está invisível, checa se pode ativar por cooldown
        if not getattr(self, 'invisivel', False):
            if agora - self.ultima_invisibi >= self.cooldown_invisibilidade:
                self.cooldown_invisibilidade = self.novo_cooldown(9000, 18000)
                self.ultima_invisibi = agora
                self.velocidade_base *= 4 # Bônus de velocidade do Boss
                self.adicionar_escudo(250) # REAPROVEITADO do EnemyCombat
                
                # Inicia a máquina de estados de camuflagem oficial
                self.iniciar_invisibilidade(
                    alpha_alvo=0, fade_out=600, fade_in=600, 
                    duracao=self.duracao_invisi, flashing=False
                )
        else:
            # Revelar parcialmente se tomar "trombada" do Player
            if self.hitbox.colliderect(self.jogador.hitbox):
                self.trigger_flash(duracao=400, bonus_alpha=120) # Força o boss a aparecer um pouco
                
            # Verifica se o hold/fade_in do sistema base acabou para resetar a velocidade
            if not self.invisivel:
                self.velocidade_base /= 4

    def _gerenciar_carabina(self, agora, delta_time):
        # Entra em cooldown e recarrega a contagem
        if agora - self.ultima_carabina >= self.cooldown_carabin:
            self.carabina_restante = self.contagem_carabina
            self.cooldown_carabin = self.novo_cooldown(4000, 7000)
            self.ultima_carabina = agora
        
        # Dispara as balas restantes com base no intervalo
        if self.carabina_restante > 0:
            self.cronometro_carabina += delta_time * 1000
            if self.cronometro_carabina >= self.intervalo_carabina:
                self.cronometro_carabina = 0
                self.carabina_restante -= 1
                self.carabin()

    # ----------------------------------------

    def update(self, delta_time, paredes=None):
        super().update(delta_time, paredes)
        agora = pygame.time.get_ticks()
        dt_ms = delta_time * 1000
        
        # Processamento de Habilidades
        self._gerenciar_invisibilidade(agora, dt_ms)
        self._gerenciar_carabina(agora, delta_time)

        direcao_x = self.jogador.posicao.x - self.posicao.x 
        
        self.set_sprite_direction(direcao_x)
        self.animar()