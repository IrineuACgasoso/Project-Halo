from ..baseweapon import Arma
from ...projetil import BurstRifle

class AssaultRifle(Arma):
    NOME_ASSET = 'assault_rifle'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = 'Rifle de Assalto'
        self.descricao = """Rifle UNSC de cadência elevada"""
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.inicializar_stats(self.NOME_ASSET)
        
    def disparar(self):
        inimigo_alvo = self.encontrar_inimigo_mais_proximo(self.inimigos_grupo, raio_maximo=700)
        if inimigo_alvo and inimigo_alvo.alive():
            direcao_vetor = self.direcao_para(inimigo_alvo)
            
            for _ in range(self.projeteis_por_disparo):
                BurstRifle(
                    posicao_inicial = self.jogador.posicao,
                    grupos          = (self.all_sprites,), 
                    jogador         = self.jogador,
                    game            = self.game,
                    dono            ='PLAYER',
                    tamanho         = (24, 24),
                    dano            = self.dano,
                    velocidade      = self.velocidade_projetil,
                    direcao_spread  = direcao_vetor
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
    