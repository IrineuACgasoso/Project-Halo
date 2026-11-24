"""Motor do sistema de status: um componente por entidade e o ponto único `aplicar`.

- Cada entidade (jogador e inimigos) tem `status = StatusEntidade(...)`. Os modificadores
  (`mult_velocidade`, `atordoado`...) são atributos simples, recalculados só quando um efeito
  entra ou sai: quem os lê por frame não paga nada.
- Só as entidades com efeito temporário ativo são atualizadas por frame (`atualizar_status`,
  chamado pelo `Game.update`). A lista é limpa a cada partida (`limpar_status`).
- Acúmulo (roteiro §8, item 9): efeitos do mesmo tipo e do mesmo lugar ocupam um só espaço, e
  reaplicar substitui (renova a duração e os valores). Lugares diferentes coexistem e somam por tipo.
  O lugar é a `chave`, se dada, ou a `fonte`.
- `fonte` é a entidade que causa (jogador, inimigo ou None), como em `Dano.fonte`: a queimadura dá
  o dano em nome dela. `chave` é qualquer objeto: ex. cada arma do jogador com o seu próprio lugar.
"""
from source.systems.dano import Dano, STATUS

from .efeitos import (Atordoamento, BuffCadencia, BuffDano, BuffVelocidade, Cegueira, Cura,
                      Defesa, Escudo, Fraqueza, INSTANTANEOS, Lentidao, Queimadura, SO_NO_JOGADOR,
                      TEMPORARIOS)

TICK_QUEIMADURA = 0.25   # s: a queimadura acumula o dano e o aplica a cada tick (e no fim)
_FOLGA = 1e-9            # s: soma de dt em float não fecha exata


class _Ativo:
    """Um efeito temporário em andamento."""
    __slots__ = ('efeito', 'fonte', 'restante', 'dano_pendente', 'desde_tick')

    def __init__(self, efeito, fonte):
        self.efeito = efeito
        self.fonte = fonte
        self.restante = None if efeito.duracao_ms is None else efeito.duracao_ms / 1000
        self.dano_pendente = 0.0
        self.desde_tick = 0.0


class StatusEntidade:
    __slots__ = ('dono', 'eh_jogador', 'imunidades', '_ativos',
                 'mult_velocidade', 'mult_dano_causado', 'mult_dano_recebido', 'mult_cooldown',
                 'atordoado', 'queimando', 'reducao_cura', 'raio_cegueira')

    def __init__(self, dono, eh_jogador=False, imunidades=frozenset()):
        self.dono = dono
        self.eh_jogador = eh_jogador
        self.imunidades = frozenset(imunidades)
        self._ativos = {}   # (tipo do efeito, fonte) -> _Ativo, na ordem de chegada
        self._recalcular()

    def tem(self, tipo):
        """Há um efeito desse tipo ativo (de qualquer fonte)?"""
        return any(type(a.efeito) is tipo for a in self._ativos.values())

    def ativos(self):
        """(efeito, fonte, segundos restantes ou None) de cada efeito ativo, na ordem de chegada."""
        return [(a.efeito, a.fonte, a.restante) for a in self._ativos.values()]

    def _recalcular(self):
        buff_vel = buff_dano = fraqueza = lentidao = reducao = 0.0
        cooldown = defesa = 1.0
        atordoado = queimando = False
        raio = None
        for ativo in self._ativos.values():
            e = ativo.efeito
            tipo = type(e)
            if tipo is BuffVelocidade:
                buff_vel += e.porcentagem
            elif tipo is Lentidao:
                lentidao = max(lentidao, e.porcentagem)
            elif tipo is BuffDano:
                buff_dano += e.porcentagem
            elif tipo is Fraqueza:
                fraqueza += e.porcentagem
            elif tipo is BuffCadencia:
                cooldown *= 1 - e.porcentagem
            elif tipo is Defesa:
                defesa *= 1 - e.porcentagem
            elif tipo is Atordoamento:
                atordoado = True
            elif tipo is Queimadura:
                queimando = True
                reducao = max(reducao, e.reducao_cura)
            elif tipo is Cegueira:
                raio = e.raio if raio is None else min(raio, e.raio)
        # Sem efeitos, todos os multiplicadores são exatamente 1.0 (x * 1.0 == x: nada muda).
        self.mult_velocidade = (1 + buff_vel) * (1 - lentidao)
        self.mult_dano_causado = 1 + buff_dano
        self.mult_dano_recebido = (1 + fraqueza) * defesa
        self.mult_cooldown = cooldown
        self.atordoado = atordoado
        self.queimando = queimando
        self.reducao_cura = reducao
        self.raio_cegueira = raio

    def _adicionar(self, efeito, fonte, lugar):
        anterior = self._ativos.pop((type(efeito), lugar), None)   # reaplicar: volta para o fim da ordem
        novo = self._ativos[(type(efeito), lugar)] = _Ativo(efeito, fonte)
        if anterior is not None:   # senão, renovar antes do tick apagaria o dano já acumulado
            novo.dano_pendente, novo.desde_tick = anterior.dano_pendente, anterior.desde_tick
        self._recalcular()

    def _remover(self, tipo, lugar):
        if self._ativos.pop((tipo, lugar), None) is None:
            return False
        self._recalcular()
        return True

    def limpar(self):
        self._ativos.clear()
        self._recalcular()

    def atualizar(self, delta_time):
        """Conta o tempo dos efeitos, aplica a queimadura e tira o que acabou."""
        acabou = False
        for chave, ativo in list(self._ativos.items()):
            if ativo.restante is None:   # buff sem fim
                continue
            passo = min(delta_time, ativo.restante)
            ativo.restante -= delta_time
            fim = ativo.restante <= _FOLGA
            if type(ativo.efeito) is Queimadura:
                ativo.dano_pendente += ativo.efeito.dps * passo
                ativo.desde_tick += passo
                if (ativo.desde_tick >= TICK_QUEIMADURA - _FOLGA or fim) and ativo.dano_pendente > 0:
                    dano = Dano(ativo.dano_pendente, STATUS, ativo.fonte, ignora_iframes=True)
                    ativo.dano_pendente = ativo.desde_tick = 0.0
                    self.dono.receber_dano(dano)
            # O dano acima pode ter reaplicado o mesmo efeito: só sai se ainda for este.
            if fim and self._ativos.get(chave) is ativo:
                del self._ativos[chave]
                acabou = True
        if acabou:
            self._recalcular()


