import pygame
import math
from source.feats.projetil import ProjetilUniversal
from source.systems.entitymanager import entity_manager
from source.feats.assets import ASSETS

class GrenadeBase(ProjetilUniversal):
    """Base genérica para projéteis 'granada': voam em arco parabólico até
    uma posição alvo travada no disparo. Se colidirem com algo antes de
    chegar lá (jogador ou um inimigo, dependendo de quem lançou), grudam
    nesse alvo e a artilharia de aviso passa a segui-lo em tempo real.
    Caso contrário, explodem paradas no ponto onde o arco terminou."""


    def __init__(
            self, posicao_inicial, posicao_alvo, grupos, game, dono, preset,
            sprite_key, tamanho, colisao_alvo, max_height=250, velocidade=600,
            duracao=8000, raio_contato=40, rotacionar=True, custom_config=None):
        
        self.preset = preset
        self.custom_config = custom_config
        self.colisao_alvo = colisao_alvo

        self.start_pos = pygame.math.Vector2(posicao_inicial)
        self.target_pos = pygame.math.Vector2(posicao_alvo)
        self.total_dist = self.start_pos.distance_to(self.target_pos)
        self.max_height = max_height
        self.raio_contato_sq = raio_contato ** 2

        dir_vec = self.target_pos - self.start_pos
        direcao = dir_vec.normalize() if dir_vec.length_squared() > 0 else pygame.math.Vector2(1, 0)

        super().__init__(
            posicao_inicial=posicao_inicial,
            grupos=grupos,
            game=game,
            dono=dono,
            sprite_key=sprite_key,
            tamanho=tamanho,
            dano=0,  # o dano de fato vem da ArtilhariaAviso, não do impacto do projétil
            velocidade=velocidade,
            duracao=duracao,
            direcao_custom=direcao,
            piercing=float('inf'),  # atravessa quem não for o alvo de grude
            rotacionar=rotacionar
        )

        self.grudado = False
        self.aviso = None

    def update(self, delta_time):
        if self.grudado:
            self._atualizar_grudado()
        else:
            self._atualizar_voo(delta_time)

    # Fase 1: voo em arco até a posição travada no disparo
    def _atualizar_voo(self, delta_time):
        self.posicao += self.direcao * self.velocidade * delta_time
        distancia_percorrida = self.start_pos.distance_to(self.posicao)

        alvo_atingido = self._checar_colisao()
        if alvo_atingido is not None:
            self._grudar(alvo_atingido)
            return

        if distancia_percorrida >= self.total_dist:
            self._explodir_sem_grude()
            return

        progresso = distancia_percorrida / self.total_dist
        altura = math.sin(progresso * math.pi) * self.max_height
        self.rect.center = (round(self.posicao.x), round(self.posicao.y - altura))

    def _checar_colisao(self):
        """Verifica contato contra `colisao_alvo`, seja ele um único sprite
        ou um grupo/lista de sprites."""
        alvo_bruto = self.colisao_alvo
        if alvo_bruto is None:
            return None

        if hasattr(alvo_bruto, 'sprites'):
            candidatos = alvo_bruto.sprites()
        elif isinstance(alvo_bruto, (list, tuple, set)):
            candidatos = alvo_bruto
        else:
            candidatos = [alvo_bruto]

        for alvo in candidatos:
            if hasattr(alvo, 'alive') and not alvo.alive():
                continue
            if hasattr(alvo, 'hitbox'):
                if self.rect.colliderect(alvo.hitbox):
                    return alvo
            elif self.posicao.distance_squared_to(alvo.posicao) <= self.raio_contato_sq:
                return alvo
        return None

    # Grudou de verdade: artilharia segue o alvo
    def _grudar(self, alvo):
        from source.feats.skills.artilharia import ArtilhariaAviso
        self.grudado = True
        self.velocidade = 0
        self.alvo = alvo

        self.posicao = pygame.math.Vector2(alvo.posicao)
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        self.aviso = ArtilhariaAviso(
            posicao=self.posicao,
            grupos=(entity_manager.all_sprites,),
            game=self.game,
            dono=self.dono,
            preset=self.preset,
            custom_config=self.custom_config,
            grude=True,
            alvo=alvo
        )

    def _atualizar_grudado(self):
        self.posicao = pygame.math.Vector2(self.alvo.posicao)
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        if self.aviso is not None and not self.aviso.alive():
            self.kill()

    # Não tocou em ninguém: explode estático no ponto onde o arco terminou
    def _explodir_sem_grude(self):
        from source.feats.skills.artilharia import ArtilhariaAviso

        ArtilhariaAviso(
            posicao=self.target_pos,
            grupos=(entity_manager.all_sprites,),
            game=self.game,
            dono=self.dono,
            preset=self.preset,
            custom_config=self.custom_config,
            grude=False
        )
        self.kill()

class Spike(GrenadeBase):
    """Spike do Jega/Banished: gruda no JOGADOR se tocar nele durante o voo."""

    def __init__(self, posicao_inicial, posicao_alvo, grupos, jogador, game, dono, preset):
        self.jogador = jogador
        super().__init__(
            posicao_inicial=posicao_inicial,
            posicao_alvo=posicao_alvo,
            grupos=grupos,
            game=game,
            dono=dono,
            preset=preset,
            sprite_key='spike',
            tamanho=(96, 48),
            colisao_alvo=jogador,   # sprite único: só gruda no jogador
            max_height=250,
            velocidade=600,
            duracao=8000,
            raio_contato=40,
            rotacionar=True
        )

