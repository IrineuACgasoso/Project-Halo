import pygame
import math
from source.windows.settings import *
from source.player.player import *
from source.feats.assets import ASSETS
from source.feats.baseweapon import *


class Companheiro(pygame.sprite.Sprite):
    def __init__(self, jogador, grupos, inimigos_grupo, item_grupo, tipo='MISTO', nome_asset = 'arbiter'):
        super().__init__(grupos)
        self.jogador = jogador
        self.inimigos_grupo = inimigos_grupo
        self.items_grupo = item_grupo
        self.tipo = tipo # 'CAÇADOR', 'COLETOR' ou 'MISTO'
        
        self.estado_logico = 'SEGUINDO'
        self.alvo = None
        self.direcao_movimento = pygame.math.Vector2()

        # Atributos base
        # Atributos de movimento e lógica
        self.velocidade_andar = 250 if nome_asset == 'arbiter' else 150
        self.velocidade_correr = 300 if nome_asset == 'arbiter' else 200

        self.raio_deteccao_inimigo = 400
        self.raio_deteccao_item = 350
        self.distancia_seguidor = 200

        # Lógica de Órbita
        self.angulo_orbita = 0
        self.velocidade_orbita = 5  # Velocidade do giro
        self.raio_orbita = 40      # Distância do giro ao redor do alvo 

        self.dano = 0 
        self.cooldown = 1000 
        self.ultimo_dano_tempo = 0

        # Carregamento de sprites
        self.sprites = {}
        self.sprites['right'] = ASSETS['buddies'][nome_asset]
        self.sprites['left'] = [pygame.transform.flip(sprite, True, False) for sprite in self.sprites['right']]

        # Configurações de imagem inicial
        self.estado_animacao = 'right' 
        self.frame_atual = 0
        self.image = self.sprites[self.estado_animacao][self.frame_atual]
        self.rect = self.image.get_rect(center = self.jogador.posicao)
        self.posicao = pygame.math.Vector2(self.rect.center)

        # Lógica de controle
        self.estado_logico = 'SEGUINDO'
        self.alvo = None
        self.direcao_movimento = pygame.math.Vector2()
        self.velocidade_animacao = 200 if nome_asset=='cortana' else 150
        self.ultimo_update_anim = pygame.time.get_ticks()
        
    def logica_de_decisao(self):
        # Usando a distância ao quadrado para evitar o cálculo da raiz
        dist_sq_jogador = self.posicao.distance_squared_to(self.jogador.posicao)
        # 1. Se estiver muito longe do jogador, FORÇA a volta (Independente do alvo)
        raio_maximo = self.raio_deteccao_inimigo if self.tipo == 'CAÇADOR' else self.raio_deteccao_item
        if dist_sq_jogador > raio_maximo**2:
            self.estado_logico = 'SEGUINDO'
            self.alvo = self.jogador
            return
        
        # Função auxiliar interna para checar se o alvo atual ainda é válido
        def alvo_e_valido(alvo):
            if alvo is None: return False
            if alvo == self.jogador: return True
            return hasattr(alvo, 'alive') and alvo.alive()
        
        # 2. Busca Inimigo (Apenas se for Caçador ou Misto)
        if self.tipo in ['CAÇADOR', 'MISTO']:
            # Só busca se o alvo atual for o jogador ou se o alvo atual morreu
            
            if not alvo_e_valido(self.alvo) or self.alvo == self.jogador:
                inimigo = self.encontrar_alvo_mais_proximo(self.inimigos_grupo, self.raio_deteccao_inimigo, precisa_dano=True)
                if inimigo:
                    self.estado_logico = 'ATACANDO'
                    self.alvo = inimigo
                    return

        # 3. Busca Item (Apenas se for Coletor ou Misto)
        if self.tipo in ['COLETOR', 'MISTO']:
            if not alvo_e_valido(self.alvo) or self.alvo == self.jogador:
                item = self.encontrar_alvo_mais_proximo(self.items_grupo, self.raio_deteccao_item, precisa_dano=False)
                if item:
                    self.estado_logico = 'COLETANDO'
                    self.alvo = item
                    return

        # 4. Default: Seguir Jogador
        if not alvo_e_valido(self.alvo):
            self.estado_logico = 'SEGUINDO'
            self.alvo = self.jogador
    
    def encontrar_alvo_mais_proximo(self, grupo, raio, precisa_dano = False):
        alvos_validos = []
        # Não utilizando raiz quadrada para otimização
        raio_ao_quadrado = raio ** 2
        for s in grupo:
            # distance_squared_to não calcula a raiz quadrada, é muito mais rápido
            dist_prox_sq = self.jogador.posicao.distance_squared_to(s.posicao)
            if dist_prox_sq < raio_ao_quadrado and s.alive():
                if precisa_dano:
                    if hasattr(s, "receber_dano"): alvos_validos.append(s)
                else:
                    alvos_validos.append(s)

        if alvos_validos:
            return min(alvos_validos, key=lambda s: self.posicao.distance_squared_to(s.posicao))
        return None
    
    
    def executar_comportamento(self, delta_time):
        if self.alvo is None: 
            self.alvo = self.jogador

        # Usando distância^2 para otimização
        dist_sq = self.posicao.distance_squared_to(self.alvo.posicao)

        # LÓGICA DE AÇÕES
        if self.estado_logico == 'SEGUINDO':
            vel = self.velocidade_andar
            if dist_sq < self.distancia_seguidor**2:
                self.direcao_movimento = pygame.math.Vector2()
            else:
                self.direcao_movimento = (self.alvo.posicao - self.posicao).normalize()

        elif self.estado_logico == 'ATACANDO':
            vel = self.velocidade_correr
            # LÓGICA DE ÓRBITA:
            self.angulo_orbita += self.velocidade_orbita * delta_time
            offset = pygame.math.Vector2(
                math.cos(self.angulo_orbita) * self.raio_orbita,
                math.sin(self.angulo_orbita) * self.raio_orbita
            )
            ponto_destino = self.alvo.posicao + offset
            
            if self.posicao.distance_squared_to(ponto_destino) > 5**2:
                self.direcao_movimento = (ponto_destino - self.posicao).normalize()
            
            # Dano
            if dist_sq < 60**2:  # Dist ao quadrado
                agora = pygame.time.get_ticks()
                if agora - self.ultimo_dano_tempo > self.cooldown:
                    if hasattr(self.alvo, 'receber_dano'):
                        self.alvo.receber_dano(self.dano)
                    self.ultimo_dano_tempo = agora

        elif self.estado_logico == 'COLETANDO':
            vel = self.velocidade_correr
            self.direcao_movimento = (self.alvo.posicao - self.posicao).normalize()
            if dist_sq < 30**2:  # Dist ao quadrado
                # 1. Guardamos a referência do item
                item_para_coletar = self.alvo 
                
                # 2. Resetamos o alvo do companheiro para o jogador IMEDIATAMENTE
                # Isso evita que ele tente coletar o alvo errado no próximo frame
                self.alvo = self.jogador
                self.estado_logico = 'SEGUINDO'

                # 3. Agora sim, pedimos ao jogador para processar a coleta do ITEM
                if item_para_coletar != self.jogador:
                    self.jogador.coletar_item(item_para_coletar)
                    item_para_coletar.kill()

        # Update de Posição
        if self.direcao_movimento.magnitude() > 0:
            self.posicao += self.direcao_movimento * vel * delta_time

        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        # Update de Direção para Animação
        if self.direcao_movimento.x > 0.1: self.estado_animacao = 'right'
        elif self.direcao_movimento.x < -0.1: self.estado_animacao = 'left'

    def animar(self):
        agora = pygame.time.get_ticks()
        if self.direcao_movimento.magnitude() > 0:    
            if agora - self.ultimo_update_anim > self.velocidade_animacao:
                self.ultimo_update_anim = agora
                self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
                self.image = self.sprites[self.estado_animacao][self.frame_atual]

                
    def update(self, delta_time):
        self.logica_de_decisao()
        self.executar_comportamento(delta_time)
        self.animar()


