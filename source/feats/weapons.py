import pygame
import math
from source.windows.settings import *
from source.player.player import *
from source.feats.assets import ASSETS
from source.feats.baseweapon import *


class RifleAssalto(Arma):
    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = 'Rifle de Assalto'
        self.descricao = """Rifle de cadência elevada"""
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        
        # Carregue a imagem do seu projétil aqui
        self.surface_projetil = pygame.transform.scale(ASSETS['projectiles']['ar'], (24,24))

        # Cria o Cache de Rotações (Dicionário com 360 imagens)
        self.cache_imagens = {ang: pygame.transform.rotate(self.surface_projetil, ang) for ang in range(360)}

        # Status Iniciais
        self.dano = 1
        self.cooldown = 250 
        self.projeteis_por_disparo = 1
        self.velocidade_projetil = 2000
        
    def disparar(self):
        inimigo_alvo = self.encontrar_inimigo_mais_proximo(self.inimigos_grupo)
        if inimigo_alvo and inimigo_alvo.alive():
            direcao_vetor = (inimigo_alvo.posicao - self.jogador.posicao).normalize()
            
            # Calcula o ângulo e converte para número inteiro (0 a 359)
            angulo_exato = math.degrees(math.atan2(-direcao_vetor.y, direcao_vetor.x))
            angulo_int = int(round(angulo_exato)) % 360 # O % 360 garante que fique entre 0 e 359
            
            # Puxa a imagem JÁ PRONTA do cache. Zero custo de processamento!
            imagem_rotacionada = self.cache_imagens[angulo_int]

            # Dispara projéteis múltiplos, se o nível permitir
            for _ in range(self.projeteis_por_disparo):
                Projetil(
                    surface=imagem_rotacionada,  # Passa a imagem JÁ GIRADA
                    posicao_inicial=self.jogador.posicao,
                    velocidade=self.velocidade_projetil,
                    direcao=direcao_vetor,
                    dano=self.dano,
                    grupo_sprites=(self.all_sprites, self.projeteis_grupo),
                    jogador=self.jogador,
                    piercing=1
                )
            return True
        return False

    def upgrade(self):
        super().upgrade() # Aumenta self.nivel
        
        # Aumenta o dano a cada nível
        self.dano += 1
        
        # Reduz o cooldown a cada 2 níveis (disparos mais rápidos)
        if self.nivel % 2 == 0:
            self.cooldown = max(50, self.cooldown - 20)
        
        # Adiciona projéteis extras em níveis específicos
        if self.nivel == 3:
            self.projeteis_por_disparo = 2
        elif self.nivel == 5:
            self.projeteis_por_disparo = 3
        elif self.nivel == 7:
            self.projeteis_por_disparo = 4
        elif self.nivel == 9:
            self.projeteis_por_disparo = 5


    def ver_proximo_upgrade(self):
        prox_nivel = self.nivel + 1
        prox_dano = self.dano + 1
        prox_cooldown = max(50, self.cooldown - 20)
        
        # Lógica para exibir múltiplos projéteis
        if prox_nivel == 3:
            prox_projeteis = self.projeteis_por_disparo + 1
        elif prox_nivel == 5:
            prox_projeteis = self.projeteis_por_disparo + 1
        elif prox_nivel == 7:
            prox_projeteis = self.projeteis_por_disparo + 1
        elif prox_nivel == 9:
            prox_projeteis = self.projeteis_por_disparo + 1
        else:
            prox_projeteis = self.projeteis_por_disparo
        
        return {
            'nivel': prox_nivel,
            'dano': prox_dano,
            'cooldown': prox_cooldown,
            'projeteis': prox_projeteis
        }

    def get_estatisticas_para_exibir(self):
        stats_futuros = self.ver_proximo_upgrade()
        
        stats_formatados = [
            f"Dano: {self.dano} -> {stats_futuros['dano']}",
            f"Cadência de Tiro: {self.cooldown}ms -> {stats_futuros['cooldown']}ms",
            f"Projéteis: {self.projeteis_por_disparo} -> {stats_futuros['projeteis']}"
        ]
        return stats_formatados
    

