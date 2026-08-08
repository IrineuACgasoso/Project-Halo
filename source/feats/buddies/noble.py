from source.feats.weapons import Arma
from .companion import Companheiro

class NobleVI(Arma):
    NOME_ASSET = 'noble'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        deve_criar = kwargs.get('criar_sprite', True)
        self.game = game
        self.all_sprites, self.inimigos_grupo, self.item_grupo = grupos
        self.nome = "Noble VI"
        self.descricao = "Soldado Spartan legendário na Queda de Reach."
        self.sprite_companion = None 
        if deve_criar: # Só cria se for solicitado
            self.equipar()

    def equipar(self):
        if not self.sprite_companion:
            # Passamos 'noble' para ele buscar na pasta assets/img/arbiter
            self.sprite_companion = Companheiro(
                self.jogador, self.all_sprites, 
                self.inimigos_grupo, self.item_grupo, 
                'noble' 
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
