import pygame
import math
import random
from source.windows.settings import *
from source.player.player import *
from source.feats.assets import ASSETS
from source.feats.data import COMPANION_DATA
from source.feats.projetil import BurstRifle
from source.feats.baseweapon import *


class Companheiro(pygame.sprite.Sprite):
    def __init__(self, jogador, grupos, inimigos_grupo, item_grupo, nome_asset):
        super().__init__(grupos)
        # Referências básicas
        self.jogador = jogador
        self.inimigos_grupo = inimigos_grupo
        self.items_grupo = item_grupo
        self.nome_asset = nome_asset

        # Referência para a arma pai (importante para os Marines e liberar itens)
        self.arma_parent = None

        # Carrega tudo via função dedicada
        self.configurar_atributos()
        self.carregar_assets()
        self.set_posicao_inicial()


    def configurar_atributos(self):
        """Busca no dicionário COMPANION_DATA e aplica os status"""
        config = COMPANION_DATA.get(self.nome_asset, COMPANION_DATA['marine'])
        self.tipo = config['tipo']
        
        # Aplica todos os itens do dict como atributos da classe automaticamente
        for chave, valor in config['stats'].items():
            setattr(self, chave, valor)

        if self.pode_atirar:
            self.ultimo_tiro = 0

        # Inicializadores lógicos obrigatórios
        self.estado_logico = 'SEGUINDO'
        self.alvo = None
        self.direcao_movimento = pygame.math.Vector2()
        self.frame_atual = 0
        self.ultimo_update_anim = pygame.time.get_ticks()

        # Estado para vagabundeio aleatório no SEGUINDO
        self.ponto_vagabundeio = None
        self.tempo_proximo_vagabundeio = 0

    def _sortear_ponto_vagabundeio(self):
        """Escolhe um ponto aleatório dentro do raio de vagabundeio do jogador."""
        self.raio_vaga = self.distancia_maxima_retorno * 0.75
        angulo = random.uniform(0, 2 * math.pi)
        dist = random.uniform(self.raio_vaga * 0.1, self.raio_vaga)
        return pygame.math.Vector2(
            self.jogador.posicao.x + math.cos(angulo) * dist,
            self.jogador.posicao.y + math.sin(angulo) * dist
        )


    def carregar_assets(self):
        """Cuida de toda a parte gráfica"""
        self.sprites = {
            'right': ASSETS['buddies'][self.nome_asset],
            'left': [pygame.transform.flip(s, True, False) for s in ASSETS['buddies'][self.nome_asset]]
        }
        self.estado_animacao = 'right'
        self.image = self.sprites[self.estado_animacao][self.frame_atual]


    def set_posicao_inicial(self):
        """Define o local de nascimento ao redor do jogador"""
        # Gera um ângulo aleatório (0 a 360 graus em radianos)
        angulo = random.uniform(0, 2 * math.pi)
        
        # Define um raio de spawn (ex: 100 pixels de distância do player)
        raio_spawn = 100 
        
        # Calcula o offset X e Y usando trigonometria
        offset_x = math.cos(angulo) * raio_spawn
        offset_y = math.sin(angulo) * raio_spawn
        
        # Define a posição baseada na posição atual do jogador
        self.posicao = pygame.math.Vector2(
            self.jogador.posicao.x + offset_x, 
            self.jogador.posicao.y + offset_y
        )
        
        # Atualiza o rect para o Pygame saber onde desenhar
        self.rect = self.image.get_rect(center=self.posicao)
        
    def logica_de_decisao(self):
        # Função auxiliar interna para checar se o alvo atual ainda é válido
        def alvo_e_valido(alvo):
            if alvo is None: return False
            if alvo == self.jogador: return True
            return hasattr(alvo, 'alive') and alvo.alive()
        
        # Usando a distância ao quadrado para evitar o cálculo da raiz
        dist_sq_jogador = self.posicao.distance_squared_to(self.jogador.posicao)

        if dist_sq_jogador > self.distancia_maxima_retorno**2:
            # Se já está coletando, deixa terminar antes de forçar retorno.
            # Depois que coletar, o estado volta a SEGUINDO e a checagem funciona normalmente.
            if self.estado_logico == 'COLETANDO':
                return
            self.liberar_item_atual()
            self.estado_logico = 'SEGUINDO'
            self.alvo = self.jogador
            return
        
        
        
        # Busca Inimigo (Apenas se for Caçador ou Misto)
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
            # Se o alvo atual não é item, busca um novo
            if self.estado_logico != 'COLETANDO':
                for item in self.items_grupo:
                    # Verifica se o item está no raio E se não está reservado por outro Marine
                    if item.alive() and self.posicao.distance_squared_to(item.posicao) < self.raio_deteccao_item**2:
                        # Verifica se a arma existe E se ela tem a lista de reservas (evita o erro de NoneType e AttributeError)
                        if getattr(self, 'arma_parent', None) and hasattr(self.arma_parent, 'itens_reservados'):
                            if item not in self.arma_parent.itens_reservados:
                                self.arma_parent.itens_reservados.add(item)
                                self.alvo = item
                                self.estado_logico = 'COLETANDO'
                                return

        # 4. Default: Seguir Jogador
        if not alvo_e_valido(self.alvo):
            self.estado_logico = 'SEGUINDO'
            self.alvo = self.jogador
    

    def liberar_item_atual(self):
        """ Remove o item da lista de reservas caso o marine mude de alvo ou morra """
        if self.estado_logico == 'COLETANDO' and self.alvo:
            if self.arma_parent is not None and hasattr(self.arma_parent, 'itens_reservados'):
                if self.alvo in self.arma_parent.itens_reservados:
                    self.arma_parent.itens_reservados.remove(self.alvo)
    
    def encontrar_alvo_mais_proximo(self, grupo, raio, precisa_dano = False):
        alvos_validos = []
        # Não utilizando raiz quadrada para otimização
        raio_ao_quadrado = raio ** 2
        for s in grupo:
            # distance_squared_to não calcula a raiz quadrada, é muito mais rápido
            dist_prox_sq = self.posicao.distance_squared_to(s.posicao)
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
            agora = pygame.time.get_ticks()

            # Sorteia novo ponto se: não tem ponto, chegou perto o suficiente,
            # o timer expirou, ou o ponto ficou fora do raio (jogador se moveu)
            precisa_novo_ponto = (
                self.ponto_vagabundeio is None
                or self.posicao.distance_squared_to(self.ponto_vagabundeio) < 25**2
                or agora > self.tempo_proximo_vagabundeio
                or self.jogador.posicao.distance_squared_to(self.ponto_vagabundeio) > self.raio_vaga**2
            )
            if precisa_novo_ponto:
                self.ponto_vagabundeio = self._sortear_ponto_vagabundeio()
                self.tempo_proximo_vagabundeio = agora + random.randint(2500, 5000)
 
            if self.posicao.distance_squared_to(self.ponto_vagabundeio) > 25**2:
                self.direcao_movimento = (self.ponto_vagabundeio - self.posicao).normalize()
            else:
                self.direcao_movimento = pygame.math.Vector2()


        elif self.estado_logico == 'ATACANDO':
            vel = self.velocidade_correr
            # LÓGICA DO ATIRADOR
            if self.pode_atirar:
                agora = pygame.time.get_ticks()
                
                if dist_sq < self.range_tiro**2:
                    self.direcao_movimento = pygame.math.Vector2(0,0) # Fica parado

                    if agora - self.ultimo_tiro > self.cooldown_tiro:
                        self.atirar()
                        self.ultimo_tiro = agora
                else:
                    # 2. Se o inimigo fugir do range, ele caminha em direção a ele
                    self.direcao_movimento = (self.alvo.posicao - self.posicao).normalize()

            else:
                # Lógica de órbita para lutadores corpo a corpo
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
                # Invalida ponto de vagabundeio para sortear um novo logo após coletar
                self.ponto_vagabundeio = None

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

    def atirar(self):
        direcao = (self.alvo.posicao - self.posicao).normalize()
        
        # Criando o tiro como se fosse do jogador, mas saindo do Marine
        BurstRifle(
            posicao_inicial=self.posicao.copy(),
            grupos=(self.groups()[0],), # Usa o primeiro grupo que ele pertence
            jogador=self.jogador,
            game=self.jogador.game,
            dono='PLAYER', # Importante para não acertar o mestre!
            tamanho=(24, 24),
            dano=self.dano,
            velocidade=700,
            direcao_spread=direcao
        )

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


