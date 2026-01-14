import pygame
from game import *
from feats.items import *
from enemies.enemies import *
from feats.projetil import Laser
from player import *
import random
import math

class Didact(InimigoBase):
    def __init__(self, posicao, game, grupos):
        valor_vida = 10000
        super().__init__(posicao, vida_base=valor_vida, dano_base=40, velocidade_base=50, game=game)
        self.titulo = "DIDACT, O Forerunner Banido"
        self.game = game
        # -------
        # Sprites
        # -------
        self.sprites = {}
        self.sprites['left'] = [
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'didact', 'did1.png')).convert_alpha(), (250, 375)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'didact', 'did2.png')).convert_alpha(), (250, 375)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'didact', 'did3.png')).convert_alpha(), (250, 375)),
            pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'didact', 'did4.png')).convert_alpha(), (250, 375))
            ]
        self.sprites['right'] = [
            pygame.transform.flip(sprite, True, False) for sprite in self.sprites['left']
        ]
        # Pull
        self.sprites['pull'] = pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'didact', 'didpull.png')).convert_alpha(), (250, 375))
        self.sprites['pullright'] = pygame.transform.flip(self.sprites['pull'], True, False)
        # Laser
        self.sprites['laser'] = pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'didact', 'didpull.png')).convert_alpha(), (250, 375))
        self.sprites['laserright'] = pygame.transform.flip(self.sprites['laser'], True, False)
        # Cryptum
        self.sprites['cryptum'] = pygame.transform.scale(pygame.image.load(join('assets', 'img', 'enemies', 'bosses', 'didact', 'cryptum.png')).convert_alpha(), (400, 400))
        
        # Framagem da sprite
        self.frame_atual = 0  
        self.estado_animacao = 'right'
        self.indice_animacao = 0
        self.image = self.sprites[self.estado_animacao][self.indice_animacao]
        self.rect = self.image.get_rect(center=self.posicao)
        self.mask = pygame.mask.from_surface(self.image)
        self.velocidade_animacao = 450
        self.ultimo_update_animacao = pygame.time.get_ticks()

        #hitbox
        nova_largura = self.rect.width / 2
        self.hitbox = pygame.Rect(0, 0, nova_largura, self.rect.height)
        self.hitbox.center = self.rect.center

        #pull ability
        self.velocidade_puxao = 525
        self.cooldown_pull = 5000 # 5 segundos de recarga
        self.tempo_ultimo_pull = pygame.time.get_ticks()
        self.duracao_pull = 5000 # 5 segundos de duração
        self.tempo_inicio_pull = 0
        self.dano_pull = self.jogador.vida_maxima / 100
        self.intervalo_dano_pull = 1000  # Intervalo de 1000 milissegundos
        self.tempo_ultimo_dano_pull = 0 

        #laser ability
        self.cooldown_laser = 10000
        self.tempo_ultimo_laser = pygame.time.get_ticks()
        self.duracao_aviso_laser = 500 # 0.5 segundos de aviso
        self.duracao_disparo_laser = 500 # 0.5 segundos de disparo
        self.tempo_inicio_laser = 0
        self.posicao_alvo_laser = pygame.math.Vector2()

        # Cryptum
        self.velocidade_cryptum = 80
        self.velocidade = self.velocidade_cryptum
        self.estado_habilidade = 'crypt' # 'parado', 'ataque_pull', 'ataque_laser'
        self.ultima_cryptum = pygame.time.get_ticks()
        self.cryptum_shield = 5000
        self.cryptum_healing = 4000
        self.updated_life = 0
        self.cooldown_crypt = 20000
        self.retornar_para_crypt = False
        self.enrage = False

    @property
    def collision_rect(self):
        "Retorna a hitbox de Didact."
        return self.hitbox

    def ativar_laser(self):
        agora = pygame.time.get_ticks()
        if agora - self.tempo_ultimo_laser >= self.cooldown_laser:
            # Define os possíveis valores de cooldown (em milissegundos)
            possiveis_cooldowns = [400, 4500, 5000, 5500] 
            self.cooldown_laser = random.choice(possiveis_cooldowns)
            self.velocidade = 0
            self.estado_habilidade = 'aviso_laser'
            self.tempo_inicio_laser = agora
            self.tempo_ultimo_laser = agora
            # Trava a posição do jogador para o aviso e o laser
            self.posicao_alvo_laser = self.jogador.posicao.copy()
            # Cria o aviso do laser (a linha reta)
            LaserWarning(
                start_pos=self.posicao,
                end_pos=self.posicao_alvo_laser,
                grupos=self.game.all_sprites,
                game=self.game
            )
        
    # Crie um método para disparar o laser
    def disparar_laser(self):
        # Cria o projétil de laser
        Laser(
            posicao_inicial=self.posicao.copy(), # Posição atual do Didact
            posicao_final=self.posicao_alvo_laser.copy(), # Posição travada do jogador
            grupos=(entity_manager.all_sprites, entity_manager.projeteis_inimigos_grupo),
            game=self.game,
            player=self.game.player
        )

    def puxar_jogador(self):
        agora = pygame.time.get_ticks()
        if agora - self.tempo_ultimo_pull >= self.cooldown_pull:
            novo_cooldown = [10000, 12000, 15000, 17000]
            self.cooldown_pull = random.choice(novo_cooldown)
            self.estado_habilidade = 'ataque_pull'
            self.tempo_inicio_pull = agora
            self.tempo_ultimo_pull = agora

    def aplicar_efeito_pull(self, delta_time):
        # Calcula a direção do jogador para o Didact
        direcao_puxao = self.posicao - self.jogador.posicao
        if direcao_puxao.length() > 0:
            direcao_puxao.normalize_ip()
        # Move o jogador em direção ao Didact
        self.jogador.posicao += direcao_puxao * self.velocidade_puxao * delta_time
        # E atualize o rect do jogador
        self.jogador.rect.center = self.jogador.posicao
        

    def cryptum(self):
        novo_cooldown = [12000, 13000, 14000, 15000]
        self.cooldown_crypt = random.choice(novo_cooldown)
        # Cura a vida de Didact
        self.vida += self.cryptum_healing
        if self.vida > self.vida_base:
            self.vida = self.vida_base
        # Salva a vida
        self.updated_life = self.vida
        # Aumenta a speed enquanto na cripta
        self.velocidade = self.velocidade_cryptum

    def animar(self):
        # Sai da cripta somente após ficar com menos de 6000 de vida ou receber o dano de quebra
        if self.estado_habilidade == 'crypt':
            self.image = self.sprites['cryptum']
        # Se o Didact está usando o pull, a imagem não muda
        elif self.estado_habilidade == 'ataque_pull':
            if self.estado_animacao == 'right':
                self.image = self.sprites['pullright']
            else:
                self.image = self.sprites['pull']
            # Corrija a linha abaixo para atualizar o rect corretamente
        else:
                agora = pygame.time.get_ticks()
                if agora - self.ultimo_update_animacao > self.velocidade_animacao:
                    self.ultimo_update_animacao = agora
                    self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
                    self.image = self.sprites[self.estado_animacao][self.frame_atual]
                    
        self.rect = self.image.get_rect(center=self.posicao)
        self.mask = pygame.mask.from_surface(self.image)
    
    def morrer(self, grupos):
        alvo_grupos = (entity_manager.all_sprites, entity_manager.item_group)
        chance= randint(1,1000)

        # Drop garantido de Shards grandes por ser Boss
        qtd_shards = 5
        if chance > 800: qtd_shards = 10
        elif chance > 600: qtd_shards = 7

        for _ in range(qtd_shards):
            pos_offset = self.posicao + pygame.math.Vector2(random.randint(-30, 30), random.randint(-30, 30))
            Items(posicao=pos_offset, sheet_item=join('assets', 'img', 'bigShard.png'), tipo='big_shard', grupos=alvo_grupos)
        self.kill()
        
    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        direcao = (self.jogador.posicao - self.posicao)
        distancia = direcao.length()
        if distancia > 0:
            direcao.normalize_ip()
            if direcao.x < 0: self.estado_animacao = 'left'
            elif direcao.x > 0: self.estado_animacao = 'right'

        if self.velocidade > 0:
                self.posicao += direcao * self.velocidade * delta_time
                self.rect.center = (round(self.posicao.x), round(self.posicao.y))
                self.hitbox.center = self.rect.center

        # -----------------------
        # Verificação de Estágios
        # -----------------------

        # Calcula a porcentagem de vida
        percentual_vida = self.vida / self.vida_base
        if percentual_vida < 0.15:
            if not self.enrage:
                self.enrage = True
                self.cooldown_laser = 900000
                self.cooldown_pull = 900000
                self.velocidade_cryptum = 500
                self.cooldown_crypt = 100
                self.cryptum_healing = 10000
        if percentual_vida < 0.3: # Fase 4
            if not self.enrage:
                self.velocidade_animacao = 400
                self.velocidade_cryptum = 350
                self.cryptum_healing = 8000
                self.cryptum_shield = 4000
                self.velocidade_puxao = 600
                self.duracao_aviso_laser = 250
            
        elif percentual_vida < 0.5: # Fase 3
            if not self.enrage:
                self.cryptum_healing = 5000
                self.velocidade_cryptum = 180

        elif percentual_vida < 0.75: # Fase 2
            if not self.enrage:
                self.velocidade_base = 60
                self.velocidade_cryptum = 150
                self.velocidade_puxao = 550
                self.duracao_aviso_laser = 400

        else:
            if not self.enrage:
                self.velocidade_base = 50
                self.velocidade_cryptum = 80
                self.velocidade_puxao = 525
                self.velocidade_animacao = 450
                self.duracao_aviso_laser = 500
                self.cryptum_healing = 4000
                self.cryptum_shield = 5000

        # ----------------------------
        # Lógica de controle de estado
        # ----------------------------

        # ESTADO: CRYPTUM (Cura)
        if self.estado_habilidade == 'crypt':
            self.velocidade = self.velocidade_cryptum
            if distancia > 500:
                self.retornar_para_crypt = True # Ativa a memória
                self.puxar_jogador()
            # Condição de saída (Vida inicial ou quebra de escudo)
            if not self.enrage:
                if (self.vida < 8000 and self.updated_life == 0) or \
                    (self.updated_life > 0 and (self.updated_life - self.vida) >= self.cryptum_shield):
                    self.estado_habilidade = 'parado'
                    self.ultima_cryptum = agora
                    self.updated_life = 0
                    self.velocidade = self.velocidade_base
                    self.retornar_para_crypt = False # Reset flag

        # ESTADO: PULL
        elif self.estado_habilidade == 'ataque_pull':
            self.velocidade = 0
            # Aplica o dano ao jogador se o intervalo de tempo foi atingido
            if agora - self.tempo_ultimo_dano_pull >= self.intervalo_dano_pull:
                self.jogador.tomar_dano_direto(self.dano_pull)
                self.tempo_ultimo_dano_pull = agora
            # Se a duração da habilidade terminou, volte ao estado normal
            if agora - self.tempo_inicio_pull >= self.duracao_pull:
                self.velocidade_puxao += 25
                if self.retornar_para_crypt:
                    self.estado_habilidade = 'crypt'
                    self.velocidade = self.velocidade_cryptum
                else:
                    self.estado_habilidade = 'parado'
                    self.velocidade = self.velocidade_base
                
                self.retornar_para_crypt = False # Limpa a memória
            else:
                # Continue aplicando o efeito de puxar
                self.aplicar_efeito_pull(delta_time)

        # ESTADO: AVISO LASER
        elif self.estado_habilidade == 'aviso_laser':
            # Verifica se o tempo de aviso terminou
            if agora - self.tempo_inicio_laser >= self.duracao_aviso_laser:
                # O aviso terminou, agora é o momento de disparar
                self.estado_habilidade = 'disparo_laser'
                self.tempo_inicio_laser = agora
                self.disparar_laser()
                # Mude a sprite para o laser no momento do disparo
                if self.estado_animacao == 'right':
                    self.image = self.sprites['laserright']
                else:
                    self.image = self.sprites['laser']
                
                self.rect.center = self.posicao

        # ESTADO: DISPARO LASER
        elif self.estado_habilidade == 'disparo_laser':
            # Fica com a sprite do laser enquanto ele é disparado
            if agora - self.tempo_inicio_laser >= self.duracao_disparo_laser:
                self.velocidade = self.velocidade_base
                self.estado_habilidade = 'parado'
        
        else:
            if agora - self.ultima_cryptum >= self.cooldown_crypt:
                self.estado_habilidade = 'crypt'
                self.ultima_cryptum = agora
                self.cryptum()
            elif (self.jogador.posicao - self.posicao).length() > 500:
                self.puxar_jogador()
            elif agora - self.tempo_ultimo_laser >= self.cooldown_laser and self.estado_habilidade != 'crypt':
                self.ativar_laser()

        self.animar()
        
