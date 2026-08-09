from ..baseweapon import Arma
from ...projetil import HeavyBurst

class SniperRifle(Arma):
    NOME_ASSET = 'sniper_rifle'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = 'Sniper Rifle'
        self.descricao = """Rifle de precisão UNSC, cadência lenta e dano devastador"""
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.inicializar_stats(self.NOME_ASSET)

    def disparar(self):
        inimigo_alvo = self.encontrar_inimigo_mais_forte(self.inimigos_grupo, raio_maximo=1200)
        if inimigo_alvo and inimigo_alvo.alive():
            direcao_vetor = (inimigo_alvo.posicao - self.jogador.posicao).normalize()

            HeavyBurst(
                posicao_inicial = self.jogador.posicao,
                grupos          = (self.all_sprites,),
                jogador         = self.jogador,
                game            = self.game,
                dono            = 'PLAYER',
                tamanho         = (96, 28),
                dano            = self.dano,
                velocidade      = self.velocidade_projetil,
                direcao_spread  = direcao_vetor,
                piercing        = self.piercing
            )
            return True
        return False

    def upgrade(self):
        super().upgrade()
        self.aplicar_upgrades(self.nivel, self.NOME_ASSET)

    def ver_proximo_upgrade(self):
        return self.ver_proximos_upgrades(self.nivel + 1, self.NOME_ASSET)

    def get_estatisticas_para_exibir(self):
        return super().get_estatisticas_para_exibir(self.nivel + 1, self.NOME_ASSET)

