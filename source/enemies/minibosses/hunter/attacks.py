"""Rotinas de ataque do Hunter (geradores: `yield` = 1 frame; todo `while` tem `yield`).

Canhão e burst deixam a movimentação livre ligada (ele anda enquanto atira); dash e slam a desligam.
"""
import pygame

from source.feats.projetil import PlasmaGun
from source.feats.skills.cone_strike import ConeStrikeAviso
from source.feats.skills.dash import Dash
from source.feats.skills.mortar import CanhaoParabolico
from source.systems.entitymanager import entity_manager

from .config import CFG
from .vfx import poeira_da_explosao, poeira_do_slam


class HunterAttacks:
    def _esperar(self, ms):
        fim = self._agora + ms
        while self._agora < fim:
            yield

    # ------------------------------------------------------------- longe
    def rotina_canhao(self):
        CanhaoParabolico(
            start_pos=self.posicao.copy(),
            target_pos=self.jogador.posicao.copy(),
            game=self.game,
            dono='INIMIGO', fonte=self,
            preset_artilharia=CFG.canhao_preset,
            ao_explodir=poeira_da_explosao,
        )
        self.agendar_cooldown('canhao')
        yield

    def rotina_burst(self):
        for _ in range(CFG.burst_tiros):
            PlasmaGun(
                posicao_inicial=self.posicao,
                grupos=(entity_manager.all_sprites,),
                jogador=self.jogador,
                game=self.game,
                dono='INIMIGO', fonte=self,
                dano=CFG.burst_dano,
                velocidade=CFG.burst_velocidade,
                tamanho=CFG.burst_tamanho,
                direcao_spread=self.calcular_direcao_tiro(CFG.burst_spread),
                vai_rotacionar=False,
            )
            yield from self._esperar(CFG.burst_intervalo_ms)
        self.agendar_cooldown('burst')

    # ------------------------------------------------------------ físicos
    def rotina_dash(self):
        """Corre até o fim do tempo na direção do jogador (travada no início) e depois fica parado,
        inofensivo e sem animar durante o atraso de virar pós-dash: a janela para pegar as costas."""
        self.movimento_livre = False
        self.velocidade_animacao = CFG.dash_animacao_ms
        dash = Dash(self, self.jogador.posicao, preset=CFG.dash_preset)
        if dash.direcao.x:
            self.virar_para(1 if dash.direcao.x > 0 else -1)
        self.virar_em = None
        while not dash.atualizar(self._dt, self._paredes):
            self.poeira_do_dash(self._agora, dash.direcao)
            yield

        self.estado_habilidade = 'stun'
        self.is_inofensivo = True
        self.animacao_congelada = True
        self.agendar_virada(CFG.atraso_virar_pos_dash_ms)
        yield from self._esperar(CFG.atraso_virar_pos_dash_ms)
        self.is_inofensivo = False
        self.animacao_congelada = False
        self.velocidade_animacao = self.velocidade_animacao_base
        self.agendar_cooldown('dash')

    def rotina_slam(self):
        """Cone de 90° no eixo de frente (não no jogador): dá para sair pelo lado durante a carga."""
        self.movimento_livre = False
        cone = ConeStrikeAviso(
            self.posicao.copy(), pygame.math.Vector2(self.lado, 0), (entity_manager.all_sprites,), self.game,
            dono='BOSS', preset=CFG.slam_preset, fonte=self, ao_explodir=poeira_do_slam,
        )
        while not cone.explodiu and cone.alive():
            yield
        self.agendar_cooldown('slam')
