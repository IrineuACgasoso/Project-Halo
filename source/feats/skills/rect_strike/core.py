"""Ataque retangular direcionado: aviso que se enche do dono até a ponta e depois golpeia a área.

O retângulo começa em `posicao` (o dono) e vai até `altura` px na direção travada, com `largura` px
de espessura. Como a artilharia e o cone, atinge quem tem a POSIÇÃO dentro da área no golpe."""
import pygame

from source.systems.dano import AREA, Dano, fonte_do_dono, habilidade_da
from source.systems.empurrao import empurrar_na_direcao
from source.systems.status import aplicar
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.utils.superficies import SUPERFICIE_VAZIA, camada_alpha
from source.utils.vetores import direcao_segura, no_retangulo

from .config import RECT_STRIKE_PRESETS, RectStrikeConfig

CLARAO_MS = 150
ESPESSURA_BORDA = 3


class RectStrikeAviso(pygame.sprite.Sprite):
    def __init__(self, posicao, direcao, grupos, game, dono='BOSS', preset='padrao',
                 custom_config: RectStrikeConfig = None, fonte=None, ao_explodir=None):
        if custom_config is None and preset not in RECT_STRIKE_PRESETS:
            raise KeyError(f'preset de ataque retangular desconhecido: {preset!r}')
        super().__init__(grupos)
        self.game = game
        self.dono = dono
        self.fonte = fonte_do_dono(dono, fonte)   # quem causou (contrato de dano, E1)
        self.habilidade = habilidade_da(self.fonte)
        self.cfg = custom_config if custom_config is not None else RECT_STRIKE_PRESETS[preset]
        self.preset = preset
        self.posicao = pygame.math.Vector2(posicao)
        self.direcao = direcao_segura((0, 0), direcao)
        self.tempo_criacao = relogio.agora()
        self.explodiu = False
        self.ao_explodir = ao_explodir   # chamado 1× com o aviso quando o golpe sai

        lateral = pygame.math.Vector2(-self.direcao.y, self.direcao.x) * (self.cfg.largura / 2)
        self._base = (self.posicao + lateral, self.posicao - lateral)   # cantos do lado do dono
        self._cantos = self._poligono(1.0)
        xs, ys = [c[0] for c in self._cantos], [c[1] for c in self._cantos]
        margem = ESPESSURA_BORDA
        self._caixa = pygame.Rect(int(min(xs)) - margem, int(min(ys)) - margem,
                                  int(max(xs) - min(xs)) + 2 * margem + 1, int(max(ys) - min(ys)) + 2 * margem + 1)

        self.image = SUPERFICIE_VAZIA    # o draw é próprio
        self.rect = self.image.get_rect(center=self.posicao)
        self.hitbox = self.rect.copy()

    def ao_atingir_alvo(self, alvo):
        """Evita quebras se registrado no gerenciador de colisões padrão (o dano sai no update)."""
        return False

    @property
    def progresso(self):
        """0 → 1 durante o aviso."""
        return 1.0 if self.explodiu else min((relogio.agora() - self.tempo_criacao) / self.cfg.duracao, 1.0)

    def _poligono(self, fracao):
        """Cantos (no mundo) da parte do retângulo que vai do dono até `fracao` do alcance."""
        avanco = self.direcao * (self.cfg.altura * fracao)
        a, b = self._base
        return (a, b, b + avanco, a + avanco)

    def contem(self, ponto):
        return no_retangulo(self.posicao, self.direcao, ponto, self.cfg.altura, self.cfg.largura / 2)

    # ------------------------------------------------------------------ jogo
    def update(self, delta_time, paredes=None):
        agora = relogio.agora()
        if not self.explodiu:
            if agora - self.tempo_criacao >= self.cfg.duracao:
                self.explodiu = True
                self.tempo_criacao = agora
                if self.ao_explodir is not None:
                    self.ao_explodir(self)
                self._golpear()
        elif agora - self.tempo_criacao >= CLARAO_MS:
            self.kill()

    def _golpear(self):
        alvos = entity_manager.inimigos_grupo.sprites() if self.dono == 'PLAYER' else [entity_manager.player]
        for alvo in alvos:
            if self.contem(alvo.posicao):
                alvo.receber_dano(Dano(self.cfg.dano, AREA, self.fonte, ignora_iframes=True, habilidade=self.habilidade))
                if self.cfg.knockback:
                    empurrar_na_direcao(alvo, self.direcao, self.cfg.knockback)
                for efeito in self.cfg.efeitos:
                    aplicar(alvo, efeito, fonte=self.fonte, chave=self.preset)

    # --------------------------------------------------------------- desenho
    def draw(self, surface, offset):
        dx, dy = int(offset.x), int(offset.y)
        camada, area = camada_alpha(surface, self._caixa.move(-dx, -dy))
        if camada is None:
            return
        cfg = self.cfg
        cantos = [(x - dx, y - dy) for x, y in self._cantos]
        if self.explodiu:
            pygame.draw.polygon(camada, cfg.cor_explosao, cantos)
        else:
            pygame.draw.polygon(camada, cfg.cor_fundo, cantos)
            progresso = self.progresso
            if progresso > 0:
                pygame.draw.polygon(camada, cfg.cor_preenchimento,
                                    [(x - dx, y - dy) for x, y in self._poligono(progresso)])
        pygame.draw.polygon(camada, cfg.cor_borda, cantos, ESPESSURA_BORDA)
        surface.blit(camada, area.topleft, area)
