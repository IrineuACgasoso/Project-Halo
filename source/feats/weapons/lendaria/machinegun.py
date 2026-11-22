from ..baseweapon import ArmaDeRajada
from ...projetil import BurstRifle

class MachineGun(ArmaDeRajada):
    NOME_ASSET = 'machine_gun'

    def __init__(self, jogador, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = "Machine Gun"
        self.descricao = "Altíssima cadência e um dano constante. Cuidado com o superaquecimento!"
        self.inicializar_stats(self.NOME_ASSET)

    def atirar(self, alvo):
        BurstRifle(
            posicao_inicial = self.jogador.posicao,
            grupos          = (self.all_sprites,),
            jogador         = self.jogador,
            game            = self.game,
            dono            = 'PLAYER',
            tamanho         = (32, 36),
            dano            = self.dano,
            velocidade      = self.velocidade,
            direcao_spread  = self.direcao_para(alvo),
        )

    def ver_proximo_upgrade(self):
        return self.ver_proximos_upgrades(self.nivel + 1, self.NOME_ASSET)

    def get_estatisticas_para_exibir(self):
        return super().get_estatisticas_para_exibir(self.nivel + 1, self.NOME_ASSET)