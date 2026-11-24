"""Patas do Scarab e o dano por ângulo (a ideia das costas do Hunter, com vários cones).

De pé, o que decide onde o tiro entra é o ângulo em que o jogador está, a partir do centro do chão: em
frente a uma das três patas visíveis, o dano vai para a vida dela; fora disso, a carapaça barra quase
tudo. Pata zerada = ele desaba e o núcleo, atrás, fica exposto (`rotina_queda`)."""
import pygame

from source.utils.vetores import no_cone

from .config import CFG, COS_NUCLEO, COS_PATA, EIXO_NUCLEO, EIXO_PATA, PATAS_VULNERAVEIS, PES

V2 = pygame.math.Vector2


class Pata:
    def __init__(self, nome, scarab, vida):
        self.nome = nome
        self.scarab = scarab
        self.vida_maxima = vida
        self.vida = vida
        self.erguida = False
        self.extra_y = 0.0        # px acima da arte erguida (pisada sísmica)
        self.acampado_ms = 0.0    # há quanto tempo o jogador está colado nela

    @property
    def posicao(self):
        """Onde ela pisa, no mundo (a artilharia do passo fica presa aqui)."""
        return self.scarab.no_mundo(PES[self.nome])

    @property
    def vulneravel(self):
        return self.nome in PATAS_VULNERAVEIS

    @property
    def quebrada(self):
        return self.vida <= 0

    @property
    def danificada(self):
        return self.vulneravel and self.vida <= self.vida_maxima * CFG.pata_danificada

    def ferir(self, valor):
        self.vida = max(0, self.vida - valor)

    def regenerar(self):
        self.vida = self.vida_maxima


class ScarabPatas:
    # ------------------------------------------------------------ geometria
    @property
    def espelho(self):
        """1 olhando para a esquerda (como a arte), -1 para a direita."""
        return 1 if self.animador.lado == 'left' else -1

    def no_mundo(self, ponto):
        """Um ponto da arte (px, olhando para a esquerda) em coordenadas do mundo."""
        meio = self.rect.width / 2
        return V2(self.posicao.x + self.espelho * (ponto[0] - meio), self.posicao.y + ponto[1] - meio)

    @property
    def jogador_sob(self):
        """O jogador está por baixo dele?"""
        return self.centro_chao.distance_squared_to(self.jogador.posicao) <= CFG.raio_sob ** 2

    # ------------------------------------------------------------ ângulos
    def _no_angulo(self, eixo, cos_meio):
        return no_cone(self.centro_chao, (eixo[0] * self.espelho, eixo[1]), self.jogador.posicao, cos_meio)

    @property
    def pata_exposta(self):
        """A pata que o jogador alcança de onde está (ou None: só carapaça)."""
        for nome in PATAS_VULNERAVEIS:
            if self._no_angulo(EIXO_PATA[nome], COS_PATA[nome]):
                return self.patas[nome]
        return None

    @property
    def no_angulo_do_nucleo(self):
        return self._no_angulo(EIXO_NUCLEO, COS_NUCLEO)

    # ------------------------------------------------------------ contrato de dano
    def ajustar_dano_recebido(self, valor, dano):
        if self.morrendo:
            return None
        if self.nucleo_exposto:
            return valor * (CFG.nucleo_mult if self.no_angulo_do_nucleo else CFG.nucleo_fora_mult)
        if self.pata_exposta is not None and not self.desabado:
            return valor
        return valor * CFG.carapaca_passa

    def absorver_dano(self, valor):
        if self.nucleo_exposto:
            super().absorver_dano(valor)
            self.efeito_no_nucleo()
            return
        pata = None if self.desabado else self.pata_exposta
        if pata is None:
            super().absorver_dano(valor)
            self.efeito_na_carapaca()
            return
        pata.ferir(valor)
        self.efeito_na_pata(pata)
        if pata.quebrada:
            self.desabar(pata)

    # ------------------------------------------------------------ quebra
    def desabar(self, pata):
        """Curto-circuito: corta o que ele estiver fazendo e começa a queda."""
        self.pata_quebrada = pata
        self.interromper_rotina()
        self.cancelar_avisos()
        self.desligar_armas()
        self.desabado = True
        self.pose = 'caido'
        self.wait = 0
        self.iniciar('queda')

    # ------------------------------------------------------------ acampar
    def medir_acampamento(self, delta_time):
        """Conta quanto tempo o jogador está colado em cada pata, sem recuar."""
        jogador = self.jogador.posicao
        for nome in PATAS_VULNERAVEIS:
            pata = self.patas[nome]
            perto = pata.posicao.distance_squared_to(jogador) <= CFG.acampar_raio ** 2
            pata.acampado_ms = pata.acampado_ms + delta_time * 1000 if perto else 0.0

    @property
    def pata_acampada(self):
        """A pata em que o jogador está há mais tempo, se passou do limite."""
        pata = max((self.patas[n] for n in PATAS_VULNERAVEIS), key=lambda p: p.acampado_ms)
        return pata if pata.acampado_ms >= CFG.acampar_ms else None
