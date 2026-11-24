"""Decisão do Scarab. As armas e os passos correm por fora (armas.py, movement.py); aqui só entram os
golpes do corpo, que punem quem se esconde embaixo dele ou acampa numa pata."""
import random

from .config import CENTRO_CHAO, CFG


class ScarabAI:
    def perceber(self, agora, delta_time):
        super().perceber(agora, delta_time)
        self.centro_chao = self.no_mundo(CENTRO_CHAO)
        self.medir_acampamento(delta_time)

    def preparar_frame(self, delta_time):
        agora = self._agora
        if not (self.desabado or self.morrendo):
            self.atualizar_passo(agora)
        if self.rotina is None:
            self.andar()
        else:
            self.parar()               # as rotinas são golpes parados
        self.atualizar_armas(agora, delta_time)
        self.atualizar_vfx(agora)

    def checar_fase(self):
        anterior = self.fase
        super().checar_fase()
        if self.fase != anterior:
            self.entrar_na_fase()

    def escolher_habilidade(self, agora):
        if self.no_passo:              # espera as patas chegarem ao chão
            return None
        pesos = {}
        if self.jogador_sob and self.pronto('stomp'):
            pesos['stomp'] = CFG.pesos['stomp']
        if self.pata_acampada is not None and self.pronto('sismica'):
            pesos['sismica'] = CFG.pesos['sismica']
        if not pesos:
            return None
        pesos['esperar'] = CFG.pesos['esperar']
        escolha = random.choices(list(pesos), weights=list(pesos.values()))[0]
        if escolha == 'esperar':
            self.wait = random.randint(*CFG.esperar_ms)
            return None
        return escolha
