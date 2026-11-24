import pygame
from source.systems.gameclock import relogio
import math
import random
from source.feats.particulas import emitir, imagem_pixel
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
            duracao=8000, raio_contato=40, rotacionar=True, custom_config=None, fonte=None):
        
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
            rotacionar=rotacionar,
            fonte=fonte
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

        # isinstance, não hasattr('sprites'): o Player também tem `.sprites` (dict de animação),
        # e tratá-lo como Group derrubava o jogo quando um boss lançava granada no jogador.
        if isinstance(alvo_bruto, pygame.sprite.AbstractGroup):
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

    def _criar_aviso(self, posicao, **kwargs):
        """A artilharia que explode por esta granada. A subclasse troca a classe (o visual da área)."""
        from source.feats.skills.artilharia import ArtilhariaAviso
        return self._montar_aviso(ArtilhariaAviso, posicao, **kwargs)

    def _montar_aviso(self, classe, posicao, **kwargs):
        return classe(
            posicao=posicao,
            grupos=(entity_manager.all_sprites,),
            game=self.game,
            dono=self.dono,
            fonte=self.fonte,
            preset=self.preset,
            custom_config=self.custom_config,
            **kwargs
        )

    # Grudou de verdade: artilharia segue o alvo
    def _grudar(self, alvo):
        self.grudado = True
        self.velocidade = 0
        self.alvo = alvo

        self.posicao = pygame.math.Vector2(alvo.posicao)
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        self.aviso = self._criar_aviso(self.posicao, grude=True, alvo=alvo)

    def _atualizar_grudado(self):
        self.posicao = pygame.math.Vector2(self.alvo.posicao)
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        if self.aviso is not None and not self.aviso.alive():
            self.kill()

    # Não tocou em ninguém: explode estático no ponto onde o arco terminou
    def _explodir_sem_grude(self):
        self._criar_aviso(self.target_pos, grude=False)
        self.kill()

class Spike(GrenadeBase):
    """Spike do Jega/Banished: gruda no JOGADOR se tocar nele durante o voo."""

    def __init__(self, posicao_inicial, posicao_alvo, grupos, jogador, game, dono, preset, fonte=None):
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
            rotacionar=True,
            fonte=fonte
        )

class PlasmaGrenade(GrenadeBase):
    """Granada de plasma do jogador: gruda no PRIMEIRO INIMIGO que tocar
    durante o voo. Usa a sprite própria da granada, com uma auréola azul-clara
    pulsante ao redor dela (indicando que está ativada/armada)."""

    RAIO_INTERNO = 14
    RAIO_EXTERNO = 20
    PASSO_ALPHA_PULSO = 10   # quantização do alpha da auréola (cache das compostas)

    def __init__(self, posicao_inicial, posicao_alvo, grupos, game, dono, inimigos_grupo,
                 custom_config=None, preset='plasma_grenade', fonte=None):
        # `inimigos_grupo` aceita grupo/lista OU um sprite unico (ex.: o jogador, quando
        # quem lanca e um inimigo como o Arbiter) — ver GrenadeBase._checar_colisao.
        super().__init__(
            posicao_inicial=posicao_inicial,
            posicao_alvo=posicao_alvo,
            grupos=grupos,
            game=game,
            dono=dono,
            preset=preset,
            sprite_key='plasma_grenade',
            tamanho=(36, 36),
            colisao_alvo=inimigos_grupo,
            max_height=180,
            velocidade=700,
            duracao=3000,
            raio_contato=30,
            rotacionar=False,
            custom_config=custom_config,
            fonte=fonte
        )
        self.tempo_criacao_pulso = relogio.agora()

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
        agora = relogio.agora()
        t = (agora - self.tempo_criacao_pulso) / 1000  # segundos
        velocidade_pulso = 6  # quanto maior, mais rápido pisca
        alpha_min, alpha_max = 90, 220
        pulso = (math.sin(t * velocidade_pulso) + 1) / 2  # normaliza pra 0..1
        alpha_glow = int(alpha_min + (alpha_max - alpha_min) * pulso)

        self.image = self._obter_composta(alpha_glow)
        self.rect = self.image.get_rect(center=self.rect.center)

    def _obter_composta(self, alpha_glow):
        """Sprite + auréola com o alpha do pulso, composta uma vez por nível de alpha e guardada
        no GLOBAL_CACHE (roteiro C3: antes eram 2 Surfaces por granada por frame). O alpha é
        quantizado em passos de PASSO_ALPHA_PULSO (diferença máxima de 9/255, invisível)."""
        nivel = alpha_glow - alpha_glow % self.PASSO_ALPHA_PULSO
        chave = (f"plasma_composta_{self.sprite_key}_{self.tamanho[0]}x{self.tamanho[1]}"
                 f"_{self.RAIO_INTERNO}_{self.RAIO_EXTERNO}_{nivel}")
        composta = ProjetilUniversal.GLOBAL_CACHE.get(chave)
        if composta is None:
            glow_atual = self._obter_glow_base().copy()
            glow_atual.set_alpha(nivel)

            # Recompõe num canvas maior que a sprite, pra caber a auréola inteira
            cw, ch = self.tamanho_canvas
            composta = pygame.Surface(self.tamanho_canvas, pygame.SRCALPHA)

            gw, gh = glow_atual.get_size()
            composta.blit(glow_atual, (cw / 2 - gw / 2, ch / 2 - gh / 2), special_flags=pygame.BLEND_RGBA_ADD)

            bw, bh = self.tamanho
            composta.blit(self.image_base, (cw / 2 - bw / 2, ch / 2 - bh / 2))
            ProjetilUniversal.GLOBAL_CACHE[chave] = composta
        return composta



