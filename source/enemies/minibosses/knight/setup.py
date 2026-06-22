import pygame

class KnightSetup:
    def inicializar_habilidades(self):
        agora = pygame.time.get_ticks()

        # FSM de Habilidades
        self.estado_habilidade = 'idle'
        self.wait = 0  # Impede de emendar um ataque no outro
        
        # Configurações de Teleporte (TP)
        self.cooldown_tp = 5000
        self.ultimo_tp = agora
        self.tp_orb = None  
        self.tp_destino = pygame.math.Vector2(0, 0)

        # Configurações de Stun (Preparado para uso futuro)
        self.cooldown_stun = 13000
        self.ultima_stun = agora
        
        # Configurações de Laser
        self.start_laser = 0
        self.wait_laser = 750  # 0.75s parado "carregando" antes de atirar
        self.cooldown_laser = 7000
        self.ultimo_laser = agora

        # Configurações de Corrida (Run)
        self.running = False
        self.cooldown_run = 10000
        self.duracao_run = 2500
        self.ultima_run = agora
        self.inicio_run = 0
        self.velocidade = self.velocidade_base

        # Controle de Summons (Sistema de Trava por Morte)
        self.watcher_ativo = None         # Guarda a instância do Watcher atual
        self.pode_checar_summon = True    # A trava bool que você idealizou
        self.ultimo_summon = agora            # Começa em 0 para poder invocar direto na primeira vez
        self.cooldown_summon = 15000      # 12 segundos de espera APÓS a morte do Watcher

        # Configurações de Cleave
        self.start_cleave = 0
        self.wait_cleave = 250  # Tempo de telegraph (parado) antes de disparar o aviso
        self.cooldown_cleave = 8000
        self.ultimo_cleave = agora