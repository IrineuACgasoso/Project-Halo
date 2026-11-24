from source.systems.gameclock import relogio

from .config import CENTRO_CHAO, CFG, PES
from .feixe import FeixeDeFoco
from .patas import Pata


class ScarabSetup:
    def inicializar_habilidades(self):
        """Estado só do Scarab (o do motor e os cooldowns são da BossBase)."""
        agora = relogio.agora()
        self.is_inofensivo = True          # nenhum dano de contato, nunca: passa-se por baixo dele
        self.radius = CFG.raio_aura        # `collide_circle` das auras do jogador

        # Corpo
        self.pose = 'em_pe'
        self.impulso_y = 0.0               # o corpo sobe antes do body stomp
        self.mira_torreta = self.animador.lado
        self.torreta_recuada = False

        # Patas: a vida delas acompanha a escala de dificuldade da dele
        vida_pata = CFG.vida_pata * self.vida_maxima / CFG.vida
        self.patas = {nome: Pata(nome, self, vida_pata) for nome in PES}
        self.pata_quebrada = None
        self.desabado = False              # da quebra da pata até estar de pé de novo
        self.nucleo_exposto = False
        self.nucleo_ate = 0
        self.centro_chao = self.no_mundo(CENTRO_CHAO)

        # Passos e orientação
        self.avisos = []                   # artilharias dele que ainda não estouraram
        self.par_do_passo = 0
        self.pousa_em = 0
        self.proximo_passo_em = agora + CFG.apoio_ms[0]
        self.virar_em = None               # ms em que o timer de virar vence (None = parado)

        # Armas
        self.feixe = FeixeDeFoco(self, CFG.feixe)
        self.feixe_estado = 'espera'       # 'espera' | 'carga' | 'disparo'
        self.feixe_fim = 0
        self.proximo_feixe = agora + self.novo_cooldown(*CFG.feixe.cooldown_ms)
        self.tiros_restantes = 0
        self.proximo_tiro = 0
        self.proxima_rajada = agora + self.novo_cooldown(*CFG.torreta_cooldown_ms)
        self.guarnicao = []
        self.desembarque_em_curso = None   # ms em que a escotilha termina de abrir
        self.proximo_desembarque = agora + CFG.desembarque_inicial_ms

        # Morte
        self.morrendo = False
        self.grupos_do_drop = None
