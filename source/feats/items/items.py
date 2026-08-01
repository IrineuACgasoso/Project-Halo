"""
items/items.py

A classe Items em si: dados, física de queda, e a lógica de "o que cada
item faz quando é coletado". Todo o desenho/cache/halo vive em draw.py —
esse arquivo não desenha nada, só orquestra.
"""

import random
import pygame

from . import draw
from source.systems.entitymanager import entity_manager


class Items(pygame.sprite.Sprite):
    TIPOS_XP = draw.TIPOS_XP
    TAMANHOS = draw.TAMANHOS

    def __init__(self, posicao, tipo, grupos, id_arma_alvo=None):
        super().__init__(grupos)

        self.tipo = tipo
        self.tamanho = self.TAMANHOS.get(tipo, (16, 16))

        # Se for upgrade e ninguém especificou qual arma, sorteia aqui mesmo,
        # na criação do item — assim quem chama spawn_drop não precisa saber
        # nada sobre isso, é 100% automático.
        if tipo == 'upgrade' and id_arma_alvo is None:
            id_arma_alvo = self._sortear_arma_do_jogador()

        self.id_arma_alvo = id_arma_alvo

        entrada_cache, self._chave_cache = draw.obter_imagem(tipo, self.tamanho, id_arma=id_arma_alvo)
        self.image = draw.frame_inicial(entrada_cache)

        self.rect = self.image.get_rect(center=posicao)
        self.posicao = pygame.math.Vector2(posicao)
        self.posicao_final_y = self.posicao.y

        self.velocidade = 180
        self.gravidade = 500
        self.dropping = True

        self.coletado = False
        self._fase_glow = random.uniform(0, 6.283)

    @staticmethod
    def _sortear_arma_do_jogador():
        """Escolhe aleatoriamente uma arma dentre as que o jogador já possui."""
        from source.systems.entitymanager import entity_manager
        player = entity_manager.player
        if not player or not player.armas:
            return None
        return random.choice(sorted(player.armas.keys()))

    # ------------------------------------------------------------------ #
    # SPAWN INTELIGENTE POR KWARGS
    # ------------------------------------------------------------------ #
    @classmethod
    def spawn_drop(cls, posicao, grupos, id_arma_alvo=None, **kwargs):
        """
        Gera drops dinamicamente processando múltiplos tipos de itens via kwargs.
        
        Exemplos de assinaturas aceitas:
            Quantidade Fixa:    exp_shard = (1, 100, 100)
            Quantidade Variável: big_shard = ((1, 2, 3), (70, 20, 10), 100)
        """
        for tipo, config in kwargs.items():
            # Garante que recebemos uma estrutura válida de configuração
            if not isinstance(config, (tuple, list)) or len(config) < 3:
                continue

            qtd_final = 0

            # ─── CASO 1: QUANTIDADE VARIÁVEL — ex: ((1, 2), (90, 10), 100) ───
            if isinstance(config[0], (tuple, list)):
                qtds = list(config[0])
                probs = [float(p) for p in config[1]]
                escala = float(config[2])

                # Sistema Inteligente: Se a soma das chances for menor que a escala,
                # a diferença é injetada na opção de maior probabilidade (o primeiro/maior).
                soma_probs = sum(probs)
                if soma_probs < escala:
                    sobra = escala - soma_probs
                    idx_max = probs.index(max(probs))
                    probs[idx_max] += sobra

                # Sorteio por distribuição cumulativa (Roleta)
                roll = random.uniform(0, escala)
                acumulado = 0
                for qtd, prob in zip(qtds, probs):
                    acumulado += prob
                    if roll <= acumulado:
                        qtd_final = qtd
                        break

            # ─── CASO 2: QUANTIDADE FIXA — ex: (1, 0.1, 100) ───
            else:
                qtd_base = config[0]
                prob = float(config[1])
                escala = float(config[2])

                roll = random.uniform(0, escala)
                if roll <= prob:
                    qtd_final = qtd_base

            # ─── EXECUÇÃO DO SPAWN FÍSICO ───
            if qtd_final > 0:
                for _ in range(int(qtd_final)):
                    # Aplica um pequeno espalhamento circular para os itens não nascerem colados
                    offset = pygame.math.Vector2(random.randint(-25, 25), random.randint(-25, 25))
                    cls(posicao + offset, tipo, grupos, id_arma_alvo=id_arma_alvo)

    # ------------------------------------------------------------------ #
    # UPDATE
    # ------------------------------------------------------------------ #
    def update(self, delta_time):
        if self.dropping:
            self.velocidade -= self.gravidade * delta_time
            self.posicao.y -= self.velocidade * delta_time

            if self.posicao.y >= self.posicao_final_y:
                self.posicao.y = self.posicao_final_y
                self.dropping = False

            self.rect.centery = round(self.posicao.y)

        agora = pygame.time.get_ticks()
        novo_frame = draw.atualizar_frame_pulsando(self._chave_cache, self._fase_glow, agora)
        if novo_frame is not None:
            self.image = novo_frame

    # ------------------------------------------------------------------ #
    # COLETA
    # ------------------------------------------------------------------ #
    def coletar(self, player):
        if self.coletado:
            return False
        self.coletado = True

        houve_level_up = self._aplicar_efeito(player)
        draw.emitir_particulas_coleta(self.rect.center, self.tipo, entity_manager.all_sprites)
        self.kill()

        return houve_level_up

    def _aplicar_efeito(self, player):
        houve_level_up = False

        if self.tipo in player.coletaveis:
            player.coletaveis[self.tipo] += 1

        if not hasattr(player, 'pontuacao'):
            player.pontuacao = 0

        if self.tipo == 'exp_shard':
            houve_level_up = bool(player.ganhar_xp(10))
            player.pontuacao += 10
            
        elif self.tipo == 'big_shard':
            houve_level_up = bool(player.ganhar_xp(50))
            player.pontuacao += 50
            
        elif self.tipo == 'life_orb':
            player.curar(player.vida_maxima)
            player.pontuacao += 100
            
        elif self.tipo == 'upgrade':
            player.pontuacao += 200
            player.ativar_upgrade_forcado(id_forcado=self.id_arma_alvo)

        return houve_level_up