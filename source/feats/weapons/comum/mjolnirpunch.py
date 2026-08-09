from ..baseweapon import Arma

class MjolnirPunch(Arma):
    NOME_ASSET = 'mjolnir_punch'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.nome = "Mjolnir Punch"
        self.descricao = "Contra-ataque Spartan rápido que neutraliza rapidamente pequenas ameaças."
        self.inicializar_stats(self.NOME_ASSET)
        self.jogador.configurar_espinhos(dano=self.espinhos, cooldown=self.cooldown)

    def disparar(self):
        return False

    def update(self, delta_time):
        self.jogador.atualizar_espinhos()

    def upgrade(self):
        super().upgrade()
        self.aplicar_upgrades(self.nivel, self.NOME_ASSET)
        self.jogador.configurar_espinhos(dano=self.espinhos, cooldown=self.cooldown)

    def ver_proximo_upgrade(self):
        return self.ver_proximos_upgrades(self.nivel + 1, self.NOME_ASSET)

    def get_estatisticas_para_exibir(self):
        return super().get_estatisticas_para_exibir(self.nivel + 1, self.NOME_ASSET)

