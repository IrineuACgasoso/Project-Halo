"""Invisibilidade: camuflagem de qualquer inimigo, em 3 fases (fade out → oculto → fade in).

Quem está em fade out ou oculto NÃO pode ser mirado por ninguém (`BaseEnemy.alvejavel`).

Uso (a `BaseEnemy` guarda a skill ativa em `self.invisibilidade`, None = visível):
    self.iniciar_invisibilidade('elite')           # uma vez
    self.atualizar_invisibilidade(delta_time)      # todo passo
    self.encerrar_invisibilidade()                 # opcional: corta e começa a reaparecer
"""
from .config import INVISIBILIDADE_PRESETS

FADE_OUT, OCULTO, FADE_IN = 'fade_out', 'hold', 'fade_in'


class Invisibilidade:
    __slots__ = ('inimigo', 'cfg', 'fase', 'terminou', '_total_ms', '_fase_ms', '_alpha', '_alpha_inicial',
                 '_revelado_ms', '_revelado_alpha')

    def __init__(self, inimigo, preset='padrao', config=None):
        if config is None and preset not in INVISIBILIDADE_PRESETS:
            raise KeyError(f'preset de invisibilidade desconhecido: {preset!r}')
        self.inimigo = inimigo
        self.cfg = config if config is not None else INVISIBILIDADE_PRESETS[preset]
        self.fase = FADE_OUT
        self.terminou = False
        self._total_ms = 0.0
        self._fase_ms = 0.0
        self._alpha = 255.0            # sem o clarão de `revelar`
        self._alpha_inicial = 0.0      # de onde o fade in parte (encerrar no meio do fade out)
        self._revelado_ms = 0.0
        self._revelado_alpha = 0
        inimigo._aplicar_alpha(255)

    @property
    def oculta(self):
        """Não pode ser mirado (o fade in já pode)."""
        return self.fase != FADE_IN

    @property
    def intensidade(self):
        """0 = totalmente visível, 1 = totalmente invisível (força da distorção)."""
        return 1 - self._alpha / 255

    @property
    def revelada(self):
        return self._revelado_ms > 0

    def revelar(self, duracao_ms=100, alpha=120):
        """Clarão: aparece parcialmente por um instante (ex.: ao atirar). Continua sem poder ser mirado."""
        self._revelado_ms = duracao_ms
        self._revelado_alpha = alpha

    def encerrar(self):
        """Começa a reaparecer agora, do alpha em que está. Já reaparecendo, não faz nada."""
        if self.oculta:
            self.fase = FADE_IN
            self._fase_ms = 0.0
            self._alpha_inicial = self._alpha

    def atualizar(self, delta_time):
        """Um passo. Devolve True quando o inimigo reapareceu por completo."""
        if self.terminou:
            return True
        dt = delta_time * 1000
        self._total_ms += dt
        self._fase_ms += dt

        if self.fase == FADE_OUT:
            t = min(1.0, self._fase_ms / self.cfg.fade_out_ms)
            self._alpha = 255 - 255 * t
            if t >= 1.0:
                self.fase = OCULTO
                self._fase_ms = 0.0
        elif self.fase == OCULTO:
            self._alpha = 0.0
            # Pelo tempo total: o excesso do último passo do fade out não estica a duração
            if self.cfg.duracao_ms is not None and self._total_ms >= self.cfg.fade_out_ms + self.cfg.duracao_ms:
                self.fase = FADE_IN
                self._fase_ms = 0.0
                self._alpha_inicial = 0.0
        else:
            t = min(1.0, self._fase_ms / self.cfg.fade_in_ms)
            self._alpha = self._alpha_inicial + (255 - self._alpha_inicial) * t
            self.terminou = t >= 1.0

        alpha = self._alpha
        if self._revelado_ms > 0:
            self._revelado_ms -= dt
            alpha += self._revelado_alpha
        self.inimigo._aplicar_alpha(max(0, min(255, alpha)))
        return self.terminou
