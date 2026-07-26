import pygame

ORBITA_DISTANCIA_MIN = 450
ORBITA_DISTANCIA_MAX = 600

class JegaSetup:
    def inicializar_habilidades(self):
        self.estado = 'perseguindo'
        self.tempo_inicio_estado = pygame.time.get_ticks()
        self.wait = 0

        self._inicializar_orbita_bote()
        self._inicializar_carabina()
        self._inicializar_spike()
        self._inicializar_ilusao()

    def _inicializar_orbita_bote(self):
        # Habilidade: Órbita Dinâmica e Bote
        self.ultima_habilidade = pygame.time.get_ticks()
        self.cooldown_habilidade = 5000

        # Faixa de distância em que a órbita pode ser ativada (ver config.py)
        self.orbita_distancia_min = ORBITA_DISTANCIA_MIN
        self.orbita_distancia_max = ORBITA_DISTANCIA_MAX
        self.orbita_distancia_min_sq = ORBITA_DISTANCIA_MIN ** 2
        self.orbita_distancia_max_sq = ORBITA_DISTANCIA_MAX ** 2

        self.angulo_orbita = 0
        # raio_orbita não é mais fixo: é definido dinamicamente no momento em
        # que a órbita é ativada, usando a distância real até o jogador.
        self.raio_orbita = 0
        self.velocidade_orbita = 1.3
        self.sentido_orbita = 1
        self.duracao_orbita = 3000
        self.velocidade_bote = self.velocidade_base * 10
        self.duracao_bote = 1500
        self.direcao_bote = pygame.math.Vector2(0, 0)

    def _inicializar_carabina(self):
        # Habilidade: Burst Carabina
        self.cooldown_carabin = 3000
        self.intervalo_carabina = 75
        self.cronometro_carabina = 0
        self.ultima_carabina = 0
        self.carabina_restante = 0
        self.contagem_carabina = 5

    def _inicializar_spike(self):
        # Habilidade: Spike (artilharia de aviso)
        self.ultimo_spike = pygame.time.get_ticks()
        self.cooldown_spike = self.novo_cooldown(4000, 6000)

    def _inicializar_ilusao(self):
        # Habilidade: Ilusões Sombrias (clones + backstab)
        self.ultima_ilusao = pygame.time.get_ticks()
        self.cooldown_ilusao = self.novo_cooldown(10000, 17000)

        # Tempo que o Jega real fica invisível se reposicionando pras costas
        # do jogador enquanto os clones distraem
        self.duracao_ilusao = 2200
        self.velocidade_ilusao = self.velocidade_base * 3  # rápido, mas silencioso

        # Distância atrás do jogador onde o Jega tenta terminar o reposicionamento
        self.distancia_backstab = 90
        self.ponto_reposicionamento = pygame.math.Vector2(0, 0)