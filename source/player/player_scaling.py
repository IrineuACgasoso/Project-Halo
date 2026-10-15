import random
import pygame
from source.systems.levelup import TelaDeUpgrade

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
        self.curar(self.vida_maxima / 4)
        self.escudo_atual = self.escudo_maximo
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
        if not self.fila_upgrades or self.game.tela_de_upgrade_ativa is not None:
            return
        id_forcado = self.fila_upgrades.pop(0)
        self.game.estado_do_jogo = 'level_up'
        self.game.tela_de_upgrade_ativa = TelaDeUpgrade(
            self.game.tela, self, self.game, id_arma_forcada=id_forcado
        )

    # ── Buff de cooldown ───────────────────────────────────────────────────
    def adicionar_tempo_buff(self, segundos):
        self.buff_timer += segundos

    @staticmethod
    def _aplicar_buff_cooldown(arma):
        cd = getattr(arma, 'cooldown', None)
        if cd is None or cd == float('inf') or getattr(arma, '_buff_cd_aplicado', False):
            return
        arma.cooldown = cd / 2
        arma._buff_cd_aplicado = True

    @staticmethod
    def _remover_buff_cooldown(arma):
        if getattr(arma, '_buff_cd_aplicado', False):
            arma.cooldown *= 2
            arma._buff_cd_aplicado = False

    def atualizar_buff(self, delta_time):
        if self.buff_timer > 0:
            self.buff_timer -= delta_time
            self.buff_cooldown_ativo = True
            # Idempotente: armas obtidas DURANTE o buff também recebem o bônus.
            for arma in self.armas.values():
                self._aplicar_buff_cooldown(arma)

        elif self.buff_cooldown_ativo:
            self.buff_timer = 0
            self.buff_cooldown_ativo = False
            # Antes: restaurava `cooldown_original`, apagando upgrades feitos durante o buff.
            for arma in self.armas.values():
                self._remover_buff_cooldown(arma)
