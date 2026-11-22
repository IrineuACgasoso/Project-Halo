"""BossBase: o motor comum dos bosses (roteiro F1, extraído do Arbiter).

Cada habilidade é uma ROTINA (gerador; `yield` = 1 frame; todo `while` precisa de `yield`).
A IA só decide quando não há rotina ativa. O boss declara, na classe:
  - `FASES`: `FaseBoss` em ordem (a 1ª com limiar 1.0; validado por `validar_tudo`);
  - `COOLDOWNS` (nome -> (min, max) ms) e `COOLDOWN_INICIAL` (nome -> ms depois do spawn);
  - `ESTADOS` (nome da habilidade -> `estado_habilidade`) e um `rotina_<nome>` para cada um;
  - `ANTISTUCK` (`ConfigTravamento`, ou None = sem detector; com ele, `rotina_antistuck`);
e implementa `escolher_habilidade(agora)`. Ganchos opcionais: `perceber`, `preparar_frame`,
`movimento_ocioso`, `orientar` e `rotina_transicao`.

Mixins do boss vão ANTES de `BossBase` na herança (MRO; há teste).
"""
import pygame

from source.enemies.base.enemy_base import BaseEnemy
from source.systems.gameclock import relogio
from source.systems.status import IMUNIDADES_CHEFE

from .contexto import ContextoCombate
from .fases import FASE_UNICA, fase_pela_vida
from .travamento import DetectorTravamento


