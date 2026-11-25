"""Métricas das lutas de boss com o bot jogador (roteiro F4), headless.

Para cada boss: tempo para matar, dano sofrido, % de acerto e uso de cada habilidade. A régua é fixa
(arsenal, nível e bot iguais para todos), então serve para comparar o boss com ele mesmo antes e
depois de uma mudança, e os bosses entre si; não é o balanceamento de uma partida real.

Uso (sempre da raiz do repo):
    .venv\\Scripts\\python.exe tools/lutas.py                        # resumo de todos os bosses
    .venv\\Scripts\\python.exe tools/lutas.py --boss arbiter         # + uso de cada habilidade
    .venv\\Scripts\\python.exe tools/lutas.py --boss arbiter --parado   # sem bot: a referência
"""
import argparse
import contextlib
import dataclasses
import io
import os
import random
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.pop('MCE_DEBUG', None)
os.chdir(ROOT)                      # path() resolve relativo ao cwd
for _p in (ROOT, os.path.join(ROOT, 'tests')):   # tests/ para reusar helpers.py e bot.py
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pygame  # noqa: E402

from bot import Bot  # noqa: E402
from helpers import DT, blindar_jogador, ir_para_fase, voltar_ao_menu  # noqa: E402
from source.enemies.base.boss.boss_base import BossBase  # noqa: E402
from source.feats.assets import carregar_assets  # noqa: E402
from source.game import Game  # noqa: E402
from source.systems.entitymanager import entity_manager  # noqa: E402
from source.systems.entrada import Roteiro  # noqa: E402
from source.systems.eventos import DANO_CAUSADO, eventos  # noqa: E402
from source.systems.levelup import ARMAS_REGISTRO  # noqa: E402
from source.systems.spawner.spawner_bosses import PHASE_BOSSES  # noqa: E402
from source.windows.settings import altura_tela, largura_tela  # noqa: E402

# Arsenal de alcance, na ordem em que entra: 2 armas na fase 0 e mais uma por fase, até 6.
ARSENAL = ('assault_rifle', 'sidekick_pistol', 'needler', 'carabin', 'sniper_rifle', 'light_rifle')
NIVEL_INICIAL = 3           # nível das armas na fase 0; +1 por fase, até o máximo de cada uma
VIDA_DE_REFERENCIA = 500    # a do jogador no nível 1: traduz o dano sofrido em "vidas por minuto"
LETAL = 10_000             # a partir daqui o golpe existe para matar (Halo, fundo do void)
LIMITE_S = 240
SEM_ATAQUE = (None, 'idle', 'parado', 'perseguindo')    # estados que não são uso de habilidade
PACOTES_DE_BOSS = ('source.enemies.bosses.', 'source.enemies.minibosses.')
AMOSTRA = 10                # 1 leitura da distância a cada tantos passos


class Luta:
    """Uma luta medida, do spawn do boss até ele cair, um golpe letal ou o limite."""

    def __init__(self, nome):
        self.nome = nome
        self.segundos = 0.0
        self.fim = 'limite'         # 'vitoria', 'letal' ou 'limite'
        self.vida_restante = 1.0    # fração da vida do boss
        self.dano = Counter()       # (quem, como) -> dano sofrido pelo jogador
        self.golpes = Counter()     # (quem, como) -> golpes que entraram
        self.usos = Counter()       # habilidade -> vezes
        self.acertos = Counter()    # habilidade (só BossBase) -> usos que feriram o jogador
        self.ataques = Counter()    # classe do tiro ou da área -> quantos nasceram
        self.tiros = 0              # projéteis que ferem por impacto
        self.tiros_certos = 0
        self.distancia_media = 0.0

    @property
    def dano_total(self):
        return sum(self.dano.values())

    @property
    def vidas_por_minuto(self):
        return self.dano_total / VIDA_DE_REFERENCIA / (self.segundos / 60) if self.segundos else 0.0

    @property
    def precisao(self):
        """Fração dos tiros inimigos que acertou (None = ele não atira)."""
        return self.tiros_certos / self.tiros if self.tiros else None


