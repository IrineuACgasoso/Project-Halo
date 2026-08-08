from source.feats.weapons import Arma
from .companion import Companheiro


class Cortana(Arma):
    NOME_ASSET = 'cortana'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        deve_criar = kwargs.get('criar_sprite', True)
        self.all_sprites, self.inimigos_grupo, self.item_grupo = grupos
        self.nome = "Cortana"
        self.descricao = "Busca itens e XP próximos a você, além de conceder um bônus de velocidade."

        self.sprite_companion = None
        self.itens_reservados = set()
        if deve_criar: # Só cria se for solicitado
            self.equipar()

    def equipar(self):
        if not self.sprite_companion:
            # Passamos 'cortana' para ele buscar na pasta assets/img/cortana
            self.sprite_companion = Companheiro(
                self.jogador, self.all_sprites, 
                self.inimigos_grupo, self.item_grupo, 
                'cortana'
            )
            self.sprite_companion.arma_parent = self

    def upgrade(self):
        super().upgrade()
        self.aplicar_upgrades(self.nivel, self.NOME_ASSET, target=self.sprite_companion)
        self.jogador.velocidade += 10

    def ver_proximo_upgrade(self):
        return self.ver_proximos_upgrades(self.nivel + 1, self.NOME_ASSET, target=self.sprite_companion)

    def get_estatisticas_para_exibir(self):
        return super().get_estatisticas_para_exibir(self.nivel + 1, self.NOME_ASSET, target=self.sprite_companion)
    
    def disparar(self): pass
    def update(self, delta_time): pass

    