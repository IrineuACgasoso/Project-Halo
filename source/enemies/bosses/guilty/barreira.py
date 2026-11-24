"""A barreira do Monitor: enquanto está de pé, nada o fere (só a luz visível dele mesmo, na fase 2)."""
from source.enemies.standard.sentinel import Sentinel
from source.feats.auras import EnergyAura
from source.systems.dano import AREA, Dano

from .config import CFG

_FOLGA = 1e-9   # a vida para um fio abaixo do limiar: conta em float, `<=` precisa valer


class GuiltyBarreira:
    @property
    def barreira_ativa(self):
        return self.barreira is not None

    @property
    def alvejavel(self):
        """Com a barreira de pé, ninguém mira nele: as armas atirariam no escudo, não nas sentinelas."""
        return super().alvejavel and not self.barreira_ativa

    def erguer_barreira(self, efeito=True):
        if self.barreira_ativa:
            return
        self.is_invulneravel = True
        self.barreira = EnergyAura(owner=self, raio=CFG.barreira_raio, dano_contato=CFG.barreira_dano,
                                   game=self.game, cor_base=CFG.barreira_cor, impenetravel=True,
                                   bloqueia_tiros=True, empurrao_max=CFG.barreira_empurrao_max)
        if efeito:
            self.efeito_da_barreira()

    def derrubar_barreira(self):
        if not self.barreira_ativa:
            return
        self.is_invulneravel = False
        self.barreira.kill()
        self.barreira = None
        self.efeito_da_barreira()
        self.ao_quebrar_escudo()

    # ------------------------------------------------------------ fase 1: 40 sentinelas
    def contar_sentinela(self, inimigo):
        """Assinante de INIMIGO_MORREU: toda sentinela derrotada conta (inclusive as da horda)."""
        if not (self.fase == 1 and self.barreira_ativa and self.alive() and isinstance(inimigo, Sentinel)):
            return
        self.sentinelas_derrotadas += 1
        if self.sentinelas_derrotadas >= CFG.sentinelas_para_cair:
            self.encerrar_invocacoes()
            self.derrubar_barreira()
            self.permitir_spawns_normais = True
            self.ronda_ate = 0     # acelera já num caminho novo

    # ------------------------------------------------------------ fase 2: a própria luz
    def atingido_pela_luz(self, aviso):
        """A luz visível estourou: se ele estava dentro, perde 5% da vida máxima, com barreira e tudo."""
        if self.fase != 2 or not self.barreira_ativa or self.em_teleporte:
            return False
        alcance = aviso.cfg.raio_explosao + CFG.raio_corpo
        if self.posicao.distance_squared_to(aviso.posicao) > alcance * alcance:
            return False
        self.receber_dano(Dano(self.vida_maxima * CFG.luz_dano_no_guilty, AREA, fonte=self))
        self.efeito_do_acerto()
        return True

    # ------------------------------------------------------------ contrato de dano
    def ajustar_dano_recebido(self, valor, dano):
        """Barreira de pé: só o golpe dele mesmo (a luz visível) entra."""
        if self.barreira_ativa and dano.fonte is not self:
            return None
        return valor

    @property
    def piso_de_vida(self):
        """A vida não passa do começo da próxima fase: nenhum golpe pula uma fase."""
        if self.fase >= len(self.FASES):
            return 0.0
        return self.FASES[self.fase].limiar_vida * self.vida_maxima * (1 - _FOLGA)

    def absorver_dano(self, valor):
        piso = min(self.piso_de_vida, self.vida)
        super().absorver_dano(valor)
        self.vida = max(self.vida, piso)