#==================================================================================================

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
                'arbiter' 
            )
            self.sprite_companion.dano = self.dano
            self.sprite_companion.arma_parent = self

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
            'velocidade': self.sprite_companion.velocidade_correr + 30 if self.sprite_companion else 350,
            'raio_inimigo': self.sprite_companion.raio_deteccao_inimigo + 50 if self.sprite_companion else 500,
        }

    def get_estatisticas_para_exibir(self):
        prox = self.ver_proximo_upgrade()
        
        dano_atual = self.dano
        vel_atual = int(self.sprite_companion.velocidade_correr) if self.sprite_companion else 320
        raio_atual = int(self.sprite_companion.raio_deteccao_inimigo) if self.sprite_companion else 450

        return [
            f"Dano: {dano_atual} -> {prox['dano']}",
            f"Velocidade: {vel_atual} -> {int(prox['velocidade'])}",
            f"Raio de Caça: {raio_atual} -> {prox['raio_inimigo']}",
        ]
    
    def disparar(self): pass
    def update(self, delta_time): pass


#===========================================================================================================
    
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
        self.itens_reservados = set()
        if deve_criar: # Só cria se for solicitado
            self.equipar()

    def equipar(self):
        if not self.sprite_companion:
            # Passamos 'cortana' para ele buscar na pasta assets/img/cortana
            self.sprite_companion = Companheiro(
                self.jogador, self.all_sprites, 
                self.inimigos_grupo, self.item_grupo, 
                'cortana'
            )
            self.sprite_companion.arma_parent = self

    def upgrade(self):
        super().upgrade()
        self.sprite_companion.velocidade_andar += 25
        self.sprite_companion.velocidade_correr += 25
        self.sprite_companion.raio_deteccao_item += 50
        self.jogador.velocidade += 10

    def ver_proximo_upgrade(self):
        return {
            'nivel': self.nivel + 1,
            'velocidade': self.sprite_companion.velocidade_andar + 25 if self.sprite_companion else 205,
            'corrida': self.sprite_companion.velocidade_correr + 25 if self.sprite_companion else 305,
            'raio_item': self.sprite_companion.raio_deteccao_item + 50 if self.sprite_companion else 450,
            'player': self.jogador.velocidade + 10
        }

    def get_estatisticas_para_exibir(self):
        prox = self.ver_proximo_upgrade()

        # Se o companion existe, pega o valor dele. Se não, usa o valor base (ex: 150)
        vel_atual = int(self.sprite_companion.velocidade_andar) if self.sprite_companion else 180
        corrida_atual = int(self.sprite_companion.velocidade_correr) if self.sprite_companion else 280
        raio_atual = int(self.sprite_companion.raio_deteccao_item) if self.sprite_companion else 400

        return [
            f"Velocidade Base: {int(vel_atual)} -> {int(prox['velocidade'])}",
            f"Velocidade de Busca: {int(corrida_atual)} -> {prox['corrida']}",
            f"Raio de Busca de Item: {int(raio_atual)} -> {prox['raio_item']}",
            f"Velocidade do Player: {int(self.jogador.velocidade)} -> {int(prox['player'])}"
        ] 
    
    def disparar(self): pass
    def update(self, delta_time): pass


