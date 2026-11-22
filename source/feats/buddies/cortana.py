from source.feats.weapons import Arma
from .companion import Companheiro
from source.systems.status import BuffVelocidade, aplicar


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
        # O bônus é um buff sem fim pelo sistema de status; a chave é esta Cortana: reaplicar só atualiza
        dono_stats = self.sprite_companion if self.sprite_companion is not None else self
        bonus = dono_stats.jogador_speed_bonus
        if bonus > 0:
            aplicar(self.jogador, BuffVelocidade(bonus / 100), chave=self)

    def ver_proximo_upgrade(self):
        return self.ver_proximos_upgrades(self.nivel + 1, self.NOME_ASSET, target=self.sprite_companion)

    def get_estatisticas_para_exibir(self):
        return super().get_estatisticas_para_exibir(self.nivel + 1, self.NOME_ASSET, target=self.sprite_companion)
    
    def disparar(self): pass
    def update(self, delta_time): pass

    