import pygame

class ArbiterSetup:
    def inicializar_habilidades(self):
        self.estado_habilidade = 'idle'
        self.ja_teleportou = False  # Controle do teleporte da invisibilidade comum
        self.wait = 0

        self._inicializar_invisibilidade()
        self._inicializar_carabina()
        self._inicializar_antistuck()
        self._inicializar_invocacao()
        
    def _inicializar_invisibilidade(self):
        # 1. Habilidade: Sprint Invisível (Camuflagem Ativa)
        self.ultima_invisibi = pygame.time.get_ticks()
        self.cooldown_invisibilidade = 10000
        self.duracao_invisibilidade = 3500

    def _inicializar_carabina(self):
        # 2. Habilidade: Rajada de Carabina Comum
        self.ultima_carabina = pygame.time.get_ticks()
        self.cooldown_carabin = 4000
        self.intervalo_carabina = 80
        self.cronometro_carabina = 0
        self.carabina_restante = 0
        self.contagem_carabina = 5

    def _inicializar_antistuck(self):
        # 3. Mecanismo Dependente: Anti-Stuck de Contra-Ataque (Spray Oculto)
        self.ultimo_check_posicao = pygame.time.get_ticks()
        self.posicao_anterior = pygame.math.Vector2(self.posicao.x, self.posicao.y)
        self.ja_teleportou_stuck = False
        self.spray_iniciado = False
        self.spray_restante = 0
        self.intervalo_spray = 45  # Cadência absurdamente rápida para os 20 tiros
        self.cronometro_spray = 0
        self.tempo_teleporte_stuck = 0

    def _inicializar_invocacao(self):
        # 4. Habilidade: Invocação de Elites
        self.ultima_invocacao = pygame.time.get_ticks()
        self.cooldown_invocacao = 16000
        self.tempo_inicio_summon = 0
        self.duracao_summon = 1000  # Tempo parado invocando (1 segundo)