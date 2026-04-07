import pygame
import random
from os.path import join
from source.feats.items import Items
from source.enemies.enemies import InimigoBase
from source.feats.projetil import LaserBeam
from source.feats.skills import OndaEMP, ArtilhariaAviso
from source.feats.effects import LaserWarning
from source.systems.entitymanager import entity_manager


class Didact(InimigoBase):
    def __init__(self, posicao, game, grupos):
        valor_vida = 8000
        super().__init__(posicao, vida_base=valor_vida, dano_base=60, velocidade_base=50, game=game, sprite_key='didact', flip_sprite=True)
        
        self.titulo = "DIDACT, O Forerunner Banido"
        self.game = game
        
        # --- Sprites e Animação ---
        self.sprites = self.get_sprites('default')
        self.attack_sprite = self.get_sprites('attack')
        self.cryptum_sprite = self.get_sprites('cryptum')
        
        self.frame_atual = 0  
        self.estado_animacao = 'right'
        self.velocidade_animacao = 350
        self.ultimo_update_animacao = pygame.time.get_ticks()
        
        self.image = self.sprites[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center=self.posicao)
        self.mask = pygame.mask.from_surface(self.image)

        # --- Hitbox ---
        self.hitbox = pygame.Rect(0, 0, self.rect.width / 2, self.rect.height)
        self.hitbox.center = self.rect.center

        # --- Habilidades e Estados ---
        self.estado_habilidade = 'parado' # 'parado', 'ataque_pull', 'aviso_laser', 'disparo_laser', 'crypt'
        self.enrage = False
        
        # Pull
        self.velocidade_puxao = 500
        self.cooldown_pull = 5000
        self.tempo_ultimo_pull = pygame.time.get_ticks()
        self.duracao_pull = 5000
        self.tempo_inicio_pull = 0
        self.dano_pull = self.jogador.vida_maxima / 100
        self.intervalo_dano_pull = 1000
        self.tempo_ultimo_dano_pull = 0 

        # Laser
        self.cooldown_laser = 10000
        self.tempo_ultimo_laser = pygame.time.get_ticks()
        self.duracao_aviso_laser = 1500
        self.duracao_disparo_laser = 500
        self.tempo_inicio_laser = 0
        self.posicao_alvo_laser = pygame.math.Vector2()

        # Cryptum
        self.velocidade_cryptum = 270
        self.velocidade = self.velocidade_base
        self.cryptum_shield = 15000 # Escudo bem forte
        self.entrou_fase_cryptum = False

        # --- Mecânicas Exclusivas do Cryptum ---
        
        # Pulso EMP
        self.cooldown_emp = 3000
        self.tempo_ultimo_emp = 0
        
        # Artilharia de Luz Sólida
        self.cooldown_artilharia = 1200
        self.tempo_ultima_artilharia = 0

    @property
    def collision_rect(self):
        return self.hitbox

    # ---------------------------------------------------------
    # MÉTODOS DE HABILIDADE
    # ---------------------------------------------------------
    def ativar_laser(self):
        agora = pygame.time.get_ticks()
        self.cooldown_laser = random.randint(4000, 5500)
        self.velocidade = 0
        self.estado_habilidade = 'aviso_laser'
        self.tempo_inicio_laser = agora
        self.tempo_ultimo_laser = agora
        
        self.posicao_alvo_laser = self.jogador.posicao.copy()
        LaserWarning(owner=self, 
                     alvo=self.jogador, 
                     grupos=entity_manager.all_sprites, 
                     game=self.game,
                     duracao=1600
                     )

    def disparar_laser(self):
        LaserBeam(
            posicao_inicial=self.posicao.copy(),
            grupos=(entity_manager.all_sprites, entity_manager.projeteis_inimigos_grupo),
            jogador=self.jogador,
            game=self.game,
            dano= self.dano_base * 4,
            velocidade=1500,
            duracao=1500,
            color= 'red',
            tamanho= (128, 128)
        )

    def puxar_jogador(self):
        agora = pygame.time.get_ticks()
        self.cooldown_pull = random.randint(10000, 15000)
        self.estado_habilidade = 'ataque_pull'
        self.tempo_inicio_pull = agora
        self.tempo_ultimo_pull = agora

    def aplicar_efeito_pull(self, delta_time):
        direcao_puxao = self.posicao - self.jogador.posicao
        if direcao_puxao.length() > 0:
            direcao_puxao.normalize_ip()
            
        self.jogador.posicao += direcao_puxao * self.velocidade_puxao * delta_time
        self.jogador.rect.center = self.jogador.posicao

    def ativar_cryptum(self):
        self.cooldown_crypt = random.choice([12000, 13000, 14000, 15000])
        self.adicionar_escudo(self.cryptum_shield)
        self.velocidade = self.velocidade_cryptum
        self.estado_habilidade = 'crypt'
        self.ultima_cryptum = pygame.time.get_ticks()
        
        # Reseta os status das mecânicas da crypta
        self.tempo_ultimo_emp = pygame.time.get_ticks()
        self.tempo_ultima_artilharia = pygame.time.get_ticks()

    def disparar_emp(self):
        OndaEMP(posicao=self.posicao.copy(), grupos=self.game.all_sprites, game=self.game, atacante=self)

    def disparar_artilharia(self):
        # Mira em um ponto aleatório próximo ao jogador (prevendo movimento)
        offset = pygame.math.Vector2(random.randint(-150, 150), random.randint(-150, 150))
        alvo = self.jogador.posicao + offset
        ArtilhariaAviso(posicao=alvo, grupos=self.game.all_sprites, game=self.game, atacante=self, dano=200)

    # ---------------------------------------------------------
    # ATUALIZAÇÃO E ESTADOS
    # ---------------------------------------------------------
    def verificar_fases(self):
        percentual_vida = self.vida / self.vida_base
        
        # NOVA FASE: Cryptum aos 25% de vida
        if percentual_vida <= 0.25 and not self.entrou_fase_cryptum:
            self.entrou_fase_cryptum = True
            self.ativar_cryptum()
            # Opcional: Você pode resetar o Enrage aqui para forçá-lo a ficar dentro da Crypta
            self.enrage = False 

        # Enrage aos 15% (acontece dentro ou depois da Crypta)
        if percentual_vida < 0.15 and not self.enrage:
            self.enrage = True
            self.cooldown_laser = random.randint(1000, 1500)
            self.cooldown_pull = random.randint(500, 1500)
            
        elif percentual_vida < 0.3 and not self.enrage: # Fase 4
            self.velocidade_animacao = 180
            self.velocidade_puxao = 600
            
        elif percentual_vida < 0.5 and not self.enrage: # Fase 3
            self.velocidade_base = 90
            self.velocidade_animacao = 200
            self.velocidade_puxao = 600
            
        elif percentual_vida < 0.75 and not self.enrage: # Fase 2
            self.velocidade_base = 70
            self.velocidade_animacao = 250
            self.velocidade_puxao = 550

    def executar_estados(self, agora, delta_time):
        distancia = (self.jogador.posicao - self.posicao).length()

        # ESTADO: CRYPTUM
        if self.estado_habilidade == 'crypt':
            self.velocidade = self.velocidade_cryptum
            
            # 1. Pulso EMP
            if agora - self.tempo_ultimo_emp >= self.cooldown_emp:
                self.disparar_emp()
                self.tempo_ultimo_emp = agora
                
            # 2. Artilharia de Luz Sólida
            if agora - self.tempo_ultima_artilharia >= self.cooldown_artilharia:
                self.disparar_artilharia()
                self.tempo_ultima_artilharia = agora

            # Verifica se o escudo quebrou para sair da Crypta
            quebrou_escudo = self.escudo_atual <= 0
            
            if not self.enrage and quebrou_escudo:
                self.estado_habilidade = 'parado'
                self.ultima_cryptum = agora
                self.escudo_atual = 0 
                self.velocidade = self.velocidade_base
                # Trava o laser e o pull por um tempinho após sair da crypta
                self.tempo_ultimo_laser = agora
                self.tempo_ultimo_pull = agora

        # ESTADO: PULL
        elif self.estado_habilidade == 'ataque_pull':
            self.velocidade = 0
            if agora - self.tempo_ultimo_dano_pull >= self.intervalo_dano_pull:
                self.jogador.tomar_dano_direto(self.dano_pull)
                self.tempo_ultimo_dano_pull = agora
                
            if agora - self.tempo_inicio_pull >= self.duracao_pull:
                self.estado_habilidade = 'parado'
                self.velocidade = self.velocidade_base
            else:
                self.aplicar_efeito_pull(delta_time)

        # ESTADO: AVISO LASER
        elif self.estado_habilidade == 'aviso_laser':
            if agora - self.tempo_inicio_laser >= self.duracao_aviso_laser:
                self.estado_habilidade = 'disparo_laser'
                self.tempo_inicio_laser = agora
                self.disparar_laser()
                self.rect.center = self.posicao

        # ESTADO: DISPARO LASER
        elif self.estado_habilidade == 'disparo_laser':
            if agora - self.tempo_inicio_laser >= self.duracao_disparo_laser:
                self.velocidade = self.velocidade_base
                self.estado_habilidade = 'parado'

        # ESTADO: PARADO / DECIDINDO AÇÃO
        else:
            if distancia > 500 and (agora - self.tempo_ultimo_pull >= self.cooldown_pull):
                self.puxar_jogador()
            elif agora - self.tempo_ultimo_laser >= self.cooldown_laser:
                self.ativar_laser()

    def animar(self):
        agora = pygame.time.get_ticks()
        
        if self.estado_habilidade == 'crypt':
            # Usa o sprite do cryptum na direção atual. 
            # Como é 1 frame só, pegamos o índice [0] da lista
            self.image = self.cryptum_sprite[self.estado_animacao][0]
            
        elif self.estado_habilidade in ['ataque_pull', 'aviso_laser', 'disparo_laser']:
            # Agrupa pull e laser para usarem o mesmo sprite 'attack'
            self.image = self.attack_sprite[self.estado_animacao][0]
            
        else:
            # Animação padrão (andando/parado)
            if agora - self.ultimo_update_animacao > self.velocidade_animacao:
                self.ultimo_update_animacao = agora
                self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            
            # Atualiza a imagem com base no frame atual
            self.image = self.sprites[self.estado_animacao][self.frame_atual]

        self.rect = self.image.get_rect(center=self.posicao)
        self.mask = pygame.mask.from_surface(self.image)


    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()
        direcao = (self.jogador.posicao - self.posicao)

        if direcao.length() > 0:
            direcao.normalize_ip()
            self.estado_animacao = 'left' if direcao.x < 0 else 'right'

        if self.velocidade > 0:
            self.posicao += direcao * self.velocidade * delta_time
            if paredes:
                self.aplicar_colisao_mapa(paredes, self.raio_colisao_mapa)
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))
            self.hitbox.center = self.rect.center
        
        self.verificar_fases()
        self.executar_estados(agora, delta_time)
        self.animar()

    def morrer(self, grupos = None):
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 8, 100)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 1, 80)
        Items.spawn_drop(self.posicao, grupos, 'cafe', 1, 1)
        self.kill()

