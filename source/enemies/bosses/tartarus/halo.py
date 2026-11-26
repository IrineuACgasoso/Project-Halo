"""Ativação do Halo: a luta tem hora para acabar. O cronômetro fica no topo do HUD; quando zera, a tela
vai ficando branca até tudo sumir e a partida termina (tela de game over), sem passar pelo dano (o
veículo não salva ninguém do Halo). Some se o chefe morrer antes.

Usado pelo Tartarus e pelos chefes que herdaram o kit antigo dele (Atriox, Escharum)."""
import pygame

from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.utils.superficies import SUPERFICIE_VAZIA

FADE_MS = 2600          # do primeiro branco ao branco total
BRANCO_TOTAL_MS = 700   # tudo branco antes do game over
ALERTA_S = 30           # pisca em vermelho nos últimos segundos
Y_TIMER = 34

_FONTE = None
_TEXTOS = {}            # (texto, cor) -> Surface (o texto muda 1× por segundo)


def _fonte():
    global _FONTE
    if _FONTE is None:
        _FONTE = pygame.font.SysFont('Consolas', 28, bold=True)
    return _FONTE


def _texto(texto, cor):
    chave = (texto, cor)
    surf = _TEXTOS.get(chave)
    if surf is None:
        if len(_TEXTOS) > 64:
            _TEXTOS.clear()
        surf = _TEXTOS[chave] = _fonte().render(texto, True, cor)
    return surf


class ProtocoloHalo(pygame.sprite.Sprite):
    def __init__(self, game, boss, tempo_limite_ms=180000):
        super().__init__(entity_manager.all_sprites)
        self.game = game
        self.boss = boss
        self.tempo_inicio = relogio.agora()
        self.tempo_limite = tempo_limite_ms
        self.disparou_em = None            # o cronômetro zerou: começa o branco
        self.image = SUPERFICIE_VAZIA      # só HUD (`hud_draw`): nada no mundo
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.superficie_branca = pygame.Surface(game.tela.get_size())
        self.superficie_branca.fill((255, 255, 255))
        _fonte()

    @property
    def restante_ms(self):
        return max(0, self.tempo_limite - (relogio.agora() - self.tempo_inicio))

    @property
    def alpha_branco(self):
        if self.disparou_em is None:
            return 0
        return min(255, round(255 * (relogio.agora() - self.disparou_em) / FADE_MS))

    def update(self, delta_time, *args, **kwargs):
        if not self.boss or not self.boss.alive() or getattr(self.boss, 'vida', 0) <= 0:
            self.kill()
            return
        agora = relogio.agora()
        if self.disparou_em is None:
            if self.restante_ms <= 0:
                self.disparou_em = agora
        elif agora - self.disparou_em >= FADE_MS + BRANCO_TOTAL_MS:
            self.kill()
            self.game.perder_partida()

    def hud_draw(self, surface):
        """Chamado pelo HUD: o cronômetro, ou o branco depois que o Halo disparou."""
        if self.disparou_em is not None:
            self.superficie_branca.set_alpha(self.alpha_branco)
            surface.blit(self.superficie_branca, (0, 0))
            return
        segundos = -(-self.restante_ms // 1000)        # arredonda para cima: 00:00 só no disparo
        texto = f"ATIVAÇÃO DO HALO: {segundos // 60:02d}:{segundos % 60:02d}"
        alerta = segundos <= ALERTA_S and relogio.agora() % 500 < 250
        cor = (255, 50, 50) if alerta else (180, 220, 255)
        frente, sombra = _texto(texto, cor), _texto(texto, (0, 0, 0))
        caixa = frente.get_rect(center=(surface.get_width() // 2, Y_TIMER))
        surface.blit(sombra, caixa.move(2, 2))
        surface.blit(frente, caixa)
