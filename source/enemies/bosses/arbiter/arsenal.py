import pygame
from dataclasses import replace
from source.systems.entitymanager import entity_manager
from source.feats.skills.cone_strike import ConeStrikeAviso
from source.feats.skills.cone_strike.config import CONE_STRIKE_PRESETS
from source.feats.grenades import PlasmaGrenade     # <- ajuste o caminho se o seu grenades.py estiver em outro modulo
from .config import CFG

V2 = pygame.math.Vector2


class ArbiterArsenal:
    """Espada de energia (ConeStrike azul) e Granada de Plasma."""

    # ------------------------------------------------------------------ cone
    def _raio_lamina(self):
        return CONE_STRIKE_PRESETS[CFG.lamina_preset].raio

    def _lancar_cone(self, preset, direcao, duracao_mult=1.0):
        """Cria o cone na posicao atual e devolve a config efetiva (para sincronizar a rotina)."""
        cfg = CONE_STRIKE_PRESETS[preset]
        custom = replace(cfg, duracao=int(cfg.duracao * duracao_mult)) if duracao_mult != 1.0 else None
        ConeStrikeAviso(
            posicao=self.posicao.copy(),
            direcao=direcao,
            grupos=(entity_manager.all_sprites,),
            game=self.game,
            dono=CFG.dono_skills, fonte=self,
            preset=preset,
            custom_config=custom,
        )
        return custom or cfg

    def _avancar(self, ms, mult):
        """Investida curta em direcao ao jogador (fecha o gap entre golpes do combo)."""
        if self.dist_jogador() < 90:
            return
        fim = self._agora + ms
        while self._agora < fim:
            self._ir(self.dir_jogador(), mult)
            self.animador.tocar('investida')
            yield

    def rotina_lamina(self, emboscada=False):
        """Combo de espada de energia: 1 golpe (fase 1), 2 (fase 2), 3 (fase 3).
        Cada golpe: cone azul telegrafado (mira travada no inicio) -> dano -> avanco -> proximo golpe (mais rapido)."""
        for i in range(self.fase_cfg.lamina_golpes):
            direcao = self.dir_jogador()
            cfg = self._lancar_cone(CFG.lamina_preset, direcao, CFG.lamina_combo_mult ** i)

            if emboscada or self.invisivel:     # golpear o revela: janela de contra-ataque
                self._revelar(cfg.duracao + 250, 150)

            yield from self._esperar(cfg.duracao + CFG.lamina_flash)

            if i < self.fase_cfg.lamina_golpes - 1:
                yield from self._avancar(CFG.lamina_avanco_ms, CFG.lamina_avanco_mult)
                yield from self._esperar(CFG.lamina_pausa)

        yield from self._esperar(CFG.lamina_recuperacao)
        self.agendar('lamina')
        if not emboscada:
            self.wait = 500

    # --------------------------------------------------------------- granada
    def _validar_alvo_granada(self, alvo):
        """Garante distancia minima/maxima de arremesso e que o ponto de queda esteja em chao valido."""
        to = alvo - self.posicao
        dist = to.length()
        direcao = to.normalize() if dist > 1e-6 else self.dir_jogador()
        dist = max(CFG.granada_dist_min, min(CFG.granada_dist_max, dist))
        alvo = self.posicao + direcao * dist

        for t in (1.0, 0.85, 0.7, 0.55, 0.4):
            p = self.posicao + (alvo - self.posicao) * t
            if self.verificar_posicao_valida(p):
                return p
        return V2(self.jogador.posicao)

    def _alvo_granada(self, indice):
        """1a granada: onde o jogador vai estar. Seguintes: fecham o cerco pelos lados."""
        base = self.ponto_antecipado(CFG.granada_vel, CFG.granada_antecipacao)
        if indice > 0:
            d = self.dir_jogador()
            lado = 1 if indice % 2 else -1
            base = base + V2(-d.y, d.x) * lado * CFG.granada_offset_lateral
        return self._validar_alvo_granada(base)

    def _lancar_granada(self, alvo):
        PlasmaGrenade(
            posicao_inicial=self.posicao.copy(),
            posicao_alvo=alvo,
            grupos=(entity_manager.all_sprites,),
            game=self.game,
            dono=CFG.dono_skills, fonte=self,
            inimigos_grupo=self.jogador,       # sprite unico: gruda no JOGADOR (igual ao Spike)
            preset=CFG.granada_preset,
        )

    def rotina_granada(self):
        n = self.fase_cfg.granadas
        yield from self._esperar(CFG.granada_preparo, strafe=0.25)      # telegraph: quase parado
        for i in range(n):
            self._lancar_granada(self._alvo_granada(i))
            if i < n - 1:
                yield from self._esperar(CFG.granada_intervalo, strafe=0.25)
        yield from self._esperar(CFG.granada_recuperacao, strafe=0.4)
        self.agendar('granada')
        self.wait = 600
