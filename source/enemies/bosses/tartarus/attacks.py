"""Rotinas do Tartarus (geradores: `yield` = 1 frame; todo `while` tem `yield`).

Os golpes pesados do martelo terminam em `_resolver_golpe` (errou: sobrecarga e +1 na barra)."""
from dataclasses import replace

import pygame

from source.feats.auras import EnergyAura
from source.feats.particulas.energia import energia_no_circulo, energia_no_retangulo, sugar_para_o_centro
from source.feats.particulas.explosao import explosao_de_impacto, gancho_explosao
from source.feats.skills.artilharia import ArtilhariaAviso
from source.feats.skills.artilharia.config import ARTILHARIA_PRESETS
from source.feats.skills.dash import DASH_PRESETS
from source.feats.skills.purge_grid import PurgeGrid
from source.feats.skills.purge_grid.config import PURGE_PRESETS
from source.feats.skills.rect_strike import RectStrikeAviso
from source.feats.skills.rect_strike.config import RECT_STRIKE_PRESETS
from source.feats.skills.salto import SALTO_PRESETS, Salto
from source.systems.entitymanager import entity_manager
from source.systems.status import BuffVelocidade, Lentidao, aplicar
from source.utils.vetores import direcao_segura

from .config import CFG
from .vfx import COR_VORTICE, onda_estourou, ponto_do_punho_estourou

V2 = pygame.math.Vector2


