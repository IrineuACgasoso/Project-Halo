from source.feats.weapons import Arma
from .companion import Companheiro

class Arbitro(Arma):
    NOME_ASSET = 'arbiter'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        deve_criar = kwargs.get('criar_sprite', True)
        self.game = game
        self.all_sprites, self.inimigos_grupo, self.item_grupo = grupos
        self.nome = "Árbitro"
        self.descricao = "Um elite aliado que caça inimigos próximos."
        self.sprite_companion = None 
        self.dano = 10
        if deve_criar: # Só cria se for solicitado
            self.equipar()

    def equipar(self):
        if not self.sprite_companion:
            # Passamos 'arbiter' para ele buscar na pasta assets/img/arbiter
            self.sprite_companion = Companheiro(
                self.jogador, self.all_sprites, 
                self.inimigos_grupo, self.item_grupo, 
                'arbiter' 
            )
            self.sprite_companion.dano = self.dano
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