class _Medidor:
    """Ouve uma luta em andamento. Nos bosses fora da BossBase, "uso" é a entrada num estado."""

    def __init__(self, game, luta):
        self.game, self.luta = game, luta
        self._vistos = set()
        self._estados = {}          # corpo de boss sem motor -> último estado
        self._ja_acertou = set()
        self._distancias = []
        self.letal = False
        self.boss = None
        self._seguir(game.sessao.boss_atual)
        self._receber_original = game.player.receber_dano
        game.player.receber_dano = self._receber
        eventos.assinar(DANO_CAUSADO, self._ao_causar_dano)

    def _seguir(self, boss):
        """O boss da vez (o Gravemind passa por três). Na BossBase, todo uso passa por `iniciar`."""
        self.boss = boss
        if not isinstance(boss, BossBase):
            return
        iniciar = boss.iniciar

        def contar(nome):
            self.luta.usos[nome] += 1
            iniciar(nome)
        boss.iniciar = contar

    def _receber(self, dano):
        """Golpe letal (Halo, fundo do void) encerra a luta em vez de matar o jogador blindado."""
        if dano.valor >= LETAL:
            self.letal = True
            dano = dataclasses.replace(dano, valor=0)
        self._receber_original(dano)

    def _ao_causar_dano(self, alvo, dano, valor):
        if alvo is not self.game.player or valor <= 0:
            return
        luta = self.luta
        quem = 'ambiente' if dano.fonte is None else type(dano.fonte).__name__
        chave = (quem, dano.habilidade or dano.tipo)
        luta.dano[chave] += valor
        luta.golpes[chave] += 1
        if dano.tipo == 'projetil':
            luta.tiros_certos += 1
        uso = (dano.habilidade, luta.usos[dano.habilidade]) if dano.habilidade else None
        if uso and dano.fonte is self.boss and uso not in self._ja_acertou:
            self._ja_acertou.add(uso)
            luta.acertos[dano.habilidade] += 1

    def observar(self, passo):
        for s in entity_manager.all_sprites:
            if s in self._vistos:
                continue
            self._vistos.add(s)     # guarda a referência: um id reaproveitado contaria errado
            if getattr(s, 'dono', 'PLAYER') == 'PLAYER' and not hasattr(s, 'atacante'):    # EMP não tem dono
                continue
            self.luta.ataques[type(s).__name__] += 1
            if entity_manager.projeteis_inimigos_grupo.has(s) and getattr(s, 'dano', 0) > 0:
                self.luta.tiros += 1
        for corpo in entity_manager.inimigos_grupo:     # o Warden luta com vários
            if isinstance(corpo, BossBase) or not type(corpo).__module__.startswith(PACOTES_DE_BOSS):
                continue
            estado = next((getattr(corpo, nome) for nome in ('estado_habilidade', 'estado_boss', 'estado')
                           if hasattr(corpo, nome)), None)
            if estado != self._estados.get(corpo) and estado not in SEM_ATAQUE:
                self.luta.usos[estado] += 1
            self._estados[corpo] = estado
        boss = self.game.sessao.boss_atual
        if boss is not None and boss is not self.boss:
            self._seguir(boss)
        if passo % AMOSTRA == 0:
            self._distancias.append(self.boss.posicao.distance_to(self.game.player.posicao))

    def fechar(self):
        eventos.cancelar(DANO_CAUSADO, self._ao_causar_dano)
        luta, boss = self.luta, self.boss
        if hasattr(boss, 'vida'):       # o aviso do Gravemind não tem
            luta.vida_restante = max(0.0, boss.vida / boss.vida_maxima)
        if self._distancias:
            luta.distancia_media = sum(self._distancias) / len(self._distancias)


def equipar(game, fase):
    player = game.player
    player.armas.clear()
    for id_arma in ARSENAL[:2 + fase]:
        arma = player.armas[id_arma] = ARMAS_REGISTRO[id_arma].criar(player, game)
        arma.equipar()
        while arma.nivel < NIVEL_INICIAL + fase and arma.upgrade():
            pass


