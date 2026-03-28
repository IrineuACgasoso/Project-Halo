import pygame
import random
from enemies.enemies import *
from player.player import *
from feats.items import *
from systems.entitymanager import entity_manager



class BossArbiter(InimigoBase):
    def __init__(self, posicao, game, grupos):
        valor_vida = 4500
        super().__init__(posicao, vida_base=valor_vida, dano_base=80, velocidade_base=90, game=game, sprite_key='arbiter', flip_sprite=True)
        self.titulo = "THEL 'VADAM, O Comandante da Frota Covenant"
        
        self.game = game
        
        # Sprites e Animação
        self.sprites = self.get_sprites('default')
        self.frame_atual = 0  
        self.estado_animacao = 'right'
        self.indice_animacao = 0
        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center=self.posicao)
        self.velocidade_animacao = 200
        self.ultimo_update_animacao = pygame.time.get_ticks()

        # Hitbox
        nova_largura = self.rect.width / 2
        self.hitbox = pygame.Rect(0, 0, nova_largura, self.rect.height)
        self.hitbox.center = self.rect.center

        # Habilidade: Invisibilidade
        self.cooldown_invisibilidade = 8000
        self.duracao_invisi = 3500
        self.invisivel = False
        self.ultima_invisibi = pygame.time.get_ticks()
        self.duracao_falha = 30
        self.tempo_desde_falha = 0
        
        # Variáveis do Fade
        self.alpha_atual = 255.0
        self.alpha_alvo = 255.0
        self.velocidade_fade = 600 # Quão rápido o alpha muda (pixels de alpha por segundo)

        # Habilidade: Burst Carabina
        self.cooldown_carabin = 3000
        self.intervalo_carabina = 75
        self.cronometro_carabina = 0
        self.ultima_carabina = 0
        self.carabina_restante = 0
        self.contagem_carabina = 5

    @property
    def collision_rect(self):
        "Retorna a hitbox de Arbiter."
        # Só remove a hitbox se ele estiver totalmente invisível
        if self.alpha_atual <= 0:
            return pygame.Rect(-1000, -1000, 0, 0)
        return self.hitbox
    
    @property
    def invulneravel(self):
        return self.alpha_atual < 200
    
    def carabin(self):
        Carabin(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites, entity_manager.projeteis_inimigos_grupo),
            jogador=self.jogador,
            game=self.game,
            dano=40,
            velocidade=750,
            tamanho=(16, 16)
        )

    def animar(self):
        agora = pygame.time.get_ticks()
        
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            self.rect = self.image.get_rect(center=self.posicao)
            
        # Sempre reaplica o alpha atual, pois a troca de sprites reseta a transparência
        self.image.set_alpha(int(self.alpha_atual))

    def morrer(self, grupos = None):
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 6, 100)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 75)
        Items.spawn_drop(self.posicao, grupos, 'cafe', 1, 1)
        self.kill()

    # --- FUNÇÕES FATORADAS DAS HABILIDADES ---

    def _gerenciar_invisibilidade(self, agora, delta_time):
        if not self.invisivel:
            self.alpha_alvo = 255 # Alvo é ficar visível
            # Ativa a invisibilidade se o cooldown acabou
            if agora - self.ultima_invisibi >= self.cooldown_invisibilidade:
                self.cooldown_invisibilidade = random.choice([9000, 12000, 15000, 18000])
                self.invisivel = True
                self.adicionar_escudo(250)
                self.ultima_invisibi = agora
                self.velocidade *= 4 # Bônus de velocidade
                self.alpha_alvo = 0 # Alvo muda para invisível
        else:
            # Lógica para quando o boss está invisível
            if agora - self.ultima_invisibi >= self.duracao_invisi:
                # Desativa a invisibilidade e volta ao normal
                self.invisivel = False
                self.velocidade /= 4 
                self.alpha_alvo = 255 # Volta o alvo para visível
            else:
                # Falha na invisibilidade ao encostar no jogador
                if self.hitbox.colliderect(self.jogador.hitbox):
                    self.tempo_desde_falha = agora
                    self.alpha_alvo = 100 # Fica parcialmente visível
                
                # Retorna ao stealth total após a falha
                if agora - self.tempo_desde_falha >= self.duracao_falha:
                    self.alpha_alvo = 0

        # Aplica a matemática do fade
        if self.alpha_atual != self.alpha_alvo:
            if self.alpha_atual < self.alpha_alvo:
                self.alpha_atual += self.velocidade_fade * delta_time
                if self.alpha_atual > self.alpha_alvo:
                    self.alpha_atual = self.alpha_alvo
            else:
                self.alpha_atual -= self.velocidade_fade * delta_time
                if self.alpha_atual < self.alpha_alvo:
                    self.alpha_atual = self.alpha_alvo

    def _gerenciar_carabina(self, agora, delta_time):
        # Entra em cooldown e recarrega a contagem
        if agora - self.ultima_carabina >= self.cooldown_carabin:
            self.carabina_restante = self.contagem_carabina
            self.cooldown_carabin = random.choice([4000, 5000, 6000, 7000])
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
        agora = pygame.time.get_ticks()
        
        # 1. Movimentação Principal
        direcao = (self.jogador.posicao - self.posicao)
        if direcao.length() > 0:
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * delta_time
            if paredes:
                self.aplicar_colisao_mapa(paredes, self.raio_colisao_mapa)
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))
            self.hitbox.center = self.rect.center

        # 2. Habilidades
        self._gerenciar_invisibilidade(agora, delta_time) # Agora passamos o delta_time
        self._gerenciar_carabina(agora, delta_time)

        # 3. Animação
        if direcao.x < 0:
            self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'
        
        self.animar()