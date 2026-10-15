from ..baseweapon import Arma
from ...grenades import PlasmaGrenade
from source.feats.skills.artilharia.config import ARTILHARIA_PRESETS
from dataclasses import replace


class FuelRod(Arma):
    NOME_ASSET = 'fuel_rod'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = "Fuel-Rod"
        self.descricao = "Arremessa granadas de plasma que grudam no primeiro inimigo tocado."
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.inicializar_stats(self.NOME_ASSET)

    def disparar(self):
        inimigo_alvo = self.encontrar_inimigo_mais_proximo(self.inimigos_grupo, raio_maximo=self.raio_maximo)
        if inimigo_alvo and inimigo_alvo.alive():
            # Dano escala com upgrade: clona o preset base trocando só o dano
            config_escalado = replace(ARTILHARIA_PRESETS['plasma_grenade'], dano=self.dano)

            PlasmaGrenade(
                posicao_inicial = self.jogador.posicao,
                posicao_alvo    = inimigo_alvo.posicao,
                grupos          = (self.all_sprites,),
                game            = self.game,
                dono            = 'PLAYER',
                inimigos_grupo  = self.inimigos_grupo,
                custom_config   = config_escalado
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
