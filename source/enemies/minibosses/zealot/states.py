"""Decisão do Zealot: confia no escudo, teme pela vida.

Com escudo, ataca por pesos conforme a distância. Sem escudo, a primeira coisa que faz ao ficar livre
(nunca no meio de um golpe) é fugir invisível. O ciclo (rotinas, cooldowns, anti-stuck) é da BossBase."""
import random

from .config import CFG


class ZealotAI:
    def preparar_frame(self, delta_time):
        self.atualizar_invisibilidade(delta_time)
        # Padrão de todo frame: perseguir andando, olhando para o jogador. As rotinas sobrescrevem.
        self._ir(None)
        self._olhar_x = None
        self.animador.tocar('andar')

    def orientar(self):
        if self._olhar_x is not None:
            self.set_sprite_direction(self._olhar_x)
        else:
            super().orientar()

    @property
    def sem_escudo(self):
        return self.escudo_atual <= 0

    def faixa_de_distancia(self):
        dist_sq = self.contexto.dist_sq
        if dist_sq <= CFG.dist_perto ** 2:
            return 'perto'
        return 'medio' if dist_sq <= CFG.dist_medio ** 2 else 'longe'

    def pensar(self, agora, delta_time):
        """Sem escudo, fugir vem antes de tudo (inclusive da pausa pós-habilidade)."""
        if self.sem_escudo:
            self.wait = 0
            self.iniciar('defensiva')
            return
        super().pensar(agora, delta_time)

    def movimento_ocioso(self, agora):
        if self.faixa_de_distancia() == 'longe':
            self._ir(self.dir_jogador(), CFG.mult_sprint)
            self.animador.tocar('correr')

    def escolher_habilidade(self, agora):
        pesos = {nome: peso for nome, peso in CFG.pesos[self.faixa_de_distancia()].items()
                 if nome == 'perseguir' or self.pronto(nome)}
        if not set(pesos) - {'perseguir'}:
            return None
        escolha = random.choices(list(pesos), weights=list(pesos.values()))[0]
        if escolha == 'perseguir':
            self.wait = random.randint(*CFG.perseguir_ms)
            return None
        return escolha