class Arbitro(Arma):
    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        deve_criar = kwargs.get('criar_sprite', True)
        self.game = game
        self.all_sprites, self.inimigos_grupo, self.item_grupo = grupos
        self.nome = "Árbitro"
        self.descricao = "Um elite aliado que caça inimigos próximos."
        self.dano = 10
        self.sprite_companion = None # Use um nome genérico como 'companion'
        if deve_criar: # Só cria se for solicitado
            self.equipar()

    def equipar(self):
        if not self.sprite_companion:
            # Passamos 'arbiter' para ele buscar na pasta assets/img/arbiter
            self.sprite_companion = Companheiro(
                self.jogador, self.all_sprites, 
                self.inimigos_grupo, self.item_grupo, 
                tipo='CAÇADOR', nome_asset='arbiter' 
            )
            self.sprite_companion.dano = self.dano

    def upgrade(self):
        super().upgrade()
        self.dano += 5
        self.sprite_companion.dano = self.dano
        self.sprite_companion.velocidade_correr += 30
        self.sprite_companion.raio_deteccao_inimigo += 50


    def ver_proximo_upgrade(self):
        return {
            'nivel': self.nivel + 1,
            'dano': self.dano + 5,
            'velocidade': self.sprite_companion.velocidade_correr + 30 if self.sprite_companion else 330,
            'raio_inimigo': self.sprite_companion.raio_deteccao_inimigo + 50 if self.sprite_companion else 450,
        }

    def get_estatisticas_para_exibir(self):
        prox = self.ver_proximo_upgrade()
        
        dano_atual = self.dano
        vel_atual = int(self.sprite_companion.velocidade_correr) if self.sprite_companion else 300
        raio_atual = int(self.sprite_companion.raio_deteccao_inimigo) if self.sprite_companion else 400

        return [
            f"Dano: {dano_atual} -> {prox['dano']}",
            f"Velocidade: {vel_atual} -> {int(prox['velocidade'])}",
            f"Raio de Caça: {raio_atual} -> {prox['raio_inimigo']}",
        ]
    
    def disparar(self):
        pass
    def update(self, delta_time):
        pass

    
