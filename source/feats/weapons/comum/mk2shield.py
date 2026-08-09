from ..baseweapon import Arma
from ...auras import PlayerAura

class MK2_Shield(Arma):
    NOME_ASSET = 'mk2_shield'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs) 
        self.all_sprites, self.auras_grupos, self.inimigos_grupo = grupos
        self.nome = "Escudo MK-2"
        self.descricao = "Gera um escudo e causa dano por segundo ao redor do jogador."
        self.area_de_dano = None
        self.inicializar_stats(self.NOME_ASSET)

    def equipar(self):
        self.jogador.adicionar_escudo(self.escudo)
        self.jogador.shield_regen = self.shield_regen
        self.jogador.velocidade_regen_escudo = self.velocidade_regen_escudo

        if self.area_de_dano is None:
            self.area_de_dano = PlayerAura(
                jogador=self.jogador,
                raio=self.raio,
                dano_por_segundo=self.dano_por_segundo,
                grupos=(self.all_sprites, self.auras_grupos)
            )

    def disparar(self): 
        return False
    
    def upgrade(self):
        super().upgrade()
        self.aplicar_upgrades(self.nivel, self.NOME_ASSET)
        if self.area_de_dano:
            self.area_de_dano.atualizar_stats(self.raio, self.dano_por_segundo)
        self.jogador.shield_regen = self.shield_regen
        self.jogador.velocidade_regen_escudo = self.velocidade_regen_escudo
        self.jogador.escudo_maximo = self.escudo

    def ver_proximo_upgrade(self):
        return self.ver_proximos_upgrades(self.nivel + 1, self.NOME_ASSET)

    def get_estatisticas_para_exibir(self):
        return super().get_estatisticas_para_exibir(self.nivel + 1, self.NOME_ASSET)
    