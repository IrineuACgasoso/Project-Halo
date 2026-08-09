from ..baseweapon import Arma
from ...projetil import Brick

class BrickLauch(Arma):
    NOME_ASSET = 'brick' # Removido o acento perigoso

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = "Tijolo"
        self.descricao = """Arma canônicamente associada ao Master Chief."""
        self.all_sprites, self.grupo_projeteis, self.grupo_inimigos = grupos
        self.inicializar_stats(self.NOME_ASSET)

    def disparar(self):
        inimigo = self.encontrar_inimigo_mais_proximo(self.grupo_inimigos, raio_maximo=1200)        
        if inimigo:
            direcao_tiro = (inimigo.posicao - self.jogador.posicao).normalize()
            Brick(
                posicao_inicial=self.jogador.posicao,
                grupos=(self.all_sprites,),
                jogador=self.jogador,
                game=self.game,
                direcao=direcao_tiro,
                dano=self.dano,
                velocidade=self.velocidade,
                rebatidas=self.rebatidas
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
    