#===========================================================================================================

class Marine(Arma):
    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.all_sprites, self.inimigos_grupo, self.item_grupo = grupos
        self.sprite_companion = None

        self.itens_reservados = set() # Itens que já têm um Marine indo buscar
        self.companions = [] # Lista para guardar todos os marines
        self.nome = "UNSC Marine"
        self.descricao = "Leal soldado que auxilia coletando itens e atacando inimigos."
        self.dano = 1

        if kwargs.get('criar_sprite', True):
            self.adicionar_soldado()

    def equipar(self):
        if not self.companions: # Se a lista estiver vazia, adiciona o primeiro
            self.adicionar_soldado()
            # Aponta o sprite_companion para o primeiro da lista 
            # apenas para o resto do motor do jogo não bugar
            self.sprite_companion = self.companions[0]
            
    def adicionar_soldado(self):
        novo_marine = Companheiro(
            self.jogador, self.all_sprites, 
            self.inimigos_grupo, self.item_grupo, 
            'marine' 
        )
        novo_marine.arma_parent = self # Referência para gerenciar reservas
        novo_marine.pode_atirar = True
        novo_marine.dano = self.dano
        # Dá um offset para eles não ficarem um em cima do outro
        novo_marine.angulo_orbita = len(self.companions) * (math.pi / 2)
        self.companions.append(novo_marine)

    def upgrade(self):
        super().upgrade()
        # Lógica de escala
        self.dano += 1

        novo_cooldown = max(500, self.cooldown_tiro - 20)

        
        # Adiciona novo soldado em níveis específicos
        if self.nivel in [3, 5, 7]:
            self.adicionar_soldado()

        # Atualiza status de TODOS os soldados ativos
        for m in self.companions:
            m.dano = self.dano
            m.velocidade_correr += 15
            m.range_tiro += 30
            m.raio_deteccao_inimigo += 40
            m.raio_deteccao_item += 30
            m.cooldown_tiro = novo_cooldown
            


    def ver_proximo_upgrade(self):
        # Pega um marine como base para as stats atuais, ou valores padrão
        base = self.companions[0] if self.companions else None
        
        return {
            'nivel': self.nivel + 1,
            'dano': self.dano + 1,
            'soldados': len(self.companions) + (1 if (self.nivel + 1) in [3, 5, 7] else 0),
            'velocidade': (base.velocidade_correr + 15) if base else 195,
            'range': (base.range_tiro + 30) if base else 430,
            'deteccao_inimigo': (base.raio_deteccao_inimigo + 40) if base else 490,
            'deteccao_item': (base.raio_deteccao_item + 30) if base else 280,
            'attack_speed': (base.cooldown_tiro - 20) if base else 980
        }

    def get_estatisticas_para_exibir(self):
        prox = self.ver_proximo_upgrade()
        base = self.companions[0] if self.companions else None
        
        stats = [
            f"Dano: {self.dano} -> {prox['dano']}",
            f"Soldados: {len(self.companions)} -> {prox['soldados']}"
        ]
        
        if base:
            stats.append(f"Velocidade: {int(base.velocidade_correr)} -> {int(prox['velocidade'])}")
            stats.append(f"Alcance: {int(base.range_tiro)} -> {int(prox['range'])}")
            stats.append(f"Detecção de Inimigos: {int(base.raio_deteccao_inimigo)} -> {int(prox['deteccao_inimigo'])}")
            stats.append(f"Detecção de Itens: {int(base.raio_deteccao_item)} -> {int(prox['deteccao_item'])}")
            stats.append(f"Velocidade de Ataque: {int(base.cooldown_tiro)} ms -> {int(prox['attack_speed'])} ms")

            
        return stats
    
    def disparar(self): pass
    def update(self, delta_time): pass




