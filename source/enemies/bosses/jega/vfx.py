import pygame

from source.enemies.base.enemy_base import BaseEnemy
from source.feats.skills.artilharia import ArtilhariaAviso
from source.systems.entitymanager import entity_manager


class JegaClone(BaseEnemy):
    """Ilusão holográfica do Jega: só herda de BaseEnemy (não da JegaAI/
    JegaAttacks reais - não precisa de órbita, carabina, spike etc).

    Puxa os mesmos assets do Jega original, aplica um filtro vermelho
    translúcido por cima, e corre em linha reta na direção travada no
    momento em que foi invocado. Não causa dano físico nenhum - mas se o
    jogador atirar nele (vida_base=1, qualquer hit já mata), ele explode
    numa nuvem de plasma instável (preset 'jega_decoy_explosion') que
    aplica DoT em vez de dano de impacto.

    IMPORTANTE: este update() é TOTALMENTE MANUAL - não chama
    super().update(), porque o update() padrão da BaseEnemy implementa o
    AI genérico de perseguição (mover na direção do jogador), o que
    sobrescreveria a direção travada e faria o clone se comportar
    exatamente como um Jega de verdade perseguindo o jogador.
    """

    def __init__(self, posicao, game, jogador, direcao=None, velocidade_base=300, **kwargs):
        super().__init__(posicao, vida_base=1, dano_base=0, velocidade_base=velocidade_base,
                          game=game, sprite_key='jega', flip_sprite=True)

        self.jogador = jogador
        self.is_boss = False

        self.setup_animation(estado_inicial='right', velocidade_animacao=200)
        self._aplicar_filtro_vermelho()

        # Hitbox igual à do Jega original (mesmos assets, mesma silhueta)
        nova_largura = self.rect.width / 1.3
        self.hitbox = pygame.Rect(0, 0, nova_largura, self.rect.height)
        self.hitbox.center = self.rect.center

        # Direção travada no instante da invocação - se nada for passado,
        # mira na posição do jogador naquele momento (linha reta).
        if direcao is not None and direcao.length_squared() > 0:
            self.direcao_fixa = direcao.normalize()
        else:
            vetor = self.jogador.posicao - self.posicao
            self.direcao_fixa = vetor.normalize() if vetor.length_squared() > 0 else pygame.math.Vector2(1, 0)

    def _aplicar_filtro_vermelho(self):
        """Tinge cada frame já carregado de vermelho translúcido, uma única
        vez no __init__, reaproveitando o cache de sprites do Jega original
        (não recalcula nada por frame)."""
        sprites_tintados = {}
        for chave, frames in self.sprites.items():
            novos_frames = []
            for frame in frames:
                tintado = frame.copy()
                tintado.fill((255, 60, 60, 160), special_flags=pygame.BLEND_RGBA_MULT)
                novos_frames.append(tintado)
            sprites_tintados[chave] = novos_frames
        self.sprites = sprites_tintados
        self.image = self.sprites[self.estado_animacao][self.frame_atual]

    @property
    def collision_rect(self):
        return self.hitbox

    def morrer(self, grupos=None):
        """Não dropa nada - qualquer dano recebido já é o "gatilho da
        armadilha": explode em plasma instável em vez de morrer normal."""
        ArtilhariaAviso(
            posicao=self.posicao,
            grupos=(entity_manager.all_sprites,),
            game=self.game,
            dono='INIMIGO',
            preset='jega_decoy_explosion'
        )
        self.kill()

    def update(self, delta_time, paredes=None):
        # Movimento 100% manual: sempre em linha reta na direção travada,
        # NUNCA reage ao jogador depois de invocado.
        self.posicao += self.direcao_fixa * self.velocidade * delta_time

        if paredes:
            self.aplicar_colisao_mapa(paredes)

        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        self.hitbox.center = self.rect.center

        self.set_sprite_direction(self.direcao_fixa.x)
        self.animar()