class BossBase(BaseEnemy):
    imunidades_status = IMUNIDADES_CHEFE   # sem stun nem lentidão de fora (roteiro §8, item 8)

    FASES = (FASE_UNICA,)
    COOLDOWNS = {}
    COOLDOWN_INICIAL = {}
    ESTADOS = {'antistuck': 'antistuck_combat', 'transicao': 'phase_shift'}
    ANTISTUCK = None

    def __init__(self, posicao, vida_base, dano_base, velocidade_base, game, sprite_key,
                 flip_sprite=False, variante=None):
        super().__init__(posicao, vida_base, dano_base, velocidade_base, game, sprite_key,
                         flip_sprite=flip_sprite, variante=variante)
        self.is_boss = True
        self.hitbox = self.rect.copy()     # o corpo do boss; ele pode trocar por um retângulo menor
        self.iniciar_motor()

    def iniciar_motor(self):
        agora = relogio.agora()
        self._agora = agora
        self._dt = 0.0

        self.fase = 1
        self.fase_cfg = self.FASES[0]
        self.transicao_pendente = False

        self.rotina = None
        self.estado_habilidade = 'idle'
        self.ultima_habilidade = None
        self.wait = 0                      # exaustão pós-habilidade (ms): a IA não decide enquanto > 0

        self.cd = {nome: agora + ms for nome, ms in self.COOLDOWN_INICIAL.items()}
        self.contexto = ContextoCombate(self.jogador.posicao)
        self.travamento = (DetectorTravamento(self.ANTISTUCK, agora, self.posicao)
                           if self.ANTISTUCK is not None else None)

    # ------------------------------------------------------------ frame
    def update(self, delta_time, paredes=None):
        agora = relogio.agora()
        self._agora = agora
        self._dt = delta_time

        self.perceber(agora, delta_time)
        self.checar_fase()
        self.executar_estados(agora, delta_time)

        self.orientar()
        super().update(delta_time, paredes)   # movimento + paredes (direção/velocidade das rotinas)
        self.animar()
        self.hitbox.center = self.rect.center   # a hitbox acompanha o sprite

    def perceber(self, agora, delta_time):
        """1× por frame, antes de qualquer decisão. Sobrescreva chamando `super()`."""
        self.contexto.atualizar(self, delta_time)
        if self.travamento is not None:
            self.travamento.registrar(self.posicao, livre=self.rotina is None)

    def orientar(self):
        """Padrão: olha para o jogador."""
        self.set_sprite_direction(self.jogador.posicao.x - self.posicao.x)

    # ------------------------------------------------------------ fases
    def checar_fase(self):
        nova = fase_pela_vida(self.FASES, self.contexto.razao_vida, self.fase)
        if nova > self.fase:
            self.fase = nova
            self.fase_cfg = self.FASES[nova - 1]
            self.transicao_pendente = True

    def rotina_transicao(self):
        """Padrão: nenhum ato (a fase nova só troca os números). Sobrescreva para ter um."""
        yield from ()

    # ------------------------------------------------------------ rotinas
    def executar_estados(self, agora, delta_time):
        self.preparar_frame(delta_time)
        if self.rotina is None:
            self.pensar(agora, delta_time)
        if self.rotina is not None:
            try:
                next(self.rotina)
            except StopIteration:
                self.finalizar_rotina()

    def preparar_frame(self, delta_time):
        """Gancho: roda todo frame antes de pensar/avançar a rotina (ex.: o movimento padrão)."""

    def movimento_ocioso(self, agora):
        """Gancho: o que fazer enquanto não há rotina (ex.: manter distância, circular)."""

    def pensar(self, agora, delta_time):
        """Sem rotina: anti-stuck > exaustão (`wait`) > transição de fase > `escolher_habilidade`."""
        self.estado_habilidade = 'idle'
        self.movimento_ocioso(agora)

        if self.travamento is not None and self.travamento.travou(agora, self.contexto.dist_sq):
            self.iniciar('antistuck')
            return
        if self.wait > 0:
            self.wait -= delta_time * 1000
            return
        if self.transicao_pendente:
            self.transicao_pendente = False
            self.iniciar('transicao')
            return
        escolha = self.escolher_habilidade(agora)
        if escolha is not None:
            self.iniciar(escolha)

    def escolher_habilidade(self, agora):
        """Nome da próxima habilidade (chave de `ESTADOS`), ou None para esperar."""
        raise NotImplementedError(f'{type(self).__name__} precisa implementar escolher_habilidade')

    def iniciar(self, nome):
        self.rotina = getattr(self, f'rotina_{nome}')()
        self.estado_habilidade = self.ESTADOS[nome]
        self.ultima_habilidade = nome

    def finalizar_rotina(self):
        self.rotina = None
        self.estado_habilidade = 'idle'
        if self.travamento is not None:
            self.travamento.resetar(self._agora)

    def interromper_rotina(self):
        """Corta a rotina ativa (fecha o gerador: os `finally` dela rodam) e volta a idle.
        Sem rotina, não faz nada. Não chame de dentro da própria rotina (use `return` lá)."""
        if self.rotina is None:
            return
        rotina, self.rotina = self.rotina, None
        rotina.close()
        self.finalizar_rotina()

    def _esperar(self, ms):
        """Sub-rotina: passa `ms` de tempo de jogo."""
        fim = self._agora + ms
        while self._agora < fim:
            yield

    # ------------------------------------------------------------ cooldowns
    def pronto(self, nome):
        return self._agora >= self.cd[nome]

    def agendar(self, nome):
        """Reagenda o cooldown (sorteado em `COOLDOWNS` e escalado pela fase) a partir de AGORA."""
        minimo, maximo = self.COOLDOWNS[nome]
        self.cd[nome] = self._agora + int(self.novo_cooldown(minimo, maximo) * self.fase_cfg.mult_cooldown)

    # ------------------------------------------------------------ percepção
    def dir_jogador(self):
        d = self.jogador.posicao - self.posicao
        return d.normalize() if d.length_squared() > 1e-6 else pygame.math.Vector2(1, 0)

    def dist_jogador(self):
        """Distância AGORA (o contexto guarda a do início do frame; um teleporte a muda)."""
        return self.posicao.distance_to(self.jogador.posicao)

    def ponto_antecipado(self, vel_projetil, fator, max_desloc=250):
        """Onde o jogador estará quando o projétil chegar (`fator` = confiança na previsão, 0..1)."""
        t = self.dist_jogador() / max(vel_projetil, 1)
        desloc = self.contexto.vel_jogador * t * fator
        if desloc.length() > max_desloc:
            desloc.scale_to_length(max_desloc)
        return self.jogador.posicao + desloc

    def direcao_antecipada(self, vel_projetil, fator):
        d = self.ponto_antecipado(vel_projetil, fator) - self.posicao
        return d.normalize() if d.length_squared() > 1e-6 else self.dir_jogador()