def lutar(game, nome, seed=1, limite=LIMITE_S, entrada=None):
    """Roda a luta de `nome` e devolve a `Luta`. `entrada`: a fonte do jogador (padrão: o `Bot`).
    O jogador não morre (nem sobe de nível): o dano que ele sofre é a medida."""
    fase = next(f for f, nomes in PHASE_BOSSES.items() if nome in nomes)
    random.seed(seed)
    voltar_ao_menu(game)
    game.iniciar_novo_jogo()
    ir_para_fase(game, fase)
    blindar_jogador(game.player)
    game.player.ativar_upgrade_forcado = lambda **_: None    # o item abriria uma tela e pararia a luta
    equipar(game, fase)
    game.spawner.spawnar(nome)
    luta = Luta(nome)
    medidor = _Medidor(game, luta)
    entrada_original = game.entrada
    game.entrada = Bot(game) if entrada is None else entrada
    try:
        for passo in range(round(limite / DT)):
            game.update(DT)
            medidor.observar(passo)
            luta.segundos = (passo + 1) * DT
            if medidor.letal:
                luta.fim = 'letal'
                break
            if game.sessao.boss_atual is None:
                luta.fim = 'vitoria'
                break
            if game.estado_do_jogo != 'jogando':
                raise RuntimeError(f'a luta parou no estado {game.estado_do_jogo!r}')
    finally:
        game.entrada = entrada_original
        medidor.fechar()
        voltar_ao_menu(game)
    return luta


# ------------------------------------------------------------------ #
# Relatório
# ------------------------------------------------------------------ #
def _media(valores):
    valores = list(valores)
    return sum(valores) / len(valores)


def linha_resumo(nome, lutas):
    fins = Counter(luta.fim for luta in lutas)
    vitorias = [luta.segundos for luta in lutas if luta.fim == 'vitoria']
    tempo = f'{_media(vitorias):.0f} s' if vitorias else f'resta {_media(x.vida_restante for x in lutas):.0%}'
    tiros = sum(luta.tiros for luta in lutas)
    precisao = f'{sum(luta.tiros_certos for luta in lutas) / tiros:.0%}' if tiros else '-'
    return (f"{nome:<11}{tempo:>11}{fins['vitoria']:>5}/{len(lutas)}{fins['letal']:>7}"
            f"{_media(x.vidas_por_minuto for x in lutas):>11.2f}{precisao:>9}"
            f"{_media(x.distancia_media for x in lutas):>11.0f}")


CABECALHO = (f"{'boss':<11}{'p/ matar':>11}{'vitór.':>7}{'letais':>7}{'vidas/min':>11}{'acerto':>9}"
             f"{'dist média':>11}")


def detalhes(lutas):
    """Uso de cada habilidade, o que nasceu e de onde veio o dano, na média por luta."""
    n = len(lutas)

    def somar(campo):
        total = Counter()
        for luta in lutas:
            total.update(getattr(luta, campo))
        return total

    usos, acertos = somar('usos'), somar('acertos')
    dano, golpes = somar('dano'), somar('golpes')
    linhas = ['  usos por luta (usos que feriram, só BossBase):']
    for nome, total in usos.most_common():
        certos = f'  ({acertos[nome] / total:.0%})' if acertos[nome] else ''
        linhas.append(f'    {nome:<24}{total / n:>7.1f}{certos}')
    linhas.append('  ataques criados por luta:')
    linhas += [f'    {nome:<24}{total / n:>7.1f}' for nome, total in somar('ataques').most_common()]
    linhas.append('  dano sofrido por luta (golpes):')
    linhas += [f"    {' / '.join(chave):<36}{total / n:>8.0f}  ({golpes[chave] / n:.1f})"
               for chave, total in dano.most_common()]
    return '\n'.join(linhas)


def main(argv=None):
    todos = [nome for _, nomes in sorted(PHASE_BOSSES.items()) for nome in nomes]
    parser = argparse.ArgumentParser(description='Mede as lutas de boss com o bot jogador.')
    parser.add_argument('--boss', choices=todos, help='só este, com os detalhes')
    parser.add_argument('--seeds', type=int, default=3, help='lutas por boss')
    parser.add_argument('--limite', type=float, default=LIMITE_S, help='segundos de jogo por luta')
    parser.add_argument('--parado', action='store_true', help='jogador parado, para comparar com o bot')
    args = parser.parse_args(argv)
    if args.seeds < 1 or args.limite <= 0:
        parser.error('--seeds e --limite precisam ser positivos')

    carregar_assets()
    game = Game(pygame.display.set_mode((largura_tela, altura_tela)))
    print(CABECALHO)
    for nome in [args.boss] if args.boss else todos:
        with contextlib.redirect_stdout(io.StringIO()):     # o jogo avisa a derrota de cada boss
            lutas = [lutar(game, nome, seed, args.limite, Roteiro([]) if args.parado else None)
                     for seed in range(1, args.seeds + 1)]
        print(linha_resumo(nome, lutas), flush=True)
        if args.boss:
            print(detalhes(lutas))
    return 0


if __name__ == '__main__':
    sys.exit(main())
