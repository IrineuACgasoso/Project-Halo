import pygame
import math
import random
from source.windows.settings import *
from source.feats.assets import ASSETS
from source.data.weapon_data import COMPANION_DATA
from source.feats.projetil import BurstRifle, HeavyBurst


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
        self.tipo = config.tipo

        # Lê 'value' de cada stat — ignora atributos virtuais (_prefixo)
        for attr, meta in config.stats.items():
            if not attr.startswith('_') and meta.value is not None:
                setattr(self, attr, meta.value)

        if self.pode_atirar:
            self.ultimo_tiro_burst = 0
            self.ultimo_tiro_sniper = 0

        self.estado_logico  = 'SEGUINDO'
        self.alvo           = None
        self.direcao_movimento = pygame.math.Vector2()
        self.frame_atual    = 0
        self.ultimo_update_anim = pygame.time.get_ticks()
        self.raio_vaga      = self.distancia_maxima_retorno * 0.75
        self.ponto_vagabundeio = None
        self.tempo_proximo_vagabundeio = 0


    def _sortear_ponto_vagabundeio(self):
        """Escolhe um ponto aleatório dentro do raio de vagabundeio do jogador."""
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
            if self.estado_logico != 'COLETANDO':
                itens_livres = [i for i in self.items_grupo 
                                if i.alive() and (
                                    self.arma_parent is None or 
                                    i not in getattr(self.arma_parent, 'itens_reservados', set())
                                )]
                item = self.encontrar_alvo_mais_proximo(itens_livres, self.raio_deteccao_item)
                if item:
                    if self.arma_parent and hasattr(self.arma_parent, 'itens_reservados'):
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

                    disparo = self.decidir_disparo(dist_sq, agora)
                    if disparo:
                        self.atirar(**disparo)
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
            if not self.alvo.alive():
                self.liberar_item_atual()
                self.estado_logico = 'SEGUINDO'
                self.alvo = self.jogador
                self.ponto_vagabundeio = None
                return
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

                # 3. Agora sim, pedimos a classe para processar a coleta do ITEM
                if item_para_coletar != self.jogador:
                    item_para_coletar.coletar(self.jogador)

        # Update de Posição
        if self.direcao_movimento.magnitude() > 0:
            self.posicao += self.direcao_movimento * vel * delta_time

        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        # Update de Direção para Animação
        if self.direcao_movimento.x > 0.1: self.estado_animacao = 'right'
        elif self.direcao_movimento.x < -0.1: self.estado_animacao = 'left'

    def decidir_disparo(self, dist_sq, agora):
        """
        Decide o que atirar com base em cooldown/alcance.
        Retorna um dict de kwargs para atirar(), ou None se não deve atirar agora.
        Comportamento padrão: rajada de perto, sniper de longe (usado pelo Marine).
        Subclasses (ex: CompanheiroNoble) podem sobrescrever para ter mecânicas próprias.
        """
        if agora - self.ultimo_tiro_burst > self.cooldown_tiro_burst and dist_sq < self.range_rifle**2:
            self.ultimo_tiro_burst = agora
            return dict(
                projetil_cls=BurstRifle,
                dano=self.dano_burst,
                velocidade=700,
                tamanho=(24, 24),
            )

        if agora - self.ultimo_tiro_sniper > self.cooldown_tiro_sniper and dist_sq < self.range_sniper**2:
            self.ultimo_tiro_sniper = agora
            return dict(
                projetil_cls=HeavyBurst,
                dano=self.dano_sniper,
                velocidade=1500,
                tamanho=(96, 28),
            )

        return None

    def atirar(self, projetil_cls, dano, velocidade, tamanho, direcao=None, posicao_inicial=None, **extra_kwargs):
        """
        Dispara um projétil genérico a partir do companheiro.
        projetil_cls: a classe do projétil a instanciar (BurstRifle, HeavyBurst, etc.)
        extra_kwargs: qualquer parâmetro adicional aceito pela classe do projétil.
        """
        if direcao is None:
            direcao = (self.alvo.posicao - self.posicao).normalize()
        if posicao_inicial is None:
            posicao_inicial = self.posicao.copy()

        projetil_cls(
            posicao_inicial=posicao_inicial,
            grupos=(self.jogador.game.all_sprites,), # Usa o primeiro grupo que ele pertence
            jogador=self.jogador,
            game=self.jogador.game,
            dono='PLAYER', # Importante para não acertar o mestre!
            tamanho=tamanho,
            dano=dano,
            velocidade=velocidade,
            direcao_spread=direcao,
            **extra_kwargs
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