class Arma_Loop(Arma):
    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.all_sprites, self.grupo_projeteis, self.grupo_inimigos = grupos
        # Sprite
        self.surface_pinpong = pygame.transform.scale(ASSETS['projectiles']['pingpong'], (80,80))

        self.dano = 5
        self.velocidade = 1000
        self.cooldown = 1000
        self.rebatidas = 2
        self.nome = "Bola Calderânica"
        self.descricao = """Capaz de rebater nas paredes!"""
        
    def disparar(self):
        inimigo = self.encontrar_inimigo_mais_proximo(self.grupo_inimigos)        
        if inimigo:
            direcao_tiro = (inimigo.posicao - self.jogador.posicao).normalize()
            Projetil_PingPong(
                surface=self.surface_pinpong, 
                posicao_inicial=self.jogador.posicao,
                velocidade=self.velocidade,
                direcao=direcao_tiro,
                dano=self.dano,
                grupo_sprites=(self.all_sprites, self.grupo_projeteis),
                jogador=self.jogador,
                rebatidas=self.rebatidas
            )
            return True
        return False

    def upgrade(self):
        super().upgrade()
        #a cada 3 niveis fica mais rapido

        self.rebatidas += 1
        self.dano += 2

    def ver_proximo_upgrade(self):
        prox_nivel = self.nivel + 1
        prox_dano = self.dano + 2
        prox_rebatidas = self.rebatidas + 1

        return {
            'nivel': prox_nivel,
            'dano': prox_dano,
            'rebatidas': prox_rebatidas,
        }
    
    def get_estatisticas_para_exibir(self):
        stats_futuros = self.ver_proximo_upgrade()


        stats_formatados = [
            f"Dano: {self.dano} -> {stats_futuros['dano']}",
            f"Rebotes: {self.rebatidas} -> {stats_futuros['rebatidas']}",
        ]

        return stats_formatados
    
class Projetil_PingPong(Projetil):
    def __init__(self, surface, posicao_inicial, velocidade, direcao, dano, grupo_sprites, jogador, rebatidas):
        super().__init__(surface, posicao_inicial, velocidade, direcao, dano, grupo_sprites, jogador, piercing=float('inf'))
        self.rebatidas = rebatidas

    def update(self, delta_time):
        super().update(delta_time)

        # Definimos as bordas
        margem = 10 # Pequena margem de segurança baseada no tamanho da sprite
        borda_esq = self.jogador.posicao.x - (largura_tela / 2) + margem
        borda_dir = self.jogador.posicao.x + (largura_tela / 2) - margem
        borda_topo = self.jogador.posicao.y - (altura_tela / 2) + margem
        borda_baixo = self.jogador.posicao.y + (altura_tela / 2) - margem

        # Checa colisão Eixo X
        if self.posicao.x <= borda_esq:
            self.posicao.x = borda_esq # FORÇA POSIÇÃO
            self.direcao.x *= -1
            self.rebatidas -= 1
            self.inimigos_atingidos.clear() # Limpa para dar dano de novo após rebater

        elif self.posicao.x >= borda_dir:
            self.posicao.x = borda_dir # FORÇA POSIÇÃO
            self.direcao.x *= -1
            self.rebatidas -= 1
            self.inimigos_atingidos.clear()

        # Checa colisão Eixo Y
        if self.posicao.y <= borda_topo:
            self.posicao.y = borda_topo # FORÇA POSIÇÃO
            self.direcao.y *= -1
            self.rebatidas -= 1
            self.inimigos_atingidos.clear()

        elif self.posicao.y >= borda_baixo:
            self.posicao.y = borda_baixo # FORÇA POSIÇÃO
            self.direcao.y *= -1
            self.rebatidas -= 1
            self.inimigos_atingidos.clear()

        if self.rebatidas < 0: # < 0 para garantir que a última rebatida ainda viaje
            self.kill()


