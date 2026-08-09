import pygame
from source.feats.weapons import Arma
from source.feats.projetil import BurstRifle
from .vehicles import Vehicle


class VehicleWarhog(Vehicle):
    """
    Warthog: veículo blindado com metralhadora traseira de cadência alta
    e atropelamento de inimigos.
    """

    def decidir_disparo_veiculo(self, agora):
        if agora - self.ultimo_tiro_burst > self.cooldown_tiro_burst:
            self.ultimo_tiro_burst = agora
            return dict(
                projetil_cls=BurstRifle,
                dano=self.dano_burst,
                velocidade=800,
                tamanho=(28, 28),
            )
        return None


class Warhog(Arma):
    NOME_ASSET = 'warhog'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        deve_criar = kwargs.get('criar_sprite', True)
        self.game = game
        self.all_sprites, self.inimigos_grupo, self.item_grupo = grupos
        self.nome = "Warthog"
        self.descricao = "Veículo blindado UNSC com metralhadora traseira. Aperte V para entrar ou sair."
        self.sprite_veiculo = None
        self._tecla_v_pressionada_anterior = False
        if deve_criar:  # Só cria se for solicitado
            self.equipar()

    def equipar(self):
        if not self.sprite_veiculo:
            self.sprite_veiculo = VehicleWarhog(
                self.jogador, self.all_sprites,
                self.inimigos_grupo, self.item_grupo,
                'warhog'
            )

    def disparar(self):
        return False

    def update(self, delta_time):
        if not self.sprite_veiculo:
            return
        self.sprite_veiculo.update(delta_time)
        self._checar_tecla_chamada()

    def _checar_tecla_chamada(self):
        """Detecta a borda de subida da tecla V (evita alternar 60x/s
        enquanto o jogador segura a tecla)."""
        teclas = pygame.key.get_pressed()
        pressionada = teclas[pygame.K_v]

        if pressionada and not self._tecla_v_pressionada_anterior:
            self._alternar_veiculo()

        self._tecla_v_pressionada_anterior = pressionada

    def _alternar_veiculo(self):
        veiculo = self.sprite_veiculo
        if veiculo.embarcado:
            veiculo.sair()
        elif veiculo.pode_ser_chamado():
            veiculo.entrar()

    def upgrade(self):
        super().upgrade()
        self.aplicar_upgrades(self.nivel, self.NOME_ASSET, target=self.sprite_veiculo)

    def ver_proximo_upgrade(self):
        return self.ver_proximos_upgrades(self.nivel + 1, self.NOME_ASSET, target=self.sprite_veiculo)

    def get_estatisticas_para_exibir(self):
        return super().get_estatisticas_para_exibir(self.nivel + 1, self.NOME_ASSET, target=self.sprite_veiculo)