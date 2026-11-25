"""Bot jogador (roteiro F4): a `FonteEntrada` que mantém distância do boss e esquiva. Só para medir
lutas (`tools/lutas.py`) e testar; o jogo não o usa.

Joga como uma pessoa razoável, não como um oráculo: só vê o que está na tela, reage a cada ameaça
`REACAO_MS` depois de vê-la, decide a cada `DECISAO_MS` e anda nas 8 direções do teclado.
Não usa sorteio: com a mesma seed, a luta se repete igual.

Conhece tiros em linha reta, contato, artilharia, cone, retângulo, gás e void. Feixes, anéis (EMP) e
efeitos próprios de um boss ele não esquiva: o dano deles no relatório é um teto. Ele também não
planeja caminho: um inimigo preso atrás de uma parede, fora do alcance, fica lá.
"""
import math
from weakref import WeakKeyDictionary

import pygame

from source.systems.collision import rect_de_colisao
from source.systems.entitymanager import entity_manager
from source.systems.entrada import PARADO, ComandoJogador, FonteEntrada
from source.systems.gameclock import relogio
from source.utils.collision_utils import sair_das_paredes

V = pygame.math.Vector2

DECISAO_MS = 100
REACAO_MS = 200
PASSO_S = 0.1               # cada candidato é simulado em passos de PASSO_S...
PASSOS = 8                  # ...por este tanto (0,8 s à frente)
FAIXA = (180, 340)          # distância desejada até o corpo do boss...
CORPO_MAXIMO = 150          # ...que conta até este raio: longe demais, as armas não alcançam
MARGEM_TIRO = 20            # folga, em px, para não passar raspando
MARGEM_CONTATO = 70

PESO_GOLPE = 100.0          # ser atingido; o que está mais longe no tempo pesa menos
PESO_FAIXA = 0.06           # por px fora da faixa
PESO_PAREDE = 1.5           # por passo em que a parede segurou o jogador
PESO_VOID = 300.0
BONUS_INERCIA = 2.0         # seguir como está: sem isto ele treme entre dois lados iguais

DIRECOES = [PARADO] + [ComandoJogador(direcao=(x, y))
                       for x in (-1, 0, 1) for y in (-1, 0, 1) if (x, y) != (0, 0)]


