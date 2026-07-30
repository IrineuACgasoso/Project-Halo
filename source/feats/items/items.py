



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
        """Escolhe aleatoriamente uma arma dentre as que o jogador já possui,
        pra saber qual ícone mostrar no drop e qual arma upar na coleta.
        Retorna None se o jogador ainda não tiver nenhuma arma (nesse caso
        o item cai no ícone de fallback e, na coleta, vira um level_up comum)."""
        from source.systems.entitymanager import entity_manager
        player = entity_manager.player
        if not player or not player.armas:
            return None
        return random.choice(sorted(player.armas.keys()))

    # ------------------------------------------------------------------ #
    # SPAWN
    # ------------------------------------------------------------------ #
    @classmethod
    def spawn_drop(cls, posicao, grupos, tipo, qtd, probabilidade, id_arma_alvo=None):
        """Inimigo só chama: Items.spawn_drop(pos, grupos, 'upgrade', qtd, %)
        — sem se preocupar com qual arma vai upar, isso é decidido sozinho
        dentro do __init__ quando tipo == 'upgrade'."""
        if random.randint(1, 100) <= probabilidade:
            for _ in range(qtd):
                offset = pygame.math.Vector2(random.randint(-30, 30), random.randint(-30, 30))
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
    # COLETA — Items decide o que fazer consigo mesma; o Player só recebe o resultado
    # ------------------------------------------------------------------ #
    def coletar(self, player):
        """
        Chamado quando o player pega o item (ex: pelo CollisionManager).
        Aplica o efeito correspondente no player, dispara as partículas
        de despawn e se remove do jogo.

        Retorna True se a coleta causou level up.
        """
        if self.coletado:
            return False
        self.coletado = True

        houve_level_up = self._aplicar_efeito(player)
        draw.emitir_particulas_coleta(self.rect.center, self.tipo, entity_manager.all_sprites)
        self.kill()

        return houve_level_up

    # Dentro da classe Items em source/items/items.py

    def _aplicar_efeito(self, player):
        """Toda a lógica de 'o que cada tipo de item faz' vive aqui. 
        Suporte para contagem de pontuação oficial ativo."""
        houve_level_up = False

        if self.tipo in player.coletaveis:
            player.coletaveis[self.tipo] += 1

        # Garante que a variável de pontuação exista no objeto do jogador
        if not hasattr(player, 'pontuacao'):
            player.pontuacao = 0

        # Distribuição de pontos baseada no valor/raridade do item
        if self.tipo == 'exp_shard':
            houve_level_up = bool(player.ganhar_xp(10))
            player.pontuacao += 10  # +100 pontos por Fragmento de XP comum
            
        elif self.tipo == 'big_shard':
            houve_level_up = bool(player.ganhar_xp(50))
            player.pontuacao += 50  # +500 pontos por Núcleo de XP Grande
            
        elif self.tipo == 'life_orb':
            player.curar(player.vida_maxima)
            player.pontuacao += 100  # +250 pontos por Kit Médico/Biofoam
            
        elif self.tipo == 'upgrade':
            player.pontuacao += 200
            # Repassa o id específico que o item já carregava desde o spawn.
            player.ativar_upgrade_forcado(id_forcado=self.id_arma_alvo)

        return houve_level_up