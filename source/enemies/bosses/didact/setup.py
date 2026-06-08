# enemies/didact/setup.py
import pygame

class DidactSetup:
    """Mixin responsável por inicializar todos os atributos das habilidades do Didact."""

    def inicializar_habilidades(self):
        """Chama as configurações específicas de cada poder."""
        self.estado_habilidade = 'parado'
        self.enrage = False
        
        self._setup_pull()
        self._setup_laser()
        self._setup_cryptum()

    def _setup_pull(self):
        self.velocidade_puxao = 500
        self.cooldown_pull = 5000
        self.tempo_ultimo_pull = pygame.time.get_ticks()
        self.duracao_pull = 5000
        self.tempo_inicio_pull = 0
        self.dano_pull = self.jogador.vida_maxima / 100
        self.intervalo_dano_pull = 1000
        self.tempo_ultimo_dano_pull = 0 

    def _setup_laser(self):
        self.cooldown_laser = 10000
        self.enraged_laser = self.novo_cooldown(250, 400)
        self.tempo_ultimo_laser = pygame.time.get_ticks()
        self.duracao_aviso_laser = 1500
        self.duracao_disparo_laser = 500
        self.tempo_inicio_laser = 0
        self.posicao_alvo_laser = pygame.math.Vector2()

    def _setup_cryptum(self):
        self.velocidade_cryptum = 270
        self.cryptum_shield = 5000 
        self.entrou_fase_cryptum = False
        
        # Mecânicas dentro do Cryptum
        self.cooldown_emp = 3000
        self.tempo_ultimo_emp = 0
        self.cooldown_artilharia = 1200
        self.tempo_ultima_artilharia = 0