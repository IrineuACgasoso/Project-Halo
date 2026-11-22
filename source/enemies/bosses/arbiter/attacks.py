import random
import math
import pygame
from source.feats.projetil import Carabin
from source.systems.entitymanager import entity_manager
from source.enemies.standard.elite import Elite
from .config import CFG

V2 = pygame.math.Vector2


class ArbiterAttacks:
    # ================================================================ utilidades
    def realizar_teleporte(self):
        raio_min, raio_max = 250, 450
        tentativas, padding = 40, 10

        for _ in range(tentativas):
            angulo = random.uniform(0, 2 * math.pi)
            distancia = random.uniform(raio_min, raio_max)

            nova_x = self.jogador.posicao.x + math.cos(angulo) * distancia
            nova_y = self.jogador.posicao.y + math.sin(angulo) * distancia
            pos_candidata = V2(nova_x, nova_y)

            if (self.verificar_posicao_valida(pos_candidata) and
                self.verificar_posicao_valida(pos_candidata + V2(padding, 0)) and
                self.verificar_posicao_valida(pos_candidata + V2(-padding, 0)) and
                self.verificar_posicao_valida(pos_candidata + V2(0, -padding)) and
                self.verificar_posicao_valida(pos_candidata + V2(0, padding))):
                self.posicao = pos_candidata
                return True
        return False

    def _revelar(self, duracao=100, bonus_alpha=120):
        """Revela o Arbiter por um instante mesmo camuflado.

        Substitui `trigger_flash` da base, que retorna cedo quando `self.flash` e False
        (e o Arbiter sempre camufla com flashing=False), ou seja, nunca fazia nada."""
        self.flash_timer = duracao
        self.flash_alpha_bonus = bonus_alpha

    def checar_colisao_stealth(self):
        if self.invis_phase in ('fade_out', 'hold') and self.hitbox.colliderect(self.jogador.hitbox):
            self._revelar(400, 120)

    # ================================================================== carabina
    def atirar_carabina(self, spread=0.03, dano=None, direcao=None):
        """`direcao` None = mira no jogador com spread por eixo (comportamento original).
        `direcao` dado = usa esse vetor, com jitter angular equivalente ao `spread`."""
        dano = CFG.carabina_dano if dano is None else dano
        if direcao is None:
            direcao = self.calcular_direcao_tiro(spread)
        else:
            direcao = direcao.rotate(random.uniform(-1, 1) * math.degrees(spread))

        self._revelar(CFG.revelar_tiro_ms, CFG.revelar_tiro_alpha)
        Carabin(
            posicao_inicial=self.posicao.copy(),
            grupos=(entity_manager.all_sprites,),
            jogador=self.jogador,
            game=self.game,
            dono=CFG.dono_projetil, fonte=self,
            tamanho=(20, 20),
            dano=dano,
            velocidade=CFG.carabina_vel_proj,
            direcao_spread=direcao,
        )

    def rotina_carabina(self):
        """Mira (telegraph) -> rajada com antecipacao -> recuperacao. Fases 2+ alternam rajada em leque."""
        f = self.fase_cfg
        n = f.carabina_tiros

        yield from self._esperar(CFG.carabina_mira, strafe=0.35)

        leque = self.fase >= 2 and random.random() < 0.5
        base = self.direcao_antecipada(CFG.carabina_vel_proj, CFG.carabina_antecipacao)

        for i in range(n):
            if leque:
                frac = i / (n - 1) if n > 1 else 0.5
                direcao = base.rotate(-CFG.carabina_leque_arco / 2 + CFG.carabina_leque_arco * frac)
            else:
                direcao = base
            self.atirar_carabina(CFG.carabina_spread, direcao=direcao)

            if not leque:   # rajada em linha "puxa" de leve pro jogador (pressao sem ser sniper)
                alvo = self.direcao_antecipada(CFG.carabina_vel_proj, CFG.carabina_antecipacao)
                mix = base * (1 - f.carabina_rastreio) + alvo * f.carabina_rastreio
                base = mix.normalize() if mix.length_squared() > 1e-6 else alvo

            yield from self._esperar(CFG.carabina_intervalo, strafe=0.45)

        yield from self._esperar(CFG.carabina_recuperacao, strafe=0.3)
        self.agendar('carabina')
        self.wait = 600

    # ================================================================ invocacao
    def _podar_elites(self):
        self.elites_invocados = [e for e in self.elites_invocados if e.alive()]

    def _posicoes_spawn(self, quantidade):
        posicoes = []
        for _ in range(quantidade):
            for _t in range(CFG.spawn_tentativas):
                ang = random.uniform(0, 2 * math.pi)
                r = random.uniform(*CFG.spawn_raio)
                p = self.posicao + V2(math.cos(ang), math.sin(ang)) * r
                if self.verificar_posicao_valida(p) and all(p.distance_to(o) > 45 for o in posicoes):
                    posicoes.append(p)
                    break
        return posicoes

    def _invocar_elites(self, quantidade):
        """Retorna quantos Elites realmente nasceram (respeita o teto da fase)."""
        self._podar_elites()
        vagas = self.fase_cfg.max_elites - len(self.elites_invocados)
        nasceram = 0
        for pos in self._posicoes_spawn(min(quantidade, max(0, vagas))):
            elite = Elite(pos, game=self.game)
            entity_manager.all_sprites.add(elite)
            entity_manager.inimigos_grupo.add(elite)
            self.elites_invocados.append(elite)
            nasceram += 1
        return nasceram

    def rotina_invocacao(self):
        yield from self._esperar(CFG.invocacao_canal)
        nasceram = self._invocar_elites(self.fase_cfg.elites_por_invocacao)
        if nasceram:
            self.agendar('invocacao')
        else:   # nao achou chao valido: tenta de novo logo, sem queimar o cooldown inteiro
            self.cd['invocacao'] = self._agora + 3000
        self.wait = 1500

    # ================================================================= furtivo
    def rotina_furtivo(self):
        """Camuflagem ativa -> teleporte -> sprint invisivel -> EMBOSCADA com a espada de energia.
        O cone azul e visivel mesmo com ele invisivel: o jogador e avisado e pode reagir."""
        self.adicionar_escudo(CFG.furtivo_escudo)
        self.iniciar_invisibilidade(
            alpha_alvo=0, fade_out=CFG.furtivo_fade_out, fade_in=CFG.furtivo_fade_in,
            duracao=CFG.furtivo_duracao, flashing=False)

        teleportou = False
        emboscou = False
        while self.invis_phase is not None:
            fase = self.invis_phase
            self.velocidade = self.velocidade_base * self.fase_cfg.mult_velocidade * CFG.furtivo_mult_vel
            self.velocidade_animacao = 80 if fase == 'fade_in' else 100

            if fase in ('fade_out', 'hold'):
                self.checar_colisao_stealth()

            if fase == 'hold' and not teleportou:
                self.realizar_teleporte()
                teleportou = True

            if teleportou and not emboscou and fase in ('hold', 'fade_in') \
                    and self.dist_jogador() <= CFG.emboscada_dist:
                emboscou = True
                yield from self.rotina_lamina(emboscada=True)
                continue
            yield

        self.agendar('furtivo')
        self.wait = 900

    # ================================================================ anti-stuck
    def rotina_antistuck(self):
        """Contra-ataque contra quem camperia/prendeu o boss: some, reaparece em outro lugar e despeja o spray."""
        self.iniciar_invisibilidade(alpha_alvo=0, fade_out=800, fade_in=600, duracao=2500, flashing=False)

        while self.invis_phase == 'fade_out':
            self._parar()
            yield
        if self.invis_phase is not None:
            self.realizar_teleporte()

        yield from self._esperar(500)
        for _ in range(CFG.antistuck_tiros):
            self.atirar_carabina(spread=CFG.antistuck_spread, dano=CFG.antistuck_dano)
            yield from self._esperar(CFG.antistuck_intervalo)

        while self.invis_phase is not None:
            self._parar()
            yield
        self.wait = 1200

    # ================================================================ transicao
    def rotina_transicao(self):
        """Mudanca de fase: onda de choque azul 360 (expulsa quem esta colado), escudo novo e reforcos."""
        self.adicionar_escudo(self.fase_cfg.escudo_transicao)
        cfg = self._lancar_cone('arbiter_nova', self.dir_jogador())
        yield from self._esperar(cfg.duracao + 200)
        self._invocar_elites(self.fase_cfg.elites_por_invocacao)
        self.wait = 800