# Entidades com efeito temporário ativo (dict = ordem de chegada estável: a simulação é determinística).
_com_efeito = {}


def aplicar(alvo, efeito, fonte=None, chave=None):
    """Ponto único de buffs e debuffs, para o jogador e os inimigos.

    `fonte`: a entidade que causa (ou None). `chave`: o lugar de acúmulo (padrão: a fonte). O mesmo
    lugar reaplicando só renova o efeito; lugares diferentes acumulam (ver o módulo).
    Devolve False se o alvo é imune ou já saiu do mundo. Efeito só do jogador (cegueira, cadência)
    num inimigo, efeito desconhecido ou fonte que não é entidade são bug de quem chama (exceção).
    """
    tipo = type(efeito)
    if tipo not in TEMPORARIOS and tipo not in INSTANTANEOS:
        raise TypeError(f'efeito desconhecido: {efeito!r}')
    if fonte is not None and not isinstance(getattr(fonte, 'status', None), StatusEntidade):
        raise ValueError(f'fonte precisa ser uma entidade (jogador ou inimigo) ou None, veio {fonte!r}; '
                         f'para um lugar de acúmulo próprio, use chave=')
    status = alvo.status
    if tipo in SO_NO_JOGADOR and not status.eh_jogador:
        raise ValueError(f'{tipo.__name__} só vale no jogador')
    if tipo in status.imunidades or not alvo.alive():
        return False
    if tipo is Cura:
        alvo.receber_cura(efeito.valor * (1 - status.reducao_cura))
    elif tipo is Escudo:
        alvo.receber_escudo(efeito.valor)
    else:
        status._adicionar(efeito, fonte, fonte if chave is None else chave)
        _com_efeito[status] = None
    return True


def remover(alvo, tipo, fonte=None, chave=None):
    """Tira o efeito `tipo` do lugar em que `aplicar` o pôs (mesmos `fonte`/`chave`). Devolve se havia."""
    return alvo.status._remover(tipo, fonte if chave is None else chave)


def atualizar_status(delta_time):
    """Um passo do `Game.update`: só as entidades com efeito ativo."""
    for status in list(_com_efeito):
        if status.dono.alive() and status._ativos:
            status.atualizar(delta_time)
        if not status._ativos or not status.dono.alive():
            del _com_efeito[status]


def entidades_queimando():
    """Quem está com queimadura agora (para o desenho do fogo)."""
    return [status.dono for status in _com_efeito if status.queimando and status.dono.alive()]


def limpar_status():
    """A cada partida nova (as entidades da partida anterior não contam mais)."""
    _com_efeito.clear()


def multiplicador_de_dano(dano, alvo):
    """Buff de dano de quem causa × fraqueza de quem recebe. Sem efeitos, exatamente 1.0."""
    fonte = dano.fonte
    causado = 1.0 if fonte is None else fonte.status.mult_dano_causado
    return causado * alvo.status.mult_dano_recebido
