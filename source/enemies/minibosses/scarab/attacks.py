"""Rotinas do Scarab (geradores: `yield` = 1 frame; todo `while` tem `yield`): body stomp, pisada sísmica,
queda (núcleo exposto), sobrecarga e o colapso final."""
from source.feats.items import Items
from source.feats.skills.artilharia.config import ARTILHARIA_PRESETS

from .config import CFG, FASE_CRITICA


class ScarabAttacks:
    # ------------------------------------------------------------ body stomp
    def rotina_stomp(self):
        """Toma impulso durante o aviso e senta no mesmo frame em que a artilharia estoura."""
        cfg = ARTILHARIA_PRESETS['scarab_stomp']
        self.avisar(self.centro_chao, preset='scarab_stomp')
        inicio = self._agora
        try:
            while self._agora - inicio < cfg.duracao:
                self.impulso_y = CFG.stomp_sobe_px * (self._agora - inicio) / cfg.duracao
                yield
            self.impulso_y = 0.0
            self.pose = 'sentado'
            self.impacto_do_stomp(cfg.raio_explosao)
            yield from self._esperar(CFG.sentado_ms)
        finally:
            self.impulso_y = 0.0
            if self.pose == 'sentado':
                self.pose = 'em_pe'
        self.agendar('stomp')
        self.wait = CFG.stomp_pausa_ms

    # ------------------------------------------------------------ pisada sísmica
    def rotina_sismica(self):
        """Ergue a pata em que o jogador acampou; a artilharia o persegue e trava no fim."""
        pata = self.pata_acampada
        if pata is None:                 # só chamada à mão, num teste
            return
        cfg = ARTILHARIA_PRESETS['scarab_sismica']
        aviso = self.avisar(pata.posicao, preset='scarab_sismica')
        inicio = self._agora
        fim = inicio + cfg.duracao
        self.pousa_em = float('inf')     # quem a põe no chão é esta rotina
        pata.erguida = True
        pata.acampado_ms = 0.0
        while self._agora < fim:
            pata.extra_y = CFG.sismica_ergue_px * min(1.0, (self._agora - inicio) / (cfg.duracao * 0.5))
            if fim - self._agora > CFG.sismica_trava_ms:
                self._perseguir(aviso, pata)
            yield
        pata.erguida = False
        pata.extra_y = 0.0
        self.impacto_da_sismica(aviso.posicao, cfg.raio_explosao)
        self.agendar('sismica')
        self.wait = CFG.sismica_pausa_ms

    def _perseguir(self, aviso, pata):
        """Um frame da artilharia atrás do jogador, até onde a pata alcança."""
        destino = aviso.posicao.move_towards(self.jogador.posicao, CFG.sismica_velocidade * self._dt)
        do_pe = destino - pata.posicao
        if do_pe.length() > CFG.sismica_alcance:
            do_pe.scale_to_length(CFG.sismica_alcance)
            destino = pata.posicao + do_pe
        aviso.posicao.update(destino)
        aviso.rect.center = aviso.hitbox.center = (round(destino.x), round(destino.y))

    # ------------------------------------------------------------ queda
    def rotina_queda(self):
        """Desaba, expõe o núcleo por alguns segundos, se ergue e regenera a pata."""
        pata = self.pata_quebrada
        self.efeito_da_queda(pata)
        try:
            yield from self._esperar(CFG.queda_ms)
            self.nucleo_exposto = True
            self.nucleo_ate = self._agora + CFG.exposto_ms
            yield from self._esperar(CFG.exposto_ms)
            self.nucleo_exposto = False
            yield from self._esperar(CFG.erguer_ms)
        finally:
            self.nucleo_exposto = False
        pata.regenerar()
        self.pata_quebrada = None
        self.desabado = False
        self.pose = 'em_pe'
        self.proximo_passo_em = self._agora + CFG.apoio_ms[self.fase - 1]
        self.rearmar()
        self.efeito_ao_erguer()

    # ------------------------------------------------------------ fase nova
    def rotina_transicao(self):
        """A sobrecarga crítica tem um instante de rugido; a fase 2 só troca os números."""
        if self.fase == FASE_CRITICA:
            self.efeito_da_sobrecarga()
            yield from self._esperar(700)

    # ------------------------------------------------------------ morte
    def morrer(self, grupos=None):
        """Chamado pelo CollisionManager enquanto a vida está em zero: a 1ª vez começa o colapso, e ele só
        sai do mundo quando detona."""
        if self.morrendo:
            return
        self.morrendo = True
        self.grupos_do_drop = grupos
        self.is_invulneravel = True
        self.interromper_rotina()
        self.desligar_armas()
        self.cancelar_avisos()
        self.impulso_y = 0.0
        self.pose = 'caido'
        self.iniciar('morte')

    def rotina_morte(self):
        """Explosões em cadeia por `colapso_ms`; o aviso no chão mostra até onde correr."""
        preset = ARTILHARIA_PRESETS['scarab_detonacao']
        self.avisar(self.centro_chao, preset='scarab_detonacao')
        fim = self._agora + preset.duracao
        proxima = self._agora
        while self._agora < fim:
            if self._agora >= proxima:
                proxima += CFG.explosao_intervalo_ms
                self.explosao_em_cadeia(1 - (fim - self._agora) / preset.duracao)
            yield
        self.detonar(preset.raio_explosao)

    def detonar(self, raio):
        self.efeito_da_detonacao(raio)
        centro = self.centro_chao
        # Ele anda por cima dos prédios: o drop nunca fica fora da arena
        onde = centro if self.verificar_posicao_valida(centro) else self.jogador.posicao
        Items.spawn_drop(
            onde,
            self.grupos_do_drop,
            big_shard=((5, 6, 8, 10), (70, 28, 1.5, 0.5), 100),
            life_orb=(1, 100, 100),
            upgrade=((1, 2), (99, 1), 100)
        )
        self.kill()

    def kill(self):
        """Saiu do mundo (por qualquer motivo): a câmera volta ao normal."""
        if self.alive():
            self.game.camera.definir_zoom(1, CFG.zoom_saida_ms)
        super().kill()
