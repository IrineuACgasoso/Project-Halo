from ..baseweapon import Arma
from ...projetil import HeavyBurst

class SidekickPistol(Arma):
    NOME_ASSET = 'sidekick_pistol'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = 'Sidekick Pistol'
        self.descricao = """Pistola padrão de elite, causa um grande dano com uma frequência alta."""
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.inicializar_stats(self.NOME_ASSET)

    def disparar(self):
        inimigo_alvo = self.encontrar_inimigo_mais_proximo(self.inimigos_grupo, raio_maximo=600)
        if inimigo_alvo and inimigo_alvo.alive():
            direcao_vetor = self.direcao_para(inimigo_alvo)

            HeavyBurst(
                posicao_inicial = self.jogador.posicao,
                grupos          = (self.all_sprites,),
                jogador         = self.jogador,
                game            = self.game,
                dono            = 'PLAYER',
                tamanho         = (48, 16),
                dano            = self.dano,
                velocidade      = self.velocidade_projetil,
                direcao_spread  = direcao_vetor,
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
