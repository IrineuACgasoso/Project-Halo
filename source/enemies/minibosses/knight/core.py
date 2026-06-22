import pygame
from source.enemies.base.enemy_base import BaseEnemy
from source.feats.auras import EnergyAura
from source.feats.items import Items

# Imports locais do pacote modular
from .setup import KnightSetup
from .states import KnightAI
from .attacks import KnightAttacks

class Knight(BaseEnemy, KnightSetup, KnightAI, KnightAttacks):
    def __init__(self, posicao, game, **kwargs):
        super().__init__(posicao, vida_base=500, dano_base=60, velocidade_base=50, game=game, sprite_key='knight')
        self.game = game
        self.titulo = 'PROMETHEAN KNIGHT'
        self.is_boss = True

        self.setup_animation(
            estado_inicial='right',
            velocidade_animacao=300
        )        
        
        # Inicializa o mixin de habilidades/status
        self.inicializar_habilidades()

        # Começa sem aura ativa (ela será instanciada dinamicamente quando receber escudo)
        self.aura = None

    def morrer(self, grupos):
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 6, 100)
        Items.spawn_drop(self.posicao, grupos, 'health', 1, 50)
        Items.spawn_drop(self.posicao, grupos, 'cafe', 1, 1)
        self.kill()
    
    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()

        # CORREÇÃO: Gerenciamento dinâmico da Aura baseado no escudo ativo
        if hasattr(self, 'escudo_atual') and self.escudo_atual > 0:
            # Se ganhou escudo e a aura não existe ou foi limpa, recria ela!
            if self.aura is None or not self.aura.alive():
                self.aura = EnergyAura(
                    owner=self, 
                    raio=150, 
                    dano_contato=15, 
                    game=self.game, 
                    cor_base=(255, 50, 0), 
                    impenetravel=False
                )
        elif hasattr(self, 'escudo_atual') and self.escudo_atual <= 0:
            # Se perdeu o escudo, desliga a aura com segurança
            if self.aura and self.aura.alive():
                self.aura.kill()

        # 1. Avaliação de Gatilhos da FSM (AI)
        self.executar_estados(agora)

        # 2. Movimentação Base (Congela se estiver canalizando Laser ou viajando no TP)
        if self.estado_habilidade not in ('tp_traveling', 'laser'):
            super().update(delta_time, paredes)
            direcao_x = self.jogador.posicao.x - self.posicao.x 
            self.set_sprite_direction(direcao_x)
        
        # 3. Processamento Contínuo dos Estados Ativos
        if self.estado_habilidade == 'run':
            self.executar_run()
        elif self.estado_habilidade == 'laser':
            self.executar_laser()
        elif self.estado_habilidade == 'cleave':    
            self.executar_cleave()
        elif self.estado_habilidade == 'tp_traveling':
            self.update_tp()
        elif self.estado_habilidade == 'summoning':
            self.update_summon()

        # 4. Atualiza Renderização
        if self.estado_habilidade != 'laser':
            self.animar()