from source.systems.gameclock import relogio
from source.enemies.base.enemy_base import BaseEnemy
from source.utils.superficies import mascara_de
from source.feats.items import Items
from source.systems.status import IMUNIDADES_CHEFE

from .config import CFG
from .setup import HunterSetup
from .states import HunterAI
from .attacks import HunterAttacks
from .vfx import HunterVFX


class Hunter(BaseEnemy, HunterSetup, HunterAI, HunterAttacks, HunterVFX):
    """Mgalekgolo: de frente, Defesa de 90%; pelas costas (±30° do eixo x), vulnerável e brilhando.
    Vira para o jogador com atraso (1,5 s; 2,5 s depois do dash). Os mixins depois de BaseEnemy só
    definem métodos que a base não tem (MRO)."""
    imunidades_status = IMUNIDADES_CHEFE   # sem stun nem lentidão de fora (roteiro §8, item 8)

    def __init__(self, posicao, game, **kwargs):
        super().__init__(posicao, vida_base=CFG.vida, dano_base=CFG.dano_contato, velocidade_base=CFG.velocidade,
                         game=game, sprite_key='hunter', flip_sprite=True)
        self.titulo = "HUNTER, O Guerreiro Mgalekgolo"
        self.is_boss = True

        self.velocidade_animacao_base = 900
        self.setup_animation(estado_inicial='left', velocidade_animacao=self.velocidade_animacao_base)
        self.mostrar_frame_atual()   # a imagem acompanha o lado desde o spawn (a vulnerabilidade depende dele)

        self._agora = relogio.agora()
        self.inicializar_habilidades()
        self.iniciar_vfx()

    def animar(self):
        if self.animacao_congelada:   # recuperação do dash: congelado no frame atual
            return
        agora = relogio.agora()
        if agora - self.ultimo_update_animacao > self.velocidade_animacao:
            self.ultimo_update_animacao = agora
            self.frame_atual = (self.frame_atual + 1) % len(self.sprites[self.estado_animacao])
            self.image = self.sprites[self.estado_animacao][self.frame_atual]
            self.mask = mascara_de(self.image)
            self.rect = self.image.get_rect(center=(round(self.posicao.x), round(self.posicao.y)))

    def morrer(self, grupos=None):
        Items.spawn_drop(
            self.posicao,
            grupos,
            big_shard=((2, 3, 4), (70, 20, 10), 100),
            life_orb=(1, 100, 100),
            upgrade=((1, 2), (99, 1), 100)
        )
        self.kill()

    def update(self, delta_time, paredes=None):
        agora = relogio.agora()
        self._agora, self._dt, self._paredes = agora, delta_time, paredes

        if self.estado_habilidade != 'run':   # no dash ele olha para onde corre
            self.atualizar_orientacao(agora)
        self.executar_estados(agora)
        if self.movimento_livre:
            self.mover_livre(agora, delta_time, paredes)
        self.atualizar_vulnerabilidade()
        self.animar()
