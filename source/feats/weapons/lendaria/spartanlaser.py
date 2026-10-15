from ..baseweapon import Arma
from ...projetil import LaserBlast

class SpartanLaser(Arma):
    NOME_ASSET = 'spartan_laser'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = 'Spartan Laser'
        self.descricao = """Feixe de energia concentrada de altíssimo alcance"""
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.inicializar_stats(self.NOME_ASSET)

    def disparar(self):
        inimigo_alvo = self.encontrar_inimigo_mais_forte(self.inimigos_grupo, raio_maximo=self.raio_maximo)
        if inimigo_alvo and inimigo_alvo.alive():
            direcao_vetor = self.direcao_para(inimigo_alvo)

            LaserBlast(
                posicao_inicial = self.jogador.posicao,
                grupos          = (self.all_sprites,),
                jogador         = self.jogador,
                game            = self.game,
                dono            = 'PLAYER',
                tamanho         = (260, 30),
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

