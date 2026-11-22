from ..baseweapon import Arma
from ...grenades import FuelRodGrenade
from source.feats.skills.artilharia.config import ARTILHARIA_PRESETS
from dataclasses import replace


class FuelRod(Arma):
    NOME_ASSET = 'fuel_rod'

    def __init__(self, jogador, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = "Fuel-Rod"
        self.descricao = "Dispara cargas que explodem e deixam uma nuvem venenosa. Se errar, quicam para outro inimigo."
        self.inicializar_stats(self.NOME_ASSET)

    def disparar(self):
        inimigo_alvo = self.encontrar_inimigo_mais_proximo(self.inimigos_grupo, raio_maximo=self.raio_maximo)
        if inimigo_alvo and inimigo_alvo.alive():
            # Stats de upgrade -> config da explosão: impacto (dano) + veneno (dot por `duracao` ms)
            config_escalado = replace(
                ARTILHARIA_PRESETS['plasma_grenade'],
                dano=self.dano,
                dot=True,
                impacto_com_dot=True,
                dano_por_segundo=self.dot,
                duracao_dot=self.duracao,
            )

            FuelRodGrenade(
                posicao_inicial = self.jogador.posicao,
                posicao_alvo    = inimigo_alvo.posicao,
                grupos          = (self.all_sprites,),
                game            = self.game,
                dono            = 'PLAYER',
                inimigos_grupo  = self.inimigos_grupo,
                custom_config   = config_escalado,
                quiques         = self.quique,
            )
            return True
        return False

    def ver_proximo_upgrade(self):
        return self.ver_proximos_upgrades(self.nivel + 1, self.NOME_ASSET)

    def get_estatisticas_para_exibir(self):
        return super().get_estatisticas_para_exibir(self.nivel + 1, self.NOME_ASSET)
