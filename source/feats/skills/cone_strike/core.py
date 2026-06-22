import pygame
import math
from source.systems.entitymanager import entity_manager
from .config import CONE_STRIKE_PRESETS, ConeStrikeConfig

class ConeStrikeAviso(pygame.sprite.Sprite):
    def __init__(self, posicao, direcao, grupos, game, dono='BOSS', preset='padrao', custom_config: ConeStrikeConfig = None):
        super().__init__(grupos)
        self.game = game
        self.dono = dono
        self.posicao = pygame.math.Vector2(posicao)
        
        # Define a direção apontada (converte para vetor normalizado)
        if isinstance(direcao, pygame.math.Vector2):
            self.direcao = direcao.normalize() if direcao.length() > 0 else pygame.math.Vector2(1, 0)
        else:
            # Se for passado um ângulo em graus, converte para vetor
            rad = math.radians(direcao)
            self.direcao = pygame.math.Vector2(math.cos(rad), math.sin(rad))

        # Carrega a configuração do Preset ou Customizada
        self.cfg = custom_config if custom_config else CONE_STRIKE_PRESETS.get(preset, CONE_STRIKE_PRESETS['padrao'])
        
        self.tempo_criacao = pygame.time.get_ticks()
        self.explodiu = False

        # Requisitos do Sprite do Pygame
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.posicao)
        self.hitbox = self.rect.copy()

    def ao_atingir_alvo(self, alvo):
        """ Evita quebras se registrado no gerenciador de colisões padrão """
        return False

    def _desenhar_cone(self, surface, raio_atual, cor, espessura=0):
        """ Desenha um setor circular suave. Se espessura > 0, desenha apenas a borda. """
        if raio_atual <= 0:
            return

        # Ângulo base central do vetor de direção em radianos
        angulo_base = math.atan2(self.direcao.y, self.direcao.x)
        metade_arco = math.radians(self.cfg.angulo_spray / 2)

        # Ângulos limites do cone
        ang_min = angulo_base - metade_arco
        ang_max = angulo_base + metade_arco

        # Centro local da superfície temporária
        centro_local = (self.cfg.raio, self.cfg.raio)
        pontos_poligono = [centro_local]

        # Calcula múltiplos pontos ao longo do arco para deixá-lo arredondado (1 ponto a cada ~5 graus)
        passos = max(5, int(self.cfg.angulo_spray / 5))
        passo_rad = (ang_max - ang_min) / passos

        for i in range(passos + 1):
            ang = ang_min + i * passo_rad
            px = centro_local[0] + math.cos(ang) * raio_atual
            py = centro_local[1] + math.sin(ang) * raio_atual
            pontos_poligono.append((px, py))

        # Desenha a borda ou o preenchimento dependendo da espessura informada
        if espessura > 0:
            # draw.lines com o 3º argumento True garante que ele fecha a forma de volta pro centro
            pygame.draw.lines(surface, cor, True, pontos_poligono, espessura)
        else:
            pygame.draw.polygon(surface, cor, pontos_poligono)

    def draw(self, surface, offset):
        pos_ajustada = self.posicao - offset
        agora = pygame.time.get_ticks()
        
        # Cria uma superfície local otimizada quadrada para caber o cone inteiro
        tamanho_surf = self.cfg.raio * 2
        temp_surface = pygame.Surface((tamanho_surf, tamanho_surf), pygame.SRCALPHA)
        
        if not self.explodiu:
            progresso = min((agora - self.tempo_criacao) / self.cfg.duracao, 1)
            raio_interno = int(self.cfg.raio * progresso)
            
            # 1. Desenha a borda limite vazada (Traçado fino marcando a área do ataque)
            self._desenhar_cone(temp_surface, self.cfg.raio, self.cfg.cor_borda, espessura=3)
            
            # 2. Desenha o preenchimento sólido crescendo acompanhando o tempo (por baixo da borda)
            if raio_interno > 0:
                self._desenhar_cone(temp_surface, raio_interno, self.cfg.cor_preenchimento, espessura=0)
        else:
            # 3. Desenha o clarão de impacto/explosão do cone completo
            self._desenhar_cone(temp_surface, self.cfg.raio, self.cfg.cor_explosao, espessura=0)

        # Desenha na tela centralizando o ponto de origem do cone na coordenada do disparador
        surface.blit(temp_surface, (pos_ajustada.x - self.cfg.raio, pos_ajustada.y - self.cfg.raio))

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()
        
        if not self.explodiu and agora - self.tempo_criacao >= self.cfg.duracao:
            self.explodiu = True
            self.tempo_criacao = agora 
            
            # --- Lógica Matemática Avançada e Leve de Colisão em Cone ---
            alvos = entity_manager.inimigos_grupo.sprites() if self.dono == 'PLAYER' else [entity_manager.player]

            for alvo in alvos:
                vetor_alvo = alvo.posicao - self.posicao
                distancia_sqr = vetor_alvo.length_squared()  # Otimização para checagem de distância
                raio_sqr = self.cfg.raio * self.cfg.raio
                
                # Checagem 1: Está dentro do raio de alcance?
                if distancia_sqr <= raio_sqr:
                    if distancia_sqr == 0:
                        # Evita divisão por zero se estiver exatamente no mesmo pixel
                        self._aplicar_dano(alvo)
                        continue
                        
                    # Checagem 2: O ângulo entre a mira do cone e o alvo está dentro da abertura?
                    vetor_alvo_norm = vetor_alvo.normalize()
                    produto_escalar = self.direcao.dot(vetor_alvo_norm)
                    
                    # Garante limites numéricos para o acos
                    produto_escalar = max(-1.0, min(1.0, produto_escalar))
                    angulo_alvo_graus = math.degrees(math.acos(produto_escalar))
                    
                    # Se o ângulo até o alvo for menor que a METADE da abertura total, o alvo foi pego!
                    if angulo_alvo_graus <= (self.cfg.angulo_spray / 2):
                        self._aplicar_dano(alvo)
                        
        elif self.explodiu and agora - self.tempo_criacao >= 150:
            self.kill()

    def _aplicar_dano(self, alvo):
        """ Auxiliar interno para despachar o dano respeitando os métodos do objeto """
        if hasattr(alvo, 'tomar_dano_direto'):
            alvo.tomar_dano_direto(self.cfg.dano)
        elif hasattr(alvo, 'receber_dano'):
            alvo.receber_dano(self.cfg.dano)