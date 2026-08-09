from source.feats.weapons import Arma
from source.feats.projetil import BurstRifle, HeavyBurst
from .companion import Companheiro


class CompanheiroNoble(Companheiro):
    """
    Companheiro do Noble VI: troca de arma conforme a distância do inimigo.
    Perto -> rifle de rajada (rápido, menos dano). Longe -> sniper (lento, mais dano).
    As faixas são mutuamente exclusivas (baseadas na distância), diferente do
    comportamento padrão da classe base, que prioriza por cooldown.
    """

    def decidir_disparo(self, dist_sq, agora):
        dist_rifle_sq = self.range_rifle ** 2
        dist_sniper_sq = self.range_sniper ** 2

        if dist_sq <= dist_rifle_sq:
            if agora - self.ultimo_tiro_burst > self.cooldown_tiro_burst:
                self.ultimo_tiro_burst = agora
                return dict(
                    projetil_cls=BurstRifle,
                    dano=self.dano_burst,
                    velocidade=700,
                    tamanho=(24, 24),
                )
        elif dist_sq <= dist_sniper_sq:
            if agora - self.ultimo_tiro_sniper > self.cooldown_tiro_sniper:
                self.ultimo_tiro_sniper = agora
                return dict(
                    projetil_cls=HeavyBurst,
                    dano=self.dano_sniper,
                    velocidade=1500,
                    tamanho=(96, 28),
                )

        return None


class NobleVI(Arma):
    NOME_ASSET = 'noble'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        deve_criar = kwargs.get('criar_sprite', True)
        self.game = game
        self.all_sprites, self.inimigos_grupo, self.item_grupo = grupos
        self.nome = "Noble VI"
        self.descricao = "Soldado Spartan legendário na Queda de Reach. Troca de rifle para sniper conforme a distância do alvo."
        self.sprite_companion = None
        if deve_criar: # Só cria se for solicitado
            self.equipar()

    def equipar(self):
        if not self.sprite_companion:
            # Passamos 'noble' para ele buscar na pasta assets/img/noble
            self.sprite_companion = CompanheiroNoble(
                self.jogador, self.all_sprites,
                self.inimigos_grupo, self.item_grupo,
                'noble'
            )
            self.sprite_companion.arma_parent = self

    def upgrade(self):
        super().upgrade()
        self.aplicar_upgrades(self.nivel, self.NOME_ASSET, target=self.sprite_companion)

    def ver_proximo_upgrade(self):
        return self.ver_proximos_upgrades(self.nivel + 1, self.NOME_ASSET, target=self.sprite_companion)

    def get_estatisticas_para_exibir(self):
        return super().get_estatisticas_para_exibir(self.nivel + 1, self.NOME_ASSET, target=self.sprite_companion)

    def disparar(self): pass
    def update(self, delta_time): pass