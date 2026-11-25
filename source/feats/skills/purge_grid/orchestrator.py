# source/feats/skills/purge_grid/orchestrator.py
import math
import random

import pygame
from source.systems.gameclock import relogio
from source.systems.dano import habilidade_da
from source.systems.entitymanager import entity_manager
from source.feats.skills.artilharia import ArtilhariaAviso, ArtilhariaConfig
from .patterns import (generate_grid_pattern, generate_radial_pattern, generate_directional_pattern,
                       generate_line_pattern)
from .config import PURGE_PRESETS, PurgeConfig
from .disparo import DisparoCaindo

class PurgeGrid(pygame.sprite.Sprite):
    def __init__(self, game, caster, preset='padrao', custom_config: PurgeConfig = None):
        super().__init__(entity_manager.all_sprites)
        
        self.game = game
        self.caster = caster
        self.habilidade = habilidade_da(caster)
        
        # Injeta a configuração escolhida (Preset ou uma Customizada na hora)
        self.cfg = custom_config if custom_config else PURGE_PRESETS.get(preset, PURGE_PRESETS['padrao'])
        
        self.fila_spawn = []
        self.ativo = False

        self.image = pygame.Surface((0, 0), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=caster.posicao)

    def iniciar(self, agora):
        self.ativo = True
        player_pos = pygame.math.Vector2(self.game.player.posicao)
        caster_pos = pygame.math.Vector2(self.caster.posicao)
        
        modo = self.cfg.modo.lower()

        if modo in ('grid', 'eixo_x', 'eixo_y'):
            self.fila_spawn = generate_grid_pattern(
                player_pos, modo, self.cfg.direcao_inicio.lower(), self.cfg.artilharias_por_eixo,
                self.cfg.espacamento, self.cfg.qtd_eixos, self.cfg.raio_artilharia, self.cfg.intervalo, agora
            )
        elif modo == 'eixos_inimigo':
            self.fila_spawn = generate_radial_pattern(
                caster_pos, self.cfg.qtd_eixos, self.cfg.artilharias_por_eixo,
                self.cfg.espacamento, self.cfg.direcao.lower(), self.cfg.intervalo, agora,
                self.cfg.offset_angulo
            )
        elif modo == 'linha_jogador':
            angulo = self.cfg.offset_angulo + (random.uniform(0, 2 * math.pi) if self.cfg.angulo_aleatorio else 0.0)
            self.fila_spawn = generate_line_pattern(
                player_pos, angulo, self.cfg.artilharias_por_eixo, self.cfg.espacamento,
                self.cfg.qtd_eixos, self.cfg.raio_artilharia, self.cfg.intervalo, agora
            )
        elif modo == 'inimigo_player':
            self.fila_spawn = generate_directional_pattern(
                caster_pos, player_pos, self.cfg.artilharias_por_eixo,
                self.cfg.espacamento, self.cfg.intervalo, agora
            )

        self.fila_spawn.sort(key=lambda x: x[0])

    def update(self, delta_time, paredes=None):
        if not self.ativo:
            return

        agora = relogio.agora()
        spawns_neste_frame = 0
        MAX_SPAWNS_PER_FRAME = 35

        while self.fila_spawn and agora >= self.fila_spawn[0][0]:
            if spawns_neste_frame >= MAX_SPAWNS_PER_FRAME:
                break
                
            _, pos = self.fila_spawn.pop(0)
            
            # 1. Empacota a configuração ditada pelo Purge
            config_do_purge = ArtilhariaConfig(
                dano=self.cfg.dano,
                raio_explosao=self.cfg.raio_artilharia,
                duracao=self.cfg.duracao_aviso,
                cor_borda=self.cfg.cor_borda,
                cor_preenchimento=self.cfg.cor_preenchimento,
                cor_explosao=self.cfg.cor_explosao
            )

            # 2. Chama a artilharia injetando o pacote
            ArtilhariaAviso(
                posicao=pos,
                grupos=(entity_manager.all_sprites,), # <-- Coloque o grupo de perigo real do seu jogo
                game=self.game,
                dono='BOSS',
                fonte=self.caster, habilidade=self.habilidade,
                custom_config=config_do_purge # Passa os dados sobreescrevendo os presets padrões da artilharia
            )
            if self.cfg.disparo:
                DisparoCaindo(pos, agora + self.cfg.duracao_aviso, self.cfg.disparo)
            spawns_neste_frame += 1

        if not self.fila_spawn:
            self.kill()