"""Animação dos bosses (roteiro F2): clips declarativos, hit frames e nada alocado por frame.

- `Clip`: quais quadros, quanto tempo cada um, se repete e quais quadros disparam um evento.
- `Animador`: toca o clip pedido. No spawn, faz uma cópia de cada quadro (o alpha da
  camuflagem é de cada instância: no quadro compartilhado do cache, valeria para todos) e
  pega a máscara do quadro original no cache. Por frame, só escolhe uma dessas superfícies.

Regras de tempo (as do `EnemyAnimation.animar` de antes):
- o quadro avança quando passa MAIS que `ms_por_quadro` desde a última troca;
- pedir um clip com a mesma sequência de quadros só muda o ritmo (o passo e o relógio
  continuam: andar → investida não reinicia o ciclo); sequência diferente recomeça do 1º.
"""
from dataclasses import dataclass, field
from types import MappingProxyType

from source.utils.superficies import mascara_de

LADOS = ('left', 'right')


@dataclass(frozen=True)
class Clip:
    ms_por_quadro: int
    quadros: tuple = None       # índices nos quadros do sprite; None = todos, em ordem
    loop: bool = True           # False: para no último quadro (`terminou`)
    eventos: dict = field(default_factory=dict)   # passo do clip -> nome do evento (hit frame)

    def __post_init__(self):
        ms = self.ms_por_quadro
        if not (isinstance(ms, int) and not isinstance(ms, bool) and ms > 0):
            raise ValueError(f'Clip: ms_por_quadro {ms!r} (precisa ser inteiro > 0)')
        if self.quadros is not None:
            if not (isinstance(self.quadros, tuple) and self.quadros
                    and all(isinstance(q, int) and not isinstance(q, bool) and q >= 0 for q in self.quadros)):
                raise ValueError(f'Clip: quadros {self.quadros!r} (precisa ser tupla não vazia de inteiros >= 0)')
        if not isinstance(self.loop, bool):
            raise ValueError(f'Clip: loop {self.loop!r} (precisa ser bool)')
        if not isinstance(self.eventos, dict):
            raise ValueError(f'Clip: eventos {self.eventos!r} (precisa ser dict passo -> nome)')
        for passo, nome in self.eventos.items():
            if not (isinstance(passo, int) and not isinstance(passo, bool) and passo >= 0):
                raise ValueError(f'Clip: passo de evento {passo!r} (precisa ser inteiro >= 0)')
            if self.quadros is not None and passo >= len(self.quadros):
                raise ValueError(f'Clip: evento no passo {passo}, mas o clip tem {len(self.quadros)} quadros')
            if not (isinstance(nome, str) and nome):
                raise ValueError(f'Clip: nome de evento {nome!r} (precisa ser texto)')
        object.__setattr__(self, 'eventos', MappingProxyType(dict(self.eventos)))


class Animador:
    """`sprites`: lado ('left'/'right') -> lista de quadros, como em `EnemySprites`."""

    def __init__(self, sprites, clips, inicial, lado, agora):
        if set(sprites) != set(LADOS):
            raise ValueError(f'Animador: sprites precisa ter os lados {LADOS} (tem {sorted(sprites)})')
        total = len(sprites['left'])
        if total == 0 or len(sprites['right']) != total:
            raise ValueError('Animador: os dois lados precisam ter o mesmo número (> 0) de quadros')
        if not clips:
            raise ValueError('Animador: nenhum clip')

        self._sequencias = {}
        for nome, clip in clips.items():
            if not isinstance(clip, Clip):
                raise ValueError(f'Animador: clip "{nome}" não é um Clip ({clip!r})')
            sequencia = clip.quadros if clip.quadros is not None else tuple(range(total))
            fora = [q for q in sequencia if q >= total]
            if fora:
                raise ValueError(f'Animador: clip "{nome}" usa os quadros {fora}, mas o sprite tem {total}')
            if clip.quadros is None and any(p >= total for p in clip.eventos):
                raise ValueError(f'Animador: clip "{nome}" tem evento além dos {total} quadros')
            self._sequencias[nome] = sequencia

        self.clips = clips
        self._imagens = {lado: [quadro.copy() for quadro in sprites[lado]] for lado in LADOS}
        self._mascaras = {lado: [mascara_de(quadro) for quadro in sprites[lado]] for lado in LADOS}

        self.lado = self._validar_lado(lado)
        self.clip = self._validar_clip(inicial)
        self._pedido = self.clip
        self._reiniciar = False
        self.passo = 0
        self.terminou = False
        self.evento = self.clips[self.clip].eventos.get(0)
        self._ultima_troca = agora

    # ------------------------------------------------------------ pedidos
    def tocar(self, nome, reiniciar=False):
        """Pede o clip `nome`; vale a partir do próximo `atualizar`. O último pedido ganha.
        `reiniciar=True` recomeça do 1º quadro mesmo que ele já esteja tocando (outro golpe)."""
        self._pedido = self._validar_clip(nome)
        self._reiniciar = reiniciar

    def virar(self, direcao_x):
        """Olha para o lado de `direcao_x` (0 = mantém)."""
        if direcao_x < 0:
            self.lado = 'left'
        elif direcao_x > 0:
            self.lado = 'right'

    # ------------------------------------------------------------ frame
    def atualizar(self, agora):
        """Aplica o pedido e avança o tempo. `evento` fica com o hit frame que entrou agora (ou None)."""
        self.evento = None
        if self._pedido != self.clip or self._reiniciar:
            recomecar = self._reiniciar or self._sequencias[self._pedido] != self._sequencias[self.clip]
            self.clip = self._pedido
            self._reiniciar = False
            self.terminou = False             # o fim era do clip anterior
            if recomecar:
                self._entrar_no_passo(0, agora)
                return
        clip = self.clips[self.clip]
        if self.terminou or agora - self._ultima_troca <= clip.ms_por_quadro:
            return
        proximo = self.passo + 1
        if proximo >= len(self._sequencias[self.clip]):
            if not clip.loop:
                self.terminou = True
                return
            proximo = 0
        self._entrar_no_passo(proximo, agora)

    def _entrar_no_passo(self, passo, agora):
        self.passo = passo
        self._ultima_troca = agora
        self.terminou = False
        self.evento = self.clips[self.clip].eventos.get(passo)

    # ------------------------------------------------------------ leitura
    @property
    def quadro(self):
        """Índice do quadro mostrado (no sprite, não no clip)."""
        return self._sequencias[self.clip][self.passo]

    @property
    def imagem(self):
        """Superfície própria desta instância (pode receber `set_alpha`)."""
        return self._imagens[self.lado][self.quadro]

    @property
    def mascara(self):
        """Máscara do quadro original, do cache (não a modifique)."""
        return self._mascaras[self.lado][self.quadro]

    @property
    def imagens(self):
        """Todas as superfícies desta instância (para testes de alocação)."""
        return [imagem for lado in LADOS for imagem in self._imagens[lado]]

    # ------------------------------------------------------------ validação
    def _validar_clip(self, nome):
        if nome not in self.clips:
            raise KeyError(f'clip "{nome}" não existe (há: {sorted(self.clips)})')
        return nome

    @staticmethod
    def _validar_lado(lado):
        if lado not in LADOS:
            raise ValueError(f'lado {lado!r} (precisa ser um de {LADOS})')
        return lado


__all__ = ['Clip', 'Animador', 'LADOS']
