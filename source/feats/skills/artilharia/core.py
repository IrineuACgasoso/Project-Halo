# source/feats/skills/artilharia/core.py
import pygame
from source.utils.superficies import SUPERFICIE_VAZIA, camada_alpha
from source.systems.gameclock import relogio
from source.systems.entitymanager import entity_manager
from source.systems.dano import Dano, AREA, fonte_do_dono, habilidade_da
from source.systems.empurrao import empurrar
from source.systems.status import Queimadura, aplicar
from .config import ARTILHARIA_PRESETS, ArtilhariaConfig

MS_ENTRE_TICKS = 1000        # dano contínuo direto
MS_ENTRE_QUEIMADURAS = 250   # renovação da queimadura de quem está na área


class ArtilhariaAviso(pygame.sprite.Sprite):
    def __init__(self, posicao, grupos, game, dono='BOSS', preset='padrao', custom_config: ArtilhariaConfig = None,
                 grude=False, alvo=None, fonte=None, ao_explodir=None,
                 habilidade=None):
        super().__init__(grupos)
        self.game = game
        self.dono = dono
        self.fonte = fonte_do_dono(dono, fonte)   # quem causou (contrato de dano, E1)
        self.habilidade = habilidade_da(self.fonte) if habilidade is None else habilidade
        self.posicao = pygame.math.Vector2(posicao)

        # Carrega a configuração (A customizada tem prioridade, útil para o PurgeGrid)
        self.preset = preset
        self.cfg = custom_config if custom_config else ARTILHARIA_PRESETS.get(preset, ARTILHARIA_PRESETS['padrao'])

        self.tempo_criacao = relogio.agora()
        self.explodiu = False
        self.ao_explodir = ao_explodir   # chamado 1× com o aviso quando explode (ex.: poeira do boss)

        # --- DoT: controla o ciclo de tick de dano contínuo pós-explosão ---
        self.dot_ativo = False
        self.dot_inicio = 0
        self.dot_ultimo_tick = 0

        # --- Grude: quando True, a artilharia acompanha `alvo` a cada frame
        # (ex: um Spike que fisicamente acertou o jogador) em vez de ficar
        # estática na posição de criação.
        self.grude = grude
        self.alvo = alvo

        # --- Requisito para o pygame.sprite lidar com desenho ---
        self.image = SUPERFICIE_VAZIA   # o draw é próprio
        self.rect = self.image.get_rect(center=self.posicao)

        # FIX: Atributo falso para enganar a física/colisão padrão da engine
        self.hitbox = self.rect.copy()

    def ao_atingir_alvo(self, alvo):
        """ 
        FIX ANTI-CRASH: 
        O collision_manager chama isso se a artilharia estiver no grupo de projéteis.
        Retornamos False porque a artilharia lida com o próprio dano em área no update().
        """
        return False

    def draw(self, surface, offset):
        pos_ajustada = self.posicao - offset
        agora = relogio.agora()

        # Camada reaproveitada (roteiro C3), em coordenadas de tela: mesmos pixels da antiga
        # Surface de 2r x 2r colada em (pos - r) (o blit trunca a posição, como o int()).
        raio = self.cfg.raio_explosao
        x0, y0 = int(pos_ajustada.x - raio), int(pos_ajustada.y - raio)
        temp_surface, area = camada_alpha(surface, (x0, y0, raio * 2, raio * 2))
        if temp_surface is None:
            return
        centro_local = (x0 + raio, y0 + raio)

        if not self.explodiu:
            progresso = min((agora - self.tempo_criacao) / self.cfg.duracao, 1)
            raio_interno = int(self.cfg.raio_explosao * progresso)

            # Borda do círculo
            pygame.draw.circle(temp_surface, self.cfg.cor_borda, centro_local, self.cfg.raio_explosao, 4)
            # Preenchimento crescendo
            if raio_interno > 0:
                pygame.draw.circle(temp_surface, self.cfg.cor_preenchimento, centro_local, raio_interno)
        elif self.dot_ativo:
            # Nuvem residual do DoT: fica com o preenchimento visível (pulsando
            # com a borda) enquanto os ticks de dano continuam acontecendo.
            pygame.draw.circle(temp_surface, self.cfg.cor_borda, centro_local, self.cfg.raio_explosao, 3)
            pygame.draw.circle(temp_surface, self.cfg.cor_preenchimento, centro_local, self.cfg.raio_explosao)
        else:
            # Impacto da explosão (sem DoT, ou já terminou o DoT)
            pygame.draw.circle(temp_surface, self.cfg.cor_explosao, centro_local, self.cfg.raio_explosao)

        surface.blit(temp_surface, area.topleft, area)

    def _alvos_na_area(self):
        alvos = entity_manager.inimigos_grupo.sprites() if self.dono == 'PLAYER' else [entity_manager.player]
        return [a for a in alvos if (a.posicao - self.posicao).length() <= self.cfg.raio_explosao]

    def _queimar_area(self):
        """Acende (ou renova) a queimadura de quem está na área. Duas áreas do mesmo preset ocupam o
        mesmo lugar: não somam."""
        efeito = Queimadura(self.cfg.dano_por_segundo, self.cfg.queimadura_ms)
        for alvo in self._alvos_na_area():
            if not getattr(alvo, 'invulneravel', False):
                aplicar(alvo, efeito, fonte=self.fonte, chave=self.preset)

    def _aplicar_dano_em_area(self, dano, impacto=False):
        """Aplica `dano` a todos os alvos dentro do raio, uma vez. `impacto`: é a explosão (e não um
        tick), então valem o knockback e os efeitos da configuração."""
        for alvo in self._alvos_na_area():
            alvo.receber_dano(Dano(dano, AREA, self.fonte, ignora_iframes=True, habilidade=self.habilidade))
            if impacto and self.cfg.knockback:
                empurrar(alvo, self.posicao, self.cfg.knockback)
            if impacto:
                for efeito in self.cfg.efeitos:
                    aplicar(alvo, efeito, fonte=self.fonte, chave=self.preset)

    def update(self, delta_time, paredes=None):
        # Se estiver grudada em um alvo (ex: Spike que acertou o jogador),
        # acompanha a posição dele a cada frame antes de qualquer outra lógica.
        if self.grude and self.alvo is not None:
            self.posicao = pygame.math.Vector2(self.alvo.posicao)
            self.rect.center = self.posicao
            self.hitbox.center = self.rect.center

        agora = relogio.agora()

        # --- Explosão inicial (telegraph terminou) ---
        if not self.explodiu and agora - self.tempo_criacao >= self.cfg.duracao:
            self.explodiu = True
            self.tempo_criacao = agora
            if self.ao_explodir is not None:
                self.ao_explodir(self)

            if self.cfg.dot:
                # Por padrão não aplica o `dano` de impacto, só liga o ciclo de ticks
                if self.cfg.impacto_com_dot:
                    self._aplicar_dano_em_area(self.cfg.dano, impacto=True)
                self.dot_ativo = True
                self.dot_inicio = agora
                self.dot_ultimo_tick = agora
                if self.cfg.queimadura_ms:   # queima já na explosão
                    self._queimar_area()
            else:
                self._aplicar_dano_em_area(self.cfg.dano, impacto=True)

        # --- Ciclo de DoT (dano direto ou queimadura, durante duracao_dot) ---
        elif self.dot_ativo:
            queima = self.cfg.queimadura_ms > 0
            if agora - self.dot_ultimo_tick >= (MS_ENTRE_QUEIMADURAS if queima else MS_ENTRE_TICKS):
                self.dot_ultimo_tick = agora
                if queima:
                    self._queimar_area()
                else:
                    self._aplicar_dano_em_area(self.cfg.dano_por_segundo)

            if agora - self.dot_inicio >= self.cfg.duracao_dot:
                self.dot_ativo = False
                self.kill()

        # --- Fim de vida normal (sem DoT) ---
        elif self.explodiu and agora - self.tempo_criacao >= 150:
            self.kill()