class Cortana(Arma):
    """ Cortana: Foca em buscar XP e itens. """
    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        deve_criar = kwargs.get('criar_sprite', True)
        self.all_sprites, self.inimigos_grupo, self.item_grupo = grupos
        self.nome = "Cortana"
        self.descricao = "Busca itens e XP próximos a você, além de conceder um bônus de velocidade."
        self.sprite_companion = None
        if deve_criar: # Só cria se for solicitado
            self.equipar()

    def equipar(self):
        if not self.sprite_companion:
            # Passamos 'cortana' para ele buscar na pasta assets/img/cortana
            self.sprite_companion = Companheiro(
                self.jogador, self.all_sprites, 
                self.inimigos_grupo, self.item_grupo, 
                tipo='COLETOR', nome_asset='cortana'
            )

    def upgrade(self):
        super().upgrade()
        self.sprite_companion.velocidade_andar += 25
        self.sprite_companion.velocidade_correr += 25
        self.sprite_companion.raio_deteccao_item += 50
        self.jogador.velocidade += 10

    def ver_proximo_upgrade(self):
        return {
            'nivel': self.nivel + 1,
            'velocidade': self.sprite_companion.velocidade_andar + 25 if self.sprite_companion else 175,
            'corrida': self.sprite_companion.velocidade_correr + 25 if self.sprite_companion else 225,
            'raio_item': self.sprite_companion.raio_deteccao_item + 50 if self.sprite_companion else 400,
            'player': self.jogador.velocidade + 10
        }

    def get_estatisticas_para_exibir(self):
        prox = self.ver_proximo_upgrade()

        # Se o companion existe, pega o valor dele. Se não, usa o valor base (ex: 150)
        vel_atual = int(self.sprite_companion.velocidade_andar) if self.sprite_companion else 150
        corrida_atual = int(self.sprite_companion.velocidade_correr) if self.sprite_companion else 200
        raio_atual = int(self.sprite_companion.raio_deteccao_item) if self.sprite_companion else 350

        return [
            f"Velocidade Base: {int(vel_atual)} -> {int(prox['velocidade'])}",
            f"Velocidade de Busca: {int(corrida_atual)} -> {prox['corrida']}",
            f"Raio de Busca de Item: {int(raio_atual)} -> {prox['raio_item']}",
            f"Velocidade do Player: {int(self.jogador.velocidade)} -> {int(prox['player'])}"
        ] 
    
    def disparar(self):
        pass
    def update(self, delta_time):
        pass