class PlasmaGrenade(GrenadeBase):
    """Granada de plasma do jogador: gruda no PRIMEIRO INIMIGO que tocar
    durante o voo. Usa a sprite própria da granada, com uma auréola azul-clara
    pulsante ao redor dela (indicando que está ativada/armada)."""

    RAIO_INTERNO = 14
    RAIO_EXTERNO = 20

    def __init__(self, posicao_inicial, posicao_alvo, grupos, game, dono, inimigos_grupo, custom_config=None):
        super().__init__(
            posicao_inicial=posicao_inicial,
            posicao_alvo=posicao_alvo,
            grupos=grupos,
            game=game,
            dono=dono,
            preset='plasma_grenade',
            sprite_key='plasma_grenade',
            tamanho=(36, 36),
            colisao_alvo=inimigos_grupo,
            max_height=180,
            velocidade=700,
            duracao=3000,
            raio_contato=30,
            rotacionar=False,
            custom_config=custom_config
        )
        self.tempo_criacao_pulso = pygame.time.get_ticks()

        # Canvas final precisa ser maior que a sprite pra caber a auréola
        # sem cortar (raio externo de 35 já ultrapassa uma sprite de 36x36)
        lado_canvas = self.RAIO_EXTERNO * 2 + 6  # pequena margem de respiro
        self.tamanho_canvas = (lado_canvas, lado_canvas)

    def obter_imagem_base(self, sprite_key, tamanho):
        """Usa a sprite própria da granada (sem desenhar nada por cima aqui —
        a auréola pulsante é composta à parte, em tempo real, no update())."""
        base_key = f"base_{sprite_key}_{tamanho[0]}x{tamanho[1]}"
        if base_key not in ProjetilUniversal.GLOBAL_CACHE:
            img = ASSETS['projectiles'].get(sprite_key)
            if img:
                ProjetilUniversal.GLOBAL_CACHE[base_key] = pygame.transform.scale(img, tamanho)
            else:
                surf = pygame.Surface(tamanho, pygame.SRCALPHA); surf.fill((255, 0, 255))
                ProjetilUniversal.GLOBAL_CACHE[base_key] = surf
        return ProjetilUniversal.GLOBAL_CACHE[base_key]

    def _obter_glow_base(self):
        """Desenha (uma única vez, cacheado) a auréola azul-clara em forma de
        coroa circular — só o anel entre RAIO_INTERNO e RAIO_EXTERNO, com
        algumas camadas para suavizar a borda em vez de ficar serrilhada."""
        glow_key = f"glow_ring_plasma_{self.RAIO_INTERNO}_{self.RAIO_EXTERNO}"
        if glow_key not in ProjetilUniversal.GLOBAL_CACHE:
            lado = self.RAIO_EXTERNO * 2 + 4
            glow = pygame.Surface((lado, lado), pygame.SRCALPHA)
            centro = (lado // 2, lado // 2)

            espessura_total = self.RAIO_EXTERNO - self.RAIO_INTERNO

            # Camadas concêntricas com alpha decrescente nas bordas do anel,
            # pra simular um leve blur em vez de um traço duro
            pygame.draw.circle(glow, (80, 110, 255, 90), centro, self.RAIO_EXTERNO, espessura_total)
            pygame.draw.circle(glow, (120, 160, 255, 160), centro, self.RAIO_EXTERNO - 1, max(1, espessura_total - 3))
            pygame.draw.circle(glow, (180, 220, 255, 220), centro, self.RAIO_EXTERNO - 3, max(1, espessura_total - 6))

            ProjetilUniversal.GLOBAL_CACHE[glow_key] = glow
        return ProjetilUniversal.GLOBAL_CACHE[glow_key]

    def update(self, delta_time):
        super().update(delta_time)

        # --- Pulso: oscila a opacidade da auréola com uma senoide no tempo ---
        agora = pygame.time.get_ticks()
        t = (agora - self.tempo_criacao_pulso) / 1000  # segundos
        velocidade_pulso = 6  # quanto maior, mais rápido pisca
        alpha_min, alpha_max = 90, 220
        pulso = (math.sin(t * velocidade_pulso) + 1) / 2  # normaliza pra 0..1
        alpha_glow = int(alpha_min + (alpha_max - alpha_min) * pulso)

        glow_base = self._obter_glow_base()
        glow_atual = glow_base.copy()
        glow_atual.set_alpha(alpha_glow)

        # Recompõe num canvas maior que a sprite, pra caber a auréola inteira
        cw, ch = self.tamanho_canvas
        composta = pygame.Surface(self.tamanho_canvas, pygame.SRCALPHA)

        gw, gh = glow_atual.get_size()
        composta.blit(glow_atual, (cw / 2 - gw / 2, ch / 2 - gh / 2), special_flags=pygame.BLEND_RGBA_ADD)

        bw, bh = self.tamanho
        composta.blit(self.image_base, (cw / 2 - bw / 2, ch / 2 - bh / 2))

        self.image = composta
        self.rect = self.image.get_rect(center=self.rect.center)