class ArmaLista(Arma):
    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.game = game

        # Sprite
        self.surface_listas = pygame.transform.scale(ASSETS['projectiles']['lista'], (45, 80))

        # Específicos da arma
        self.nome = "Ciclo de Lâminas"
        self.descricao = "Protegem o jogador!"
        self.num_listas = 1
        self.dano = 15
        self.cooldown = 6000
        self.duracao = 5000    
        self.velocidade_rotacao = 120 
        self.distancia_orbita = 140    

    def disparar(self):
        angulo_step = 360 / self.num_listas
        for i in range(self.num_listas):
            Projetil_Lista(
                surface=self.surface_listas, 
                posicao_inicial=self.jogador.posicao,
                velocidade=0,
                direcao=pygame.math.Vector2(0,0),
                dano=self.dano,
                grupo_sprites=(self.all_sprites, self.projeteis_grupo),
                jogador=self.jogador,
                angulo_inicial=i * angulo_step,
                duracao=self.duracao,
                velocidade_rotacao=self.velocidade_rotacao, 
                distancia_orbita=self.distancia_orbita
            )
        return True
    
    def upgrade(self):
        super().upgrade()

        self.velocidade_rotacao += 10
        self.distancia_orbita += 10
        self.dano += 5
        if self.nivel % 2 == 0:
            self.num_listas += 1

    def ver_proximo_upgrade(self):
        prox_nivel = self.nivel + 1
        prox_dano = self.dano + 5
        prox_velocidade_rotacao = self.velocidade_rotacao + 10
        prox_orbita = self.distancia_orbita + 10
        if prox_nivel % 2 == 0:
            prox_listas = self.num_listas + 1
        else:
            prox_listas = self.num_listas

        return {
            'nivel': prox_nivel,
            'dano': prox_dano,
            'velocidade_rotacao': prox_velocidade_rotacao,
            'num_listas': prox_listas,
            'orbita' : prox_orbita
        }
    def get_estatisticas_para_exibir(self):
        stats_futuros = self.ver_proximo_upgrade()

        stats_formatados = [
            f"Dano: {self.dano} -> {stats_futuros['dano']}",
            f"Velocidade Angular: {self.velocidade_rotacao}°/s-> {stats_futuros['velocidade_rotacao']}°/s",
            f"Num. Listas: {self.num_listas} -> {stats_futuros['num_listas']}",
            f"Raio da Órbita: {self.distancia_orbita} -> {stats_futuros['orbita']}"
        ]

        return stats_formatados    

class Projetil_Lista(Projetil):
    def __init__(self, surface, posicao_inicial, velocidade, direcao, dano, grupo_sprites, jogador, angulo_inicial, duracao, velocidade_rotacao, distancia_orbita):
        super().__init__(surface, posicao_inicial, velocidade, direcao, dano, grupo_sprites, jogador, piercing=float('inf'))
        self.angulo = angulo_inicial  # Posição angular inicial no círculo
        self.distancia_orbita = distancia_orbita
        self.velocidade_rotacao = velocidade_rotacao #graus por segundo
        self.tempo_criacao = pygame.time.get_ticks()
        self.duracao = duracao
        
    def update(self, delta_time):
        # Calcula a rotação ao redor do jogador
        self.angulo += self.velocidade_rotacao * delta_time
        deslocamento = pygame.math.Vector2(
            math.cos(math.radians(self.angulo)), 
            math.sin(math.radians(self.angulo))
        ) * self.distancia_orbita

        self.posicao = self.jogador.posicao + deslocamento
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        if pygame.time.get_ticks() - self.tempo_criacao > self.duracao:
            self.kill()

class Dicionario_Divino(Arma):
    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs) 
        self.all_sprites, self.auras_grupos, self.inimigos_grupo = grupos
        # Status Iniciais da Arma
        self.nome = "Dicionário Divino"
        self.descricao = "Causa dano por segundo"
        self.dano_por_segundo = 1
        self.raio = 120
        self.cooldown = float('inf') 
        self.area_de_dano = None

    def equipar(self):
        if self.area_de_dano is None:
            self.area_de_dano = Projetil_Area(
                jogador=self.jogador,
                raio=self.raio,
                dano_por_segundo=self.dano_por_segundo,
                grupos=(self.all_sprites, self.auras_grupos)
            )

    def disparar(self):
        return False
    
    def upgrade(self):
        super().upgrade() # Aumenta self.nivel
        self.dano_por_segundo += 1
        self.raio += 15

        if self.area_de_dano:
            self.area_de_dano.atualizar_stats(self.raio, self.dano_por_segundo)

    def ver_proximo_upgrade(self):
        return {
            'nivel': self.nivel + 1,
            'dano_por_segundo': self.dano_por_segundo + 1,
            'raio': self.raio + 15
        }

    def get_estatisticas_para_exibir(self):
        prox = self.ver_proximo_upgrade()
        return [
            f"Dano/s: {self.dano_por_segundo:.2f} -> {prox['dano_por_segundo']:.2f}",
            f"Raio: {self.raio} -> {prox['raio']}"
        ] 
    
    
