from ..baseweapon import ArmaDeRajada
from ...projetil import DizimatorBullet


class Dizimator(ArmaDeRajada):
    NOME_ASSET = 'dizimator'

    def __init__(self, jogador, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = 'Dizimator'
        self.descricao = """Arma de alto calibre que atira rajadas poderosas a curtas distâncias."""
        self.inicializar_stats(self.NOME_ASSET)

    def atirar(self, alvo):
        DizimatorBullet(
            posicao_inicial = self.jogador.posicao,
            grupos          = (self.all_sprites,),
            jogador         = self.jogador,
            game            = self.game,
            dono            = 'PLAYER',
            tamanho         = (32, 32),
            dano            = self.dano,
            velocidade      = self.velocidade_projetil,
            direcao_spread  = self.direcao_para(alvo),
        )

    def upgrade(self):
        super().upgrade()
        self.aplicar_upgrades(self.nivel, self.NOME_ASSET)

    def ver_proximo_upgrade(self):
        return self.ver_proximos_upgrades(self.nivel + 1, self.NOME_ASSET)

    def get_estatisticas_para_exibir(self):
        return super().get_estatisticas_para_exibir(self.nivel + 1, self.NOME_ASSET)