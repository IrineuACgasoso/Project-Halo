import random
import pygame
from source.systems.levelup import TelaDeUpgrade
from source.systems.estados import LEVEL_UP
from source.systems.status import Cura, Escudo, aplicar

class PlayerScaling:
    def ganhar_xp(self, quantidade):
        """Soma XP e processa TODOS os level-ups devidos.
        Antes: um ganho grande (boss, vários orbes no mesmo frame) subia no máximo 1 nível
        por chamada e vários level-ups no mesmo frame sobrescreviam a tela de escolha."""
        self.experiencia_atual += quantidade
        while self.experiencia_atual >= self.experiencia_level_up:
            self.level_up()

    def level_up(self):
        self.experiencia_atual -= self.experiencia_level_up
        self.contador_niveis += 1
        self.vida_maxima += 25
        self.velocidade += 10
        self.pontuacao += 100
        aplicar(self, Cura(self.vida_maxima / 4))
        falta_escudo = self.escudo_maximo - self.escudo_atual
        if falta_escudo > 0:
            aplicar(self, Escudo(falta_escudo))   # enche: o Escudo para no máximo
        self.experiencia_level_up = self.experiencia_level_up_base + 10 * self.contador_niveis

        self._enfileirar_upgrade(None)

    def ativar_upgrade_forcado(self, id_forcado=None):
        """Enfileira uma tela de upgrade mostrando UMA única arma. Se `id_forcado`
        vier preenchido (o item já sabia qual arma era desde o spawn), usa
        ele direto. Caso contrário, sorteia entre as armas já possuídas
        (fallback pra drops antigos/manuais sem id definido)."""
        if not self.armas:
            self.level_up()
            return

        id_escolhido = id_forcado if id_forcado in self.armas else random.choice(sorted(self.armas.keys()))
        self._enfileirar_upgrade(id_escolhido)

    # ── Fila de telas de upgrade ───────────────────────────────────────────
    def _enfileirar_upgrade(self, id_forcado):
        self.fila_upgrades.append(id_forcado)
        self.abrir_proxima_tela_de_upgrade()

    def abrir_proxima_tela_de_upgrade(self):
        """Abre a próxima tela pendente, se não houver uma aberta. O EventManager chama
        isto ao fechar uma tela, encadeando level-ups acumulados."""
        if not self.fila_upgrades or self.game.sessao.tela_de_upgrade_ativa is not None:
            return
        id_forcado = self.fila_upgrades.pop(0)
        self.game.mudar_estado(LEVEL_UP)
        self.game.sessao.tela_de_upgrade_ativa = TelaDeUpgrade(
            self.game.tela, self, self.game, id_arma_forcada=id_forcado
        )