class FuelRodGrenade(GrenadeBase):
    """Carga do Fuel Rod: gota de plasma verde que acompanha a curva do voo e deixa rastro. Explode com
    impacto + poça que queima (`PocaDePlasma`; a config é montada pela arma).

    Quique: se o alvo morrer antes de ela chegar, em vez de explodir no chão ela quica até `quiques`
    vezes (rumo ao inimigo mais próximo; sem nenhum por perto, segue em frente) até grudar em alguém.
    Alvo vivo que só saiu do lugar não conta: ela explode onde caiu."""

    RAIO_BUSCA_QUIQUE = 350
    SALTO_SEM_ALVO = 180         # px: quique sem ninguém por perto
    REDUCAO_ALTURA_QUIQUE = 0.6

    LADO_COLISAO = 46            # px: o rect que gruda (a imagem é maior, por causa do halo)
    PASSO_ANGULO = 10            # graus (cache das imagens)
    ALPHAS_HALO = (110, 150, 190, 230)
    MS_POR_HALO = 60
    MS_ENTRE_RASTROS = 22
    CAMADAS_GOTA = (((20, 130, 40), 1.0), ((70, 225, 50), 0.84), ((180, 255, 70), 0.66),
                    ((255, 255, 240), 0.42))     # (cor, escala), de fora para dentro
    CORES_RASTRO = ((232, 255, 130), (150, 255, 60), (50, 225, 50), (14, 130, 44))

    def __init__(self, posicao_inicial, posicao_alvo, grupos, game, dono, inimigos_grupo,
                 custom_config=None, preset='fuel_rod', quiques=0, alvo=None, fonte=None):
        super().__init__(
            posicao_inicial=posicao_inicial,
            posicao_alvo=posicao_alvo,
            grupos=grupos,
            game=game,
            dono=dono,
            preset=preset,
            sprite_key='fuel_rod',
            tamanho=(52, 30),
            colisao_alvo=inimigos_grupo,
            max_height=180,
            velocidade=700,
            duracao=3000,
            raio_contato=30,
            rotacionar=False,   # a rotação é pela tangente do arco (_animar), não pela direção no chão
            custom_config=custom_config,
            fonte=fonte
        )
        self.quiques = max(0, int(quiques))
        self.alvo_visado = alvo
        self.quicando = False        # perdeu o alvo: quica até grudar ou acabarem os quiques
        self.angulo = 0
        self._proximo_rastro = 0
        self.rect = pygame.Rect(0, 0, self.LADO_COLISAO, self.LADO_COLISAO)
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        self._animar()

    def obter_imagem_base(self, sprite_key, tamanho):
        """Gota de plasma desenhada uma vez (GLOBAL_CACHE): círculos que engordam da cauda para a
        frente, do verde escuro ao núcleo branco."""
        chave = f'base_{sprite_key}_{tamanho[0]}x{tamanho[1]}'
        if chave not in ProjetilUniversal.GLOBAL_CACHE:
            w, h = tamanho
            surf = pygame.Surface(tamanho, pygame.SRCALPHA)
            frente = w - h / 2
            for cor, escala in self.CAMADAS_GOTA:
                cauda = frente - (w - h * 0.65) * escala
                for i in range(17):
                    t = i / 16
                    raio = h / 2 * escala * (0.25 + 0.75 * t)
                    pygame.draw.circle(surf, cor, (cauda + (frente - cauda) * t, h / 2), max(1, raio))
            ProjetilUniversal.GLOBAL_CACHE[chave] = surf
        return ProjetilUniversal.GLOBAL_CACHE[chave]

    def _criar_aviso(self, posicao, **kwargs):
        from source.feats.skills.artilharia import PocaDePlasma
        return self._montar_aviso(PocaDePlasma, posicao, **kwargs)

    def update(self, delta_time):
        super().update(delta_time)
        if self.aviso is not None and self.aviso.explodiu:
            self.kill()   # virou a poça
        if not self.alive():
            return
        self._animar()
        if not self.grudado:
            self._deixar_rastro()

    def _tangente(self):
        """Direção do voo na tela: a do chão mais a subida ou descida do arco."""
        if self.total_dist <= 0:
            return self.direcao
        progresso = min(1.0, self.start_pos.distance_to(self.posicao) / self.total_dist)
        subida = math.cos(progresso * math.pi) * math.pi * self.max_height / self.total_dist
        return self.direcao - pygame.math.Vector2(0, subida)

    def _animar(self):
        if not self.grudado:   # grudada, fica no ângulo em que bateu
            t = self._tangente()
            graus = math.degrees(math.atan2(-t.y, t.x))
            self.angulo = round(graus / self.PASSO_ANGULO) * self.PASSO_ANGULO % 360
        ida_e_volta = 2 * len(self.ALPHAS_HALO) - 2
        nivel = int((relogio.agora() - self.spawn_time) // self.MS_POR_HALO) % ida_e_volta
        self.image = self._composta(self.angulo, self.ALPHAS_HALO[min(nivel, ida_e_volta - nivel)])

    def _composta(self, angulo, alpha_halo):
        """Halo quente + gota girada, composta uma vez por ângulo e nível do halo (GLOBAL_CACHE)."""
        chave = f'fuel_rod_composta_{angulo}_{alpha_halo}'
        composta = ProjetilUniversal.GLOBAL_CACHE.get(chave)
        if composta is None:
            w, h = self.tamanho
            base = pygame.Surface((w + 32, h + 32), pygame.SRCALPHA)
            area = base.get_rect()
            for folga, peso in ((0, 0.16), (10, 0.3), (20, 0.55)):   # de fora para dentro
                pygame.draw.ellipse(base, (110, 255, 60, round(alpha_halo * peso)), area.inflate(-folga, -folga))
            base.blit(self.image_base, self.image_base.get_rect(center=area.center))
            composta = ProjetilUniversal.GLOBAL_CACHE[chave] = pygame.transform.rotate(base, angulo)
        return composta

    def _deixar_rastro(self):
        agora = relogio.agora()
        if agora < self._proximo_rastro:
            return
        self._proximo_rastro = agora + self.MS_ENTRE_RASTROS
        tras = pygame.math.Vector2(-1, 0).rotate(-self.angulo)
        lado = pygame.math.Vector2(-tras.y, tras.x) * random.uniform(-9, 9)
        emitir(pygame.math.Vector2(self.rect.center) + tras * 22 + lado,
               imagem_pixel(random.choice(self.CORES_RASTRO), random.choice((4, 6, 8))),
               tras * random.uniform(30, 110), random.uniform(180, 380))

    def draw(self, surface, offset):
        surface.blit(self.image, self.image.get_rect(center=pygame.math.Vector2(self.rect.center) - offset))

    @property
    def _perdeu_o_alvo(self):
        alvo = self.alvo_visado
        return alvo is not None and not (alvo.alive() and alvo.vivo)

    def _explodir_sem_grude(self):
        if self.quiques <= 0 or not (self.quicando or self._perdeu_o_alvo):
            super()._explodir_sem_grude()
            return
        self.quicando = True
        self.alvo_visado = self._alvo_do_quique()
        self._quicar(self.target_pos + self.direcao * self.SALTO_SEM_ALVO if self.alvo_visado is None
                     else self.alvo_visado.posicao)

    def _alvo_do_quique(self):
        grupo = self.colisao_alvo
        if not isinstance(grupo, pygame.sprite.AbstractGroup):
            return None
        raio_sq = self.RAIO_BUSCA_QUIQUE ** 2
        melhor, melhor_dist = None, raio_sq
        for inimigo in grupo:
            if not inimigo.alive() or not inimigo.alvejavel or getattr(inimigo, 'invulneravel', False):
                continue
            dist = self.target_pos.distance_squared_to(inimigo.posicao)
            if dist <= melhor_dist:
                melhor, melhor_dist = inimigo, dist
        return melhor

    def _quicar(self, destino):
        """Reinicia o arco a partir do ponto de queda, mais baixo a cada quique."""
        self.quiques -= 1
        self.start_pos = pygame.math.Vector2(self.target_pos)
        self.target_pos = pygame.math.Vector2(destino)
        self.posicao = pygame.math.Vector2(self.start_pos)
        self.total_dist = self.start_pos.distance_to(self.target_pos)
        self.max_height *= self.REDUCAO_ALTURA_QUIQUE
        vetor = self.target_pos - self.start_pos
        if vetor.length_squared() > 0:
            self.direcao = vetor.normalize()