class Bot(FonteEntrada):
    def __init__(self, game):
        self.game = game
        self.comando = PARADO
        self._decidir_em = 0
        self._vistos = WeakKeyDictionary()      # sprite -> quando apareceu na tela
        self._rastro = WeakKeyDictionary()      # inimigo -> (instante, posição) da última decisão

    def ler(self):
        agora = relogio.agora()
        if agora >= self._decidir_em:
            self._decidir_em = agora + DECISAO_MS
            self.comando = self._decidir(agora)
        return self.comando

    # ------------------------------------------------------------ percepção
    def _ameacas(self, agora):
        """(tiros, áreas, corpos, gases) que o bot já teve tempo de notar."""
        tiros, areas, corpos, gases = [], [], [], []
        camera = self.game.camera
        tela = pygame.Rect(camera.offset, camera.visao)
        for s in entity_manager.all_sprites:
            if hasattr(s, 'raio_seguro'):
                gases.append(s)
                continue
            posicao = getattr(s, 'posicao', None)
            if posicao is None or not tela.collidepoint(posicao):
                continue
            if agora - self._vistos.setdefault(s, agora) < REACAO_MS:
                continue
            if entity_manager.inimigos_grupo.has(s):
                if s.alvejavel and not s.inofensivo:
                    corpos.append((V(posicao), self._velocidade(s, agora), rect_de_colisao(s).size))
            elif getattr(s, 'dono', 'PLAYER') == 'PLAYER':
                continue
            elif hasattr(s, 'cfg') and hasattr(s, 'explodiu'):
                if s.cfg.dano > 0 or getattr(s.cfg, 'dot', False):
                    areas.append(s)
            elif entity_manager.projeteis_inimigos_grupo.has(s) and s.dano > 0:
                # granada e morteiro (dano 0) viram aviso de área quando chegam ao chão
                meia = max(rect_de_colisao(s).size) / 2
                tiros.append((V(posicao), s.direcao * s.velocidade, meia))
        return tiros, areas, corpos, gases

    def _velocidade(self, inimigo, agora):
        antes = self._rastro.get(inimigo)
        self._rastro[inimigo] = (agora, V(inimigo.posicao))
        if antes is None or agora <= antes[0]:
            return V()
        v = (inimigo.posicao - antes[1]) / ((agora - antes[0]) / 1000)
        return v if v.length_squared() < 1500 ** 2 else V()     # foi teleporte

    def _alvo(self):
        """Quem dita a distância: o boss ou, sem ele para ferir, o inimigo mais próximo que dê."""
        boss = self.game.sessao.boss_atual
        if _da_para_ferir(boss):
            return boss
        pos = self.game.player.posicao
        return min((i for i in entity_manager.inimigos_grupo if _da_para_ferir(i)),
                   key=lambda i: pos.distance_squared_to(i.posicao), default=None)

    # ------------------------------------------------------------ decisão
    def _decidir(self, agora):
        ameacas, alvo = self._ameacas(agora), self._alvo()
        return min(DIRECOES, key=lambda comando: self._custo(comando, agora, ameacas, alvo))

    def _custo(self, comando, agora, ameacas, alvo):
        """O que custa andar 0,8 s nesta direção."""
        tiros, areas, corpos, gases = ameacas
        player, mapa = self.game.player, self.game.mapa
        meia = max(player.hitbox.size) / 2
        raio = player.hitbox.width / 2
        direcao = V(comando.direcao)
        if direcao:
            direcao.normalize_ip()
        passo = direcao * (player.velocidade * player.status.mult_velocidade * PASSO_S)
        # com um pedaço maior que o raio, o jogador simulado atravessaria a parede
        pedacos = max(1, math.ceil(passo.length() / (raio / 2)))
        pos = V(player.posicao)
        custo = 0.0 if comando is self.comando else BONUS_INERCIA
        pendentes = list(tiros)                 # cada tiro acerta uma vez só
        for i in range(1, PASSOS + 1):
            t = i * PASSO_S
            urgencia = 1.0 - 0.5 * i / PASSOS
            antes = V(pos)
            for _ in range(pedacos):
                pos += passo / pedacos
                sair_das_paredes(pos, raio, mapa.grade_paredes, 3)
            andou = pos - antes
            if passo and andou.length() < passo.length() * 0.7:
                custo += PESO_PAREDE
            if mapa.calcular_puxo_void(pos)[1]:
                custo += PESO_VOID * urgencia
            for tiro in tuple(pendentes):
                p, v, meia_tiro = tiro
                # no referencial do jogador, o tiro anda em linha reta neste passo
                perto = _distancia_da_origem(p + v * (t - PASSO_S) - antes, v * PASSO_S - andou)
                if perto < meia + meia_tiro + MARGEM_TIRO:
                    custo += PESO_GOLPE * urgencia
                    pendentes.remove(tiro)
            for p, v, (largura, altura) in corpos:
                onde = p + v * t
                folga = max(abs(pos.x - onde.x) - largura / 2, abs(pos.y - onde.y) - altura / 2) - meia
                if folga < MARGEM_CONTATO:
                    perigo = 2.0 if folga < 0 else 1.0 - folga / MARGEM_CONTATO
                    custo += PESO_GOLPE * urgencia * perigo / PASSOS
            for area in areas:
                if _area_fere(area, agora + t * 1000, ultimo=i == PASSOS) and _na_area(area, pos):
                    # a área que não dá para deixar em 0,8 s ainda precisa puxar para fora
                    custo += PESO_GOLPE * urgencia / 2 - PESO_FAIXA * pos.distance_to(area.posicao)
            for gas in gases:
                if pos.distance_to(gas.posicao_boss) > gas.raio_seguro - meia:
                    custo += PESO_GOLPE * urgencia / PASSOS
        if alvo is not None:
            dist = pos.distance_to(alvo.posicao) - min(max(rect_de_colisao(alvo).size) / 2, CORPO_MAXIMO)
            custo += PESO_FAIXA * max(FAIXA[0] - dist, dist - FAIXA[1], 0)
        return custo


def _da_para_ferir(inimigo):
    # None, o aviso de área que faz as vezes de boss (Gravemind) e a consciência do Warden: não dá
    return inimigo is not None and getattr(inimigo, 'alvejavel', False) and not inimigo.invulneravel


def _distancia_da_origem(inicio, trecho):
    """Menor distância da origem ao segmento que começa em `inicio` e anda `trecho`."""
    comprimento2 = trecho.length_squared()
    t = 0.0 if comprimento2 == 0 else max(0.0, min(1.0, -inicio.dot(trecho) / comprimento2))
    return (inicio + trecho * t).length()


def _area_fere(area, quando, ultimo):
    """A área fere no instante `quando` (ms)? No último passo, o aviso que ainda não chegou conta:
    parar dentro dele só adia o problema."""
    dot = getattr(area.cfg, 'dot', False)
    if area.explodiu:
        return getattr(area, 'dot_ativo', False)
    impacto = area.tempo_criacao + area.cfg.duracao
    return abs(quando - impacto) <= PASSO_S * 1000 or (dot and quando >= impacto) or (ultimo and quando < impacto)


def _na_area(area, ponto):
    if hasattr(area, 'contem'):
        return area.contem(ponto)
    delta = ponto - area.posicao
    raio = getattr(area.cfg, 'raio_explosao', None) or getattr(area.cfg, 'raio', 0)
    if delta.length() > raio + MARGEM_TIRO:
        return False
    abertura = getattr(area.cfg, 'angulo_spray', 360)
    if abertura >= 360 or not delta:
        return True
    cosseno = max(-1.0, min(1.0, area.direcao.dot(delta.normalize())))
    return math.degrees(math.acos(cosseno)) <= abertura / 2 + 5
