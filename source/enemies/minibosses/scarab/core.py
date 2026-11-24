from source.enemies.base.boss import BossBase

from .armas import ScarabArmas
from .attacks import ScarabAttacks
from .config import CFG, CLIPS, ESTADOS, FASES, VARIANTES
from .corpo import mascara
from .movement import ScarabMovement
from .patas import ScarabPatas
from .setup import ScarabSetup
from .states import ScarabAI
from .vfx import ScarabVFX


class Scarab(ScarabMovement, ScarabPatas, ScarabAI, ScarabArmas, ScarabAttacks, ScarabVFX, ScarabSetup, BossBase):
    """Andador gigante, sem dano de contato: passa-se por baixo dele. Mixins ANTES de BossBase (MRO).

    - Blindado: só as três patas visíveis sofrem dano, cada uma no ângulo dela.
    - Pata quebrada: desaba e expõe o núcleo, atrás; depois se ergue, regenera a pata e recomeça.
    - Abaixo de 30%: sobrecarga crítica. Vida zerada: colapso em cadeia e detonação."""
    FASES = FASES
    COOLDOWNS = CFG.cooldown
    COOLDOWN_INICIAL = CFG.cooldown_inicial
    ESTADOS = ESTADOS
    CLIPS = CLIPS

    def __init__(self, posicao, game, **kwargs):
        super().__init__(posicao, vida_base=CFG.vida, dano_base=0, velocidade_base=CFG.velocidade,
                         game=game, sprite_key='scarab', flip_sprite=True)   # a arte olha para a esquerda
        self.titulo = "SCARAB, Plataforma de Assalto Covenant"
        self.inicializar_habilidades()
        self.iniciar_vfx()
        self.atualizar_mascara()
        game.camera.definir_zoom(CFG.zoom, CFG.zoom_entrada_ms)

    @property
    def variante_arte(self):
        return VARIANTES[self.fase - 1]

    @property
    def y_desenho(self):
        """Por cima de tudo que estiver à frente dos pés dele: o jogador some por baixo (Renderer)."""
        return self.rect.bottom

    def atualizar_mascara(self):
        self.mask = mascara(self.pose, self.animador.lado)

    def animar(self):
        super().animar()
        self.atualizar_mascara()       # a da pose e do lado de agora (o animador só conhece a de pé)
