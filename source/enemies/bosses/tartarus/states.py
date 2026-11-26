"""Decisão do Tartarus: força bruta, sempre para a frente.

- Barreira do Punho de Rukt: com ela ativa, -90% de dano. Golpe pesado que erra o jogador sobrecarrega
  o núcleo (a barreira cai por 3 s) e soma 1 na barra de esquivas; barra cheia, a barreira cai por
  `quebra_ms` (a barra do HUD esvazia com o tempo) e ele reage com o Chieftain Rampage.
- Escolha por alcance (só usa o que alcança): colado, o vórtice; de média, a onda sísmica; longe, o
  salto meteoro. Na Fúria (35%), o Punho de Rukt e a Hammer Run entram, e ele invoca Brutes fora da
  rotina. O ciclo (rotinas, cooldowns, anti-stuck, nota da IA) é da BossBase."""
import math
import random

import pygame

from source.enemies.standard.brute import Brute
from source.feats.particulas.poeira import anel_de_poeira

from .config import CFG

V2 = pygame.math.Vector2


class TartarusAI:
    def preparar_frame(self, delta_time):
        self._resetar_movimento()

    # ------------------------------------------------------------ percepção
    def perceber(self, agora, delta_time):
        super().perceber(agora, delta_time)
        self._atualizar_barreira(agora)
        self._fora_da_rotina(agora)

    # ------------------------------------------------------------ barreira
    @property
    def barreira_ativa(self):
        return self._agora >= self._sem_barreira_ate

    @property
    def quebra_longa(self):
        """A barreira caiu pela barra de esquivas (não pela sobrecarga curta)."""
        return self._quebra is not None

    @property
    def ofegante(self):
        return self._agora < self._ofegante_ate

    def _atualizar_barreira(self, agora):
        ativa = agora >= self._sem_barreira_ate
        if ativa and not self._barreira_estava:
            self._quebra = None
            self.barreira_voltou_vfx()
        self._barreira_estava = ativa

    def _derrubar_barreira(self, ate, longa):
        caiu_agora = self.barreira_ativa
        self._sem_barreira_ate = max(self._sem_barreira_ate, ate)
        self._barreira_estava = False
        if caiu_agora or longa:
            self.barreira_caiu_vfx(longa)

    def sobrecarregar(self):
        """Errou um golpe pesado do martelo: o núcleo gravitacional sobrecarrega (barreira cai por pouco)."""
        self._derrubar_barreira(self._agora + CFG.sobrecarga_ms, longa=False)

    def quebrar_barreira(self):
        """Barra de esquivas cheia: a barreira cai por `quebra_ms` e ele reage com o Rampage."""
        self.esquivas = 0
        self._quebra = (self._agora, self._agora + CFG.quebra_ms)
        self._derrubar_barreira(self._quebra[1], longa=True)
        self._rampage_pendente = True

    def _resolver_golpe(self):
        """Fim de um golpe pesado. Acertou o jogador: nada. Errou: +1 na barra e sobrecarga; a barra
        cheia derruba a barreira (durante a queda longa, não conta)."""
        acertou, self._acertou = self._acertou, False
        if acertou or self.quebra_longa:
            return
        self.esquivas += 1
        if self.esquivas >= CFG.meta_esquivas:
            self.quebrar_barreira()
        else:
            self.sobrecarregar()

    def ajustar_dano_recebido(self, valor, dano):
        if self.barreira_ativa:
            return valor * (1 - CFG.barreira_reducao)
        if self.ofegante:
            return valor * CFG.ofegante_mult
        return valor

    def iniciar(self, nome):
        super().iniciar(nome)
        self._acertou = False

    def _lembrar_dano(self, alvo, dano, valor):
        """Também marca se o golpe em curso acertou o jogador (esquiva = golpe que acabou sem acertar)."""
        if self.decisor is not None:
            super()._lembrar_dano(alvo, dano, valor)
        if dano.fonte is self and alvo is self.jogador and valor > 0 and self.rotina is not None:
            self._acertou = True

    # ------------------------------------------------------------ decisão
    def pensar(self, agora, delta_time):
        """Reações antes da exaustão: a troca de fase e o Rampage (a barreira caiu pela barra)."""
        if self.transicao_pendente:
            self.wait = 0
        elif self._rampage_pendente:
            self._rampage_pendente = False
            self.wait = 0
            self.iniciar('rampage')
            return
        super().pensar(agora, delta_time)

    def _fim(self, nome):
        """Fim de rotina: reagenda e descansa pouco (extremamente ofensivo)."""
        self.agendar(nome)
        self.wait = random.randint(*CFG.descanso_ms)

    # notas (a conta é do Decisor, F3); o `alcance` das HABILIDADES já corta o que não alcança
    def pontuar_vortice(self, ctx):
        return 1.0 if self.dist_jogador() <= CFG.vortice_alcance else 0.0

    def pontuar_salto(self, ctx):
        """Longe: o salto domina, e mais ainda se o jogador está fugindo."""
        return 1.3 if ctx.afastamento > 60 else 1.0

    def pontuar_punho(self, ctx):
        return 1.0 if self.fase_cfg.furia else 0.0

    def pontuar_corrida(self, ctx):
        return 1.0 if self.fase_cfg.furia else 0.0

    # ------------------------------------------------------------ fora da rotina (Fúria)
    def _fora_da_rotina(self, agora):
        if not self._furia or agora < self.cd_brutes or self.no_ar:
            return
        if self._invocar_brutes():
            minimo, maximo = CFG.brutes_cooldown
            self.cd_brutes = agora + self.novo_cooldown(minimo, maximo)
        else:                        # escolta cheia ou sem chão: tenta de novo logo
            self.cd_brutes = agora + 3000

    def _invocar_brutes(self):
        """3 Brutes ao redor dele (respeita o teto). Devolve quantos nasceram."""
        self.brutes_invocados = [b for b in self.brutes_invocados if b.alive()]
        vagas = max(0, CFG.max_brutes - len(self.brutes_invocados))
        posicoes = []
        for _ in range(min(CFG.brutes_por_invocacao, vagas)):
            for _t in range(CFG.spawn_tentativas):
                ang = random.uniform(0, 2 * math.pi)
                p = self.posicao + V2(math.cos(ang), math.sin(ang)) * random.uniform(*CFG.spawn_raio)
                if self.verificar_posicao_valida(p) and all(p.distance_to(o) > 50 for o in posicoes):
                    posicoes.append(p)
                    break
        for pos in posicoes:
            self.brutes_invocados.append(Brute(pos, game=self.game))
            anel_de_poeira(pos, 40, 12)
        return len(posicoes)
