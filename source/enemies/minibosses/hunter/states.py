"""IA do Hunter: orientação com atraso, vulnerabilidade pelas costas, decisão e movimentação.

Cada habilidade é uma ROTINA (gerador; `yield` = 1 frame) em `attacks.py`. A IA só decide quando
não há rotina ativa e a pausa entre ataques passou.
"""
import random

from source.systems.status import Defesa, aplicar, remover
from source.utils.vetores import no_cone

from .config import CFG, COS_COSTAS, COS_FRENTE_SLAM, DEFESA

ESTADOS = {'canhao': 'cannon', 'burst': 'burst', 'dash': 'run', 'slam': 'shield_slam'}


class HunterAI:
    # ------------------------------------------------------------ orientação
    def agendar_virada(self, atraso_ms):
        """(Re)inicia o timer de virar: quando vencer, ele olha para o lado do jogador NAQUELE instante."""
        self.virar_em = self._agora + atraso_ms

    def virar_para(self, lado):
        """Vira na hora (ex.: no início do dash, para o lado da corrida)."""
        self.lado = lado
        self.set_sprite_direction(lado)

    def atualizar_orientacao(self, agora):
        """Jogador do outro lado inicia o timer; mudar de lado de novo (spam) NÃO o reinicia.
        Quando o timer vence, vale o lado do jogador naquele instante (pode ser nenhum giro)."""
        dx = self.jogador.posicao.x - self.posicao.x
        lado_jogador = (dx > 0) - (dx < 0)
        if self.virar_em is None:
            if lado_jogador and lado_jogador != self.lado:
                self.agendar_virada(CFG.atraso_virar_ms)
        elif agora >= self.virar_em:
            self.virar_em = None
            if lado_jogador and lado_jogador != self.lado:
                self.virar_para(lado_jogador)

    # -------------------------------------------------------- vulnerabilidade
    def atualizar_vulnerabilidade(self):
        """Vulnerável = jogador dentro de ±`costas_graus` do eixo x, do lado das costas.
        Sem a Defesa enquanto vulnerável; o status só é tocado quando o estado muda."""
        nas_costas = no_cone(self.posicao, (-self.lado, 0), self.jogador.posicao, COS_COSTAS)
        if nas_costas == self.vulneravel:
            return
        self.vulneravel = nas_costas
        if nas_costas:
            remover(self, Defesa, chave=self)
        else:
            aplicar(self, DEFESA, chave=self)

    # ------------------------------------------------------------------ loop
    def executar_estados(self, agora):
        if self.rotina is None and agora >= self.livre_em:
            self._pensar(agora)
        if self.rotina is not None:
            try:
                next(self.rotina)
            except StopIteration:
                self._finalizar_rotina()

    def _pensar(self, agora):
        escolha = self.escolher_habilidade(agora)
        if escolha is None:
            return
        self.ultima_habilidade = escolha
        self.estado_habilidade = ESTADOS[escolha]
        self.rotina = getattr(self, f'rotina_{escolha}')()

    def _finalizar_rotina(self):
        self.rotina = None
        self.estado_habilidade = 'idle'
        self.movimento_livre = True
        self.livre_em = self._agora + CFG.pausa_entre_ataques_ms

    def agendar_cooldown(self, nome):
        """Cooldown sorteado a partir de AGORA (fim da habilidade)."""
        self.cd[nome] = self._agora + self.novo_cooldown(*CFG.cooldown[nome])

    def pode_slam(self):
        """Jogador colado e na frente dele."""
        if self.posicao.distance_squared_to(self.jogador.posicao) > CFG.slam_dist ** 2:
            return False
        return no_cone(self.posicao, (self.lado, 0), self.jogador.posicao, COS_FRENTE_SLAM)

    def escolher_habilidade(self, agora):
        """Sorteio por pesos: longe, prefere os canhões; perto, os golpes físicos. Nunca determinista."""
        perto = self.posicao.distance_squared_to(self.jogador.posicao) <= CFG.dist_perto ** 2
        tabela = CFG.pesos_perto if perto else CFG.pesos_longe
        pesos = {}
        for nome, peso in tabela.items():
            if peso <= 0 or agora < self.cd[nome]:
                continue
            if nome == 'slam' and not self.pode_slam():
                continue
            pesos[nome] = peso * (CFG.repetir_mult if nome == self.ultima_habilidade else 1)
        if not pesos:
            return None
        return random.choices(list(pesos), weights=list(pesos.values()))[0]

    # ------------------------------------------------------------ movimento
    def mover_livre(self, agora, delta_time, paredes):
        """Avança no jogador ou anda de lado (perpendicular), trocando ao acaso de tempos em tempos."""
        if agora >= self.troca_movimento_em:
            self.troca_movimento_em = agora + random.randint(*CFG.troca_movimento_ms)
            if random.random() < CFG.chance_lateral:
                self.modo_movimento = 'lateral'
                self.sentido_lateral = random.choice((-1, 1))
            else:
                self.modo_movimento = 'avancar'
        direcao = self._direcao_mov
        direcao.update(self.jogador.posicao.x - self.posicao.x, self.jogador.posicao.y - self.posicao.y)
        if self.modo_movimento == 'lateral':
            direcao.update(-direcao.y * self.sentido_lateral, direcao.x * self.sentido_lateral)
        if direcao.length_squared() == 0:
            return
        self.mover(delta_time, direcao)
        if paredes:
            self.aplicar_colisao_mapa(paredes)
        self.sync_rect()
