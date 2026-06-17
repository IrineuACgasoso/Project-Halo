import pygame
import random

class GravemindSetup:
    def inicializar_habilidades(self):
        # === 1. MAPEAMENTO DINÂMICO POR VARIANTE ===
        # Define os dados de equilíbrio sem misturar com o código do core
        CONFIGURACOES = {
            'final': {
                'tamanho_sprite': (900, 600),
                'intensidade_shake': 25,
                'raio_safezone': 1000,
                'cd_acido_base': (2000, 3000),
                'cd_infeccao_base': (2500, 4000),
                'cd_cabecas_base': (13000, 19000),
                'cd_tentaculos_base': (2000, 3500),
                'cd_chuva_base': (2000, 4000),
                'tiros_burst': 15,
                'velocidade_baforada': 525,
                'titulo': "GRAVEMIND, O Monumento de Todos os Pecados",
                'is_boss': True,
                'is_final_form': True
            },
            'proto': {
                'tamanho_sprite': (750, 500),
                'intensidade_shake': 10,
                'raio_safezone': 0,
                'cd_acido_base': (3000, 5000),
                'cd_infeccao_base': (4000, 6500),
                'cd_cabecas_base': (9999999, 10000000),
                'cd_tentaculos_base': (10000, 14000),
                'cd_chuva_base': (8000, 12000),
                'tiros_burst': 8,
                'velocidade_baforada': 400,
                'titulo': "PROTO GRAVEMIND",
                'is_boss': False,
                'is_final_form': False
            }
        }

        # Injeta as configurações da variante atual (proto ou final) antes de inicializar as specs
        cfg = CONFIGURACOES.get(self.variante, CONFIGURACOES['proto'])
        for chave, valor in cfg.items():
            setattr(self, chave, valor)

        # === 2. INICIALIZAÇÃO DAS HABILIDADES ===
        self.estado_habilidade = 'idle'
        self.wait = 0

        self._inicializar_respawn_animation()
        self._inicializar_acid_breath()
        self._inicializar_infection()
        self._inicializar_heads()
        self._inicializar_tentacles()
        self._inicializar_hell_rain()

    
    def _inicializar_respawn_animation(self):
        # === ANIMAÇÃO E RESPAWN ===
        self.estado_respawn = 'reaparecendo'
        self.is_animating_respawn = True
        self.altura_atual = 0
        self.posicao_chao = pygame.math.Vector2(self.posicao)
        self.timer_particula = pygame.time.get_ticks()
        
        # Setup do pequeno loop de animação do Gravemind
        self.frame_atual = 0
        self.velocidade_animacao_loop = 600
        self.ultimo_update_animacao = pygame.time.get_ticks()

    def _inicializar_acid_breath(self):
        # Usa o asterisco * para extrair o mínimo e máximo da tupla para a função
        self.cooldown_acido = self.novo_cooldown(*self.cd_acido_base)
        self.ultima_baforada = pygame.time.get_ticks()
        self.tiros_restantes = 0
        self.ultimo_tiro_burst = 0

    def _inicializar_infection(self):
        self.cooldown_infeccao = self.novo_cooldown(*self.cd_infeccao_base)
        self.ultima_infeccao = pygame.time.get_ticks()
        self.spawns_restantes = 0
        self.ultimo_spawn_tick = 0

        # Inicializadores seguros para a variante Infection Forms (Fase 2)
        self.cooldown_infeccao_forms = 0
        self.ultima_infeccao_forms = 0
        self.forms_restantes = 0

    def _inicializar_heads(self):
        self.cooldown_cabecas = self.novo_cooldown(*self.cd_cabecas_base)
        self.ultima_cabeca = pygame.time.get_ticks()
        self.cabecas_restantes = 0
        self.intervalo_cabeca_tick = 0

    def _inicializar_tentacles(self):
        # === TENTÁCULOS PERSEGUIDORES ===
        self.cooldown_tentaculos = self.novo_cooldown(*self.cd_tentaculos_base)
        self.ultimos_tentaculos = 0  # 0 garante que ele pode usar logo no início se a IA escolher
        

    def _inicializar_hell_rain(self):
        # No setup do Gravemind
        self.cooldown_chuva = self.novo_cooldown(*self.cd_chuva_base)
        self.cooldown_chuva = 0
        self.ultima_chuva = 0

        self.morteiros_restantes = 0
        self.ultimo_morteiro_tick = 0