class TartarusAttacks:
    # ------------------------------------------------------------------ peças
    def _artilharia(self, preset, posicao, ao_explodir=None, duracao=None):
        cfg = ARTILHARIA_PRESETS[preset]
        custom = replace(cfg, duracao=int(duracao)) if duracao is not None else None
        return ArtilhariaAviso(posicao=V2(posicao), grupos=(entity_manager.all_sprites,), game=self.game,
                               dono=CFG.dono_skills, fonte=self, preset=preset, custom_config=custom,
                               ao_explodir=ao_explodir)

    def _grito(self, ms=None):
        """Sub-rotina: o rugido (parado, o corpo treme, faíscas e tremor)."""
        ms = CFG.grito_ms if ms is None else ms
        self.grito_vfx(ms)
        fim = self._agora + ms
        while self._agora < fim:
            self._parar(clip='grito')
            yield

    def _saltar(self, salto):
        """Sub-rotina: o arco do salto até pousar (no ar não é mirado nem atingido)."""
        self._salto = salto
        try:
            while not salto.atualizar(self._dt):
                self._parar(salto.direcao.x, 'corrida')
                yield
        finally:
            salto.cancelar()
            self._salto = None

    # ------------------------------------------------------------------ 1. Vórtice Gravitacional
    def _puxar(self):
        """Puxa o jogador que está na aura para perto dele, devagar (sem vencer a corrida dele)."""
        para_mim = self.posicao - self.jogador.posicao
        dist = para_mim.length()
        if dist > CFG.vortice_raio or dist <= CFG.vortice_puxao_min:
            return
        passo = min(CFG.vortice_puxao * self._dt, dist - CFG.vortice_puxao_min)
        self.jogador.deslocar(para_mim / dist * passo, self._paredes)

    def rotina_vortice(self):
        """Ergue o martelo e abre um campo roxo: lentidão alta em quem está dentro (a aura) e um puxão
        fraco para o alcance do martelo; o círculo do golpe cresce o tempo todo e estoura no fim."""
        yield from self._esperar(CFG.vortice_preparo_ms, clip='grito')
        EnergyAura(owner=self, raio=CFG.vortice_raio, dano_contato=0, game=self.game, cor_base=COR_VORTICE,
                   impenetravel=False, efeitos=(Lentidao(CFG.vortice_lentidao, CFG.vortice_lentidao_ms),),
                   duracao_ms=CFG.vortice_ms)
        aviso = self._artilharia(CFG.vortice_artilharia, self.posicao,
                                 ao_explodir=gancho_explosao('vortice', shake=(9, 380)))
        self.game.camera.shake(*CFG.vortice_shake)
        fim = self._agora + CFG.vortice_ms
        proximas = self._agora
        while self._agora < fim:
            self._parar(clip='grito')
            self._puxar()
            if self._agora >= proximas:
                proximas = self._agora + CFG.vortice_particulas_ms
                sugar_para_o_centro(self.posicao, CFG.vortice_raio, CFG.vortice_particulas)
            yield
        yield from self._ate_explodir(aviso)
        self._resolver_golpe()
        yield from self._esperar(CFG.vortice_recuperacao_ms)
        self._fim('vortice')

    # ------------------------------------------------------------------ 2. Esmagamento Sísmico
    def rotina_onda(self):
        """Martelada no chão: uma fissura gravitacional em linha (larga e comprida) por onde a energia
        azul vaza durante o aviso e é liberada no golpe (arremessa, deixa lento, poeira, tremor)."""
        yield from self._esperar(CFG.onda_preparo_ms, clip='grito')
        alvo = self.ponto_antecipado(1200, CFG.onda_antecipacao)
        direcao = direcao_segura(self.posicao, alvo, self.dir_jogador())
        cfg = RECT_STRIKE_PRESETS[CFG.onda_preset]
        RectStrikeAviso(V2(self.posicao), direcao, (entity_manager.all_sprites,), self.game,
                        dono=CFG.dono_skills, preset=CFG.onda_preset, fonte=self, ao_explodir=onda_estourou)
        energia_no_retangulo(self.posicao, direcao, cfg.altura, cfg.largura, cfg.duracao, 'gravidade')
        yield from self._esperar(cfg.duracao + 60, olhar_x=direcao.x)
        self._resolver_golpe()
        yield from self._esperar(CFG.onda_recuperacao_ms, olhar_x=direcao.x)
        self._fim('onda')

    # ------------------------------------------------------------------ 3. Salto Meteoro
    def rotina_salto(self, preset=None, agendar=True):
        """Salto descomunal que pousa onde o jogador VAI estar; o círculo do impacto aparece no pouso
        na decolagem. Recuperação lenta: a melhor janela para puni-lo. Também é o anti-stuck."""
        preset = preset or CFG.salto_preset
        yield from self._esperar(CFG.salto_preparo_ms, clip='grito')
        cfg = SALTO_PRESETS[preset]
        if cfg.alvo == 'ponto':
            velocidade = max(1.0, self.dist_jogador() / (cfg.duracao_ms / 1000))
            salto = Salto(self, preset, alvo=self.ponto_antecipado(velocidade, CFG.salto_antecipacao, 400))
        else:
            salto = Salto(self, preset)
        aviso = self._artilharia(CFG.salto_artilharia, salto.destino, duracao=cfg.duracao_ms,
                                 ao_explodir=gancho_explosao('gravidade', shake=CFG.salto_shake))
        yield from self._saltar(salto)
        yield from self._ate_explodir(aviso, salto.direcao.x)
        self._resolver_golpe()
        yield from self._esperar(CFG.salto_recuperacao_ms, olhar_x=salto.direcao.x, clip='ofegante')
        if agendar:
            self._fim('salto')

    def rotina_antistuck(self):
        """Preso longe do jogador: salta por cima do que o prende e pousa em cima dele."""
        yield from self.rotina_salto(preset=CFG.antistuck_salto, agendar=False)
        self.wait = 200

    # ------------------------------------------------------------------ 4. Chieftain Rampage
    def rotina_rampage(self):
        """A barreira caiu: rugido e 3 marteladas avançando passo a passo (cada passo termina numa
        explosão). Esquivou das 3: fica ofegante, parado e tomando mais dano (a maior janela da luta)."""
        yield from self._grito()
        acertou_algum = False
        self.is_inofensivo = True            # o corpo não fere: quem fere são as explosões
        try:
            for _ in range(CFG.rampage_golpes):
                self._acertou = False
                yield from self._esperar(CFG.rampage_preparo_ms)
                direcao = yield from self._dash(CFG.rampage_dash, rastro=True)
                aviso = self._artilharia(CFG.rampage_artilharia, self.posicao,
                                         ao_explodir=gancho_explosao('fogo', shake=CFG.rampage_shake))
                yield from self._ate_explodir(aviso, direcao.x)
                acertou_algum = acertou_algum or self._acertou
                yield from self._esperar(CFG.rampage_pausa_ms, olhar_x=direcao.x)
            self._acertou = False
            if not acertou_algum:
                self._ofegante_ate = self._agora + CFG.ofegante_ms
                yield from self._esperar(CFG.ofegante_ms, clip='ofegante')
        finally:
            self.is_inofensivo = False
            self._ofegante_ate = min(self._ofegante_ate, self._agora)
        self._fim('rampage')

    # ------------------------------------------------------------------ Fúria (transição)
    def rotina_transicao(self):
        """Fúria Jiralhanae: descarta o capacete, ruge e corre muito mais (aura vermelha até o fim)."""
        self.descartar_capacete_vfx()
        yield from self._grito(CFG.transicao_ms)
        aplicar(self, BuffVelocidade(CFG.furia_buff), chave=self)
        self._furia = True
        self.cd_brutes = self._agora + CFG.brutes_primeira_ms
        self.wait = 200

    # ------------------------------------------------------------------ 6. Punho de Rukt (Fúria)
    def _centro_da_arena(self):
        """O chão válido mais perto do meio do mapa."""
        centro = V2(self.game.mapa.rect_background.center)
        for raio in CFG.punho_raio_busca:
            for graus in range(0, 360, 45 if raio else 360):
                ponto = centro + V2(raio, 0).rotate(graus)
                if self.verificar_posicao_valida(ponto):
                    return ponto
        return V2(self.posicao)

    def _energia_do_ponto(self, posicao, cfg):
        energia_no_circulo(posicao, cfg.raio_explosao, cfg.duracao, 'gravidade', CFG.punho_energia_densidade)

    def _onda_do_punho(self, preset):
        """Uma onda do Purge Grid com a energia vazando de cada ponto. Devolve quanto ela dura (ms)."""
        purge = PurgeGrid(self.game, self, preset=preset, ao_criar=self._energia_do_ponto,
                          ao_explodir=ponto_do_punho_estourou)
        purge.iniciar(self._agora)
        cfg = PURGE_PRESETS[preset]
        self.game.camera.shake(*CFG.punho_shake)
        return cfg.intervalo * (cfg.artilharias_por_eixo - 1) + 25 * (cfg.qtd_eixos - 1) + cfg.duracao_aviso

    def rotina_punho(self):
        """Salta ao meio da arena e soca o chão: a cruz e, em seguida, as diagonais."""
        centro = self._centro_da_arena()
        yield from self._esperar(CFG.salto_preparo_ms, clip='grito')
        yield from self._saltar(Salto(self, CFG.punho_salto, alvo=centro))
        explosao_de_impacto(self.posicao, 260, 'gravidade', self.game, CFG.punho_shake, faiscas=1.4)
        self._onda_do_punho(CFG.punho_cruz)
        yield from self._esperar(CFG.punho_intervalo_ms, clip='grito')
        duracao = self._onda_do_punho(CFG.punho_diagonal)
        yield from self._esperar(duracao + 80)
        self._resolver_golpe()
        yield from self._esperar(CFG.punho_recuperacao_ms, clip='ofegante')
        self._fim('punho')

    # ------------------------------------------------------------------ 7. Hammer Run (Fúria)
    def rotina_corrida(self):
        """Encara, firma os pés e dispara reto (sem corrigir a rota) até o fim do dash, com o corpo
        ferindo; termina numa mega explosão."""
        yield from self._esperar(CFG.corrida_preparo_ms, clip='grito')
        direcao = self.dir_jogador()
        cfg = DASH_PRESETS[CFG.corrida_dash]
        alvo = self.posicao + direcao * (cfg.velocidade * cfg.duracao_ms / 1000 * 2)
        direcao = yield from self._dash(CFG.corrida_dash, alvo=alvo, inofensivo=False, rastro=True)
        aviso = self._artilharia(CFG.corrida_artilharia, self.posicao,
                                 ao_explodir=gancho_explosao('furia', shake=CFG.corrida_shake, faiscas=1.6))
        yield from self._ate_explodir(aviso, direcao.x)
        self._resolver_golpe()
        yield from self._esperar(CFG.corrida_recuperacao_ms, olhar_x=direcao.x)
        self._fim('corrida')