class LaserWarning(pygame.sprite.Sprite):
    def __init__(self, start_pos, end_pos, grupos, game):
        super().__init__(grupos)
        self.game = game
        self.start_pos = pygame.math.Vector2(start_pos)
        
        # Calcular a direção do laser
        direcao = pygame.math.Vector2(end_pos) - self.start_pos
        if direcao.length() > 0:
            direcao.normalize_ip()
        else:
            # Caso o jogador esteja exatamente na mesma posição do didact
            direcao = pygame.math.Vector2(1, 0)
        
        self.end_pos = self.start_pos + direcao * 2000

        self.duracao = 1000  # 1.5 segundos de aviso
        self.largura = 400
        self.tempo_criacao = pygame.time.get_ticks()

        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.start_pos)
    def draw(self, surface, offset):
        agora = pygame.time.get_ticks()
        if agora - self.tempo_criacao < self.duracao:
            # Posições ajustadas pela câmera
            start_pos_ajustada = self.start_pos - offset
            end_pos_ajustada = self.end_pos - offset
            
            # Desenha a linha na tela principal
            pygame.draw.line(surface, (250, 0, 0, 100), start_pos_ajustada, end_pos_ajustada, self.largura)

    def update(self, delta_time):
        agora = pygame.time.get_ticks()
        if agora - self.tempo_criacao >= self.duracao:
            self.kill() # Remove o aviso depois que o tempo de vida termina


     