import random
import pygame
from source.systems.levelup import TelaDeUpgrade, gerar_opcoes
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
        aplicar(self, Cura(self.vida_maxima / 2))
        falta_escudo = self.escudo_maximo - self.escudo_atual
        if falta_escudo > 0:
            aplicar(self, Escudo(falta_escudo))   # enche: o Escudo para no máximo
        self.experiencia_level_up = self.experiencia_level_up_base + 10 * self.contador_niveis

        self._enfileirar_upgrade(None)

    def ativar_upgrade_forcado(self, id_forcado=None):
        """Enfileira uma tela de upgrade mostrando UMA única arma: `id_forcado` (o item já
        sabia qual arma era desde o spawn) se ela ainda puder subir; senão, sorteia entre as
        armas abaixo do nível máximo. Sem nenhuma, não abre tela (recompensa_sem_upgrade)."""
        if not self.armas:
            self.level_up()
            return

        id_escolhido = self._arma_para_upgrade_forcado(id_forcado)
        if id_escolhido is None:
            self.recompensa_sem_upgrade()
            return
        self._enfileirar_upgrade(id_escolhido)

    def _arma_para_upgrade_forcado(self, id_preferido):
        """`id_preferido` se a arma ainda pode subir; senão, uma sorteada entre as que podem
        (None se nenhuma pode)."""
        candidatas = sorted(i for i, arma in self.armas.items() if not arma.no_maximo)
        if not candidatas:
            return None
        return id_preferido if id_preferido in candidatas else random.choice(candidatas)

    def recompensa_sem_upgrade(self):
        """Level-up ou item `upgrade` sem nenhuma arma para melhorar (todas no máximo).
        Provisório (roteiro E6): não abre tela; o nível e os pontos do item já foram dados."""
        # TODO(itens temporários): o recurso de itens temporários e boosts pluga aqui (roteiro §7.1)

    # ── Fila de telas de upgrade ───────────────────────────────────────────
    def _enfileirar_upgrade(self, id_forcado):
        self.fila_upgrades.append(id_forcado)
        self.abrir_proxima_tela_de_upgrade()

    def abrir_proxima_tela_de_upgrade(self):
        """Abre a próxima tela pendente, se não houver uma aberta. O EventManager chama
        isto ao fechar uma tela, encadeando level-ups acumulados. Level-up sem nenhuma
        opção não abre tela vazia: vira recompensa_sem_upgrade e passa ao próximo da fila."""
        while self.fila_upgrades and self.game.sessao.tela_de_upgrade_ativa is None:
            id_forcado = self.fila_upgrades.pop(0)
            if id_forcado is None:
                opcoes = gerar_opcoes(self)
            else:
                # a arma pode ter chegado ao máximo numa tela anterior da fila
                id_forcado = self._arma_para_upgrade_forcado(id_forcado)
                opcoes = [id_forcado] if id_forcado is not None else []
            if not opcoes:
                self.recompensa_sem_upgrade()
                continue
            self.game.mudar_estado(LEVEL_UP)
            self.game.sessao.tela_de_upgrade_ativa = TelaDeUpgrade(
                self.game.tela, self, self.game, id_arma_forcada=id_forcado, ids_das_opcoes=opcoes
            )