class Projetil_Area(pygame.sprite.Sprite):
    def __init__(self, jogador, raio, dano_por_segundo, grupos):
        super().__init__(grupos)
        self.jogador = jogador
        
        # Atributos exigidos pelo seu CollisionManager (Item 5)
        self.raio = raio
        self.dano_por_segundo = dano_por_segundo
        
        # Visual: Criamos a superfície e a máscara de colisão radial
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.jogador.posicao)
        
        # O Pygame usa o atributo 'radius' para o collide_circle
        self.radius = self.raio 
        
        self.desenhar_aura()

    def desenhar_aura(self):
        """Desenha o efeito visual da aura"""
        self.image.fill((0, 0, 0, 0)) # Limpa
        # Desenha um círculo amarelo suave
        pygame.draw.circle(self.image, (255, 255, 0, 30), (self.raio, self.raio), self.raio)
        # Desenha uma borda leve para dar definição
        pygame.draw.circle(self.image, (255, 255, 0, 100), (self.raio, self.raio), self.raio, 2)

    def atualizar_stats(self, novo_raio, novo_dano):
        """Chamado pelo upgrade da Arma"""
        self.raio = novo_raio
        self.radius = self.raio # Atualiza para o motor de colisão
        self.dano_por_segundo = novo_dano
        
        # Redimensiona a imagem
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.jogador.posicao)
        self.desenhar_aura()

    def update(self, delta_time):
        # A aura apenas segue o jogador. 
        # O dano é aplicado pelo CollisionManager.update()
        self.rect.center = self.jogador.posicao


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
        self.descricao = "Busca itens e XP próximos para você."
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

    def ver_proximo_upgrade(self):
        return {
            'nivel': self.nivel + 1,
            'velocidade': self.sprite_companion.velocidade_andar + 25 if self.sprite_companion else 175,
            'corrida': self.sprite_companion.velocidade_correr + 25 if self.sprite_companion else 225,
            'raio_item': self.sprite_companion.raio_deteccao_item + 50 if self.sprite_companion else 400
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
            f"Raio de Busca de Item: {int(raio_atual)} -> {prox['raio_item']}"
        ] 
    
    def disparar(self):
        pass
    def update(self, delta_time):
        pass


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
        distancia_jogador = self.posicao.distance_to(self.jogador.posicao)
        # 1. Se estiver muito longe do jogador, FORÇA a volta (Independente do alvo)
        raio_maximo = self.raio_deteccao_inimigo if self.tipo == 'CAÇADOR' else self.raio_deteccao_item
        if distancia_jogador > raio_maximo:
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
        for s in grupo:
            dist_prox = self.jogador.posicao.distance_to(s.posicao) # Avalia distância a partir do JOGADOR
            if dist_prox < raio and s.alive():
                if precisa_dano:
                    if hasattr(s, "receber_dano"): alvos_validos.append(s)
                else:
                    alvos_validos.append(s)

        if alvos_validos:
            return min(alvos_validos, key=lambda s: self.posicao.distance_to(s.posicao))
        return None
    
    
    def executar_comportamento(self, delta_time):
        if self.alvo is None: 
            self.alvo = self.jogador

        distancia = self.posicao.distance_to(self.alvo.posicao)

        # LÓGICA DE AÇÕES
        if self.estado_logico == 'SEGUINDO':
            vel = self.velocidade_andar
            if distancia < self.distancia_seguidor:
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
            
            if self.posicao.distance_to(ponto_destino) > 5:
                self.direcao_movimento = (ponto_destino - self.posicao).normalize()
            
            # Dano
            if distancia < 60:
                agora = pygame.time.get_ticks()
                if agora - self.ultimo_dano_tempo > self.cooldown:
                    if hasattr(self.alvo, 'receber_dano'):
                        self.alvo.receber_dano(self.dano)
                    self.ultimo_dano_tempo = agora

        elif self.estado_logico == 'COLETANDO':
            vel = self.velocidade_correr
            self.direcao_movimento = (self.alvo.posicao - self.posicao).normalize()
            if distancia < 30:
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

