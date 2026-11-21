"""Medição de desempenho headless (etapa A1 do roteiro).

Roda cenários fixos com o loop real (update + draw no driver dummy, dt de 1/60) e mede ms/frame.
Tempo varia por máquina: só compare medições feitas na mesma máquina.

Uso (sempre da raiz do repo):
    .venv\\Scripts\\python.exe tools/perf.py                  # mede e compara com tools/perf_base.json
    .venv\\Scripts\\python.exe tools/perf.py --gravar-base    # mede tudo e regrava a base
    .venv\\Scripts\\python.exe tools/perf.py --cenario boss   # só cenários cujo nome contém 'boss'
    .venv\\Scripts\\python.exe tools/perf.py --escala 0.1     # durações x 0,1 (rodada rápida)
Código de saída: 0 = ok; 1 = algum cenário piorou e a piora se confirmou ao medir de novo;
2 = base ilegível ou --gravar-base na bateria (a medida varia até 2x; grave só na tomada).

Os imports do jogo ficam dentro das funções de propósito: o import de `source.feats.assets`
(que carrega todos os assets) é uma das coisas medidas.
"""
import argparse
import functools
import json
import math
import os
import platform
import random
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.pop('MCE_DEBUG', None)   # hacks de debug mudariam a simulação
os.chdir(ROOT)                      # path() resolve relativo ao cwd
for _p in (ROOT, os.path.join(ROOT, 'tests')):   # tests/ para reusar helpers.py
    if _p not in sys.path:
        sys.path.insert(0, _p)

DT = 1 / 60
CAMINHO_BASE = os.path.join(ROOT, 'tools', 'perf_base.json')
TOLERANCIA = 0.10                        # portão de qualidade (roteiro §3)
# Diferença absoluta mínima para contar como piora. Duas rodadas sem mudança de código variaram
# até 0,8 ms em cenários de 1–4 ms (p95 até +42%); o orçamento do frame é 16,7 ms.
PISO_MS = 1.0
METRICAS_COMPARADAS = ('media_ms', 'p95_ms')
TAMANHO_HORDA = 150
SEGUNDOS_HORDA = 20
SEGUNDOS_FASE0 = 60
SEGUNDOS_BOSS = 20


# ------------------------------------------------------------------ #
# Medidas
# ------------------------------------------------------------------ #
def memoria_pico_mb():
    """Pico de memória residente do processo em MB, ou None se a plataforma não informar."""
    try:
        if sys.platform == 'win32':
            import ctypes
            from ctypes import wintypes

            class _Contadores(ctypes.Structure):   # PROCESS_MEMORY_COUNTERS (psapi.h)
                _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
                    (nome, ctypes.c_size_t) for nome in (
                        'PeakWorkingSetSize', 'WorkingSetSize',
                        'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage',
                        'QuotaPeakNonPagedPoolUsage', 'QuotaNonPagedPoolUsage',
                        'PagefileUsage', 'PeakPagefileUsage')]

            kernel32 = ctypes.WinDLL('kernel32')
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            psapi = ctypes.WinDLL('psapi')
            psapi.GetProcessMemoryInfo.argtypes = [
                wintypes.HANDLE, ctypes.POINTER(_Contadores), wintypes.DWORD]
            contadores = _Contadores()
            contadores.cb = ctypes.sizeof(contadores)
            if not psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(),
                                              ctypes.byref(contadores), contadores.cb):
                return None
            return round(contadores.PeakWorkingSetSize / 2 ** 20, 1)
        import resource
        return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)  # Linux: KB
    except (OSError, AttributeError, ImportError):
        return None


def fonte_de_energia():
    """'tomada', 'bateria' ou None (desconhecido). Na bateria o Windows varia o clock da CPU:
    na A1, rodadas seguidas sem mudança de código diferiram até 2x."""
    if sys.platform != 'win32':
        return None
    import ctypes

    class _Status(ctypes.Structure):   # SYSTEM_POWER_STATUS (winbase.h)
        _fields_ = [('ACLineStatus', ctypes.c_ubyte), ('BatteryFlag', ctypes.c_ubyte),
                    ('BatteryLifePercent', ctypes.c_ubyte), ('SystemStatusFlag', ctypes.c_ubyte),
                    ('BatteryLifeTime', ctypes.c_ulong), ('BatteryFullLifeTime', ctypes.c_ulong)]

    status = _Status()
    try:
        if not ctypes.WinDLL('kernel32').GetSystemPowerStatus(ctypes.byref(status)):
            return None
    except OSError:
        return None
    return {0: 'bateria', 1: 'tomada'}.get(status.ACLineStatus)


def p95(valores):
    """Percentil 95 pelo método do posto mais próximo (com 1 valor, é ele mesmo)."""
    if not valores:
        raise ValueError('p95 de lista vazia')
    ordenados = sorted(valores)
    return ordenados[math.ceil(0.95 * len(ordenados)) - 1]


def _resumo_frames(updates_s, draws_s):
    totais_ms = [(u + d) * 1000 for u, d in zip(updates_s, draws_s)]
    n = len(totais_ms)
    return {
        'frames': n,
        'media_ms': round(sum(totais_ms) / n, 2),
        'p95_ms': round(p95(totais_ms), 2),
        'update_media_ms': round(sum(updates_s) * 1000 / n, 2),
        'draw_media_ms': round(sum(draws_s) * 1000 / n, 2),
    }


def _medir_frames(game, segundos, antes_do_frame=None):
    """Roda update + draw por `segundos` de jogo e cronometra cada frame.
    `antes_do_frame` roda fora do cronômetro (ex.: repor a horda)."""
    updates, draws = [], []
    for _ in range(max(1, round(segundos / DT))):
        if antes_do_frame:
            antes_do_frame()
        t0 = time.perf_counter()
        game.update(DT)
        t1 = time.perf_counter()
        game.draw()
        updates.append(t1 - t0)
        draws.append(time.perf_counter() - t1)
    if game.estado_do_jogo != 'jogando':
        # Fora de 'jogando' o update não faz nada: a medida não valeria.
        raise RuntimeError(f'simulação saiu do estado jogando: {game.estado_do_jogo!r}')
    return _resumo_frames(updates, draws)


# ------------------------------------------------------------------ #
# Cenários: função(game, escala) -> dict de métricas
# ------------------------------------------------------------------ #
def _partida(game, seed, fase=0):
    """Partida nova e determinística, com o jogador blindado (sem game over nem level-up)."""
    from helpers import blindar_jogador, ir_para_fase
    random.seed(seed)
    game.iniciar_novo_jogo()
    if fase:
        ir_para_fase(game, fase)
    blindar_jogador(game.player)


def _cenario_horda(game, escala):
    """Horda constante de TAMANHO_HORDA inimigos da fase 0 (o gargalo medido no log)."""
    from source.systems.entitymanager import entity_manager
    _partida(game, seed=1)
    game.spawner.update = lambda dt: None   # o ritmo do spawner não entra na medida

    def repor_horda():
        while len(entity_manager.inimigos_grupo) < TAMANHO_HORDA:
            game.spawner.spawnar('normal')

    repor_horda()
    return _medir_frames(game, SEGUNDOS_HORDA * escala, repor_horda)


def _cenario_fase0(game, escala):
    """Partida normal da fase 0, com o spawner real."""
    _partida(game, seed=2)
    return _medir_frames(game, SEGUNDOS_FASE0 * escala)


def _cenario_boss(game, escala, nome, fase):
    _partida(game, seed=fase, fase=fase)
    game.spawner.spawnar(nome)
    return _medir_frames(game, SEGUNDOS_BOSS * escala)


def _cenario_troca_de_fase(game, escala):
    """Tempo de cada troca de dados de fase (inclui carregar o mapa), da fase 0 até a última."""
    _partida(game, seed=3)
    tempos_ms = []
    while game.existe_proxima_fase():
        t0 = time.perf_counter()
        game.stage_manager._trocar_dados_fase()
        tempos_ms.append((time.perf_counter() - t0) * 1000)
    if not tempos_ms:
        raise RuntimeError('só existe o mapa da fase 0: não há troca de fase para medir')
    return {
        'trocas': len(tempos_ms),
        'media_ms': round(sum(tempos_ms) / len(tempos_ms), 2),
        'max_ms': round(max(tempos_ms), 2),
    }


def listar_cenarios():
    """(nome, função) na ordem de execução. Boss novo entra sozinho pelo PHASE_BOSSES."""
    from source.systems.spawner.spawner_bosses import PHASE_BOSSES
    cenarios = [(f'horda_{TAMANHO_HORDA}', _cenario_horda), ('fase0_60s', _cenario_fase0)]
    for fase, nomes in sorted(PHASE_BOSSES.items()):
        for nome in nomes:
            cenarios.append((f'boss_{nome}', functools.partial(_cenario_boss, nome=nome, fase=fase)))
    cenarios.append(('troca_de_fase', _cenario_troca_de_fase))
    return cenarios


def medir_cenarios(game, filtro=None, escala=1.0, saida=print, somente=None):
    """Mede os cenários cujo nome contém `filtro` (ou, se dado, só os nomes em `somente`)."""
    resultados = {}
    for nome, cenario in listar_cenarios():
        if (filtro and filtro not in nome) or (somente is not None and nome not in somente):
            continue
        saida(f'  medindo {nome}...')
        resultados[nome] = cenario(game, escala)
    game.estado_do_jogo = 'menu_principal'
    return resultados


# ------------------------------------------------------------------ #
# Base e comparação
# ------------------------------------------------------------------ #
def carregar_base(caminho):
    """Relatório gravado, ou None se não existir. JSON inválido é erro (não é ignorado)."""
    if not os.path.exists(caminho):
        return None
    try:
        with open(caminho, encoding='utf-8') as f:
            base = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise ValueError(f'base de desempenho ilegível em {caminho}: {e}') from e
    if not isinstance(base, dict) or not isinstance(base.get('cenarios'), dict):
        raise ValueError(f'base de desempenho sem o campo "cenarios" em {caminho}')
    return base


def salvar(relatorio, caminho):
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)
        f.write('\n')


def comparar(base, atual, tolerancia=TOLERANCIA, piso_ms=PISO_MS):
    """Lista de (cenário, métrica, base, atual) que pioraram mais que `tolerancia` E mais que
    `piso_ms`. Cenário ausente na base (ex.: boss novo) não é comparado."""
    piores = []
    for nome, novo in atual['cenarios'].items():
        antigo = base['cenarios'].get(nome) or {}
        for metrica in METRICAS_COMPARADAS:
            if metrica not in novo or metrica not in antigo:
                continue
            if novo[metrica] - antigo[metrica] > max(antigo[metrica] * tolerancia, piso_ms):
                piores.append((nome, metrica, antigo[metrica], novo[metrica]))
    return piores


def confirmar_pioras(game, base, relatorio, escala=1.0, saida=print):
    """Mede de novo só os cenários acusados e devolve as pioras que se repetem (ruído
    raramente se repete duas vezes seguidas; regressão real sim)."""
    suspeitos = {nome for nome, *_ in comparar(base, relatorio)}
    if not suspeitos:
        return []
    saida(f'confirmando: {", ".join(sorted(suspeitos))}')
    remedidos = medir_cenarios(game, escala=escala, saida=saida, somente=suspeitos)
    return comparar(base, {'cenarios': remedidos})


def formatar_tabela(relatorio, base=None):
    def delta(nome, metrica, valor):
        antigo = ((base or {}).get('cenarios', {}).get(nome) or {}).get(metrica)
        return f' ({(valor / antigo - 1) * 100:+.0f}%)' if antigo else ''

    linhas = [f"import dos assets: {relatorio['import_assets_s']} s | "
              f"memória (pico): {relatorio['memoria_pico_mb']} MB",
              f"{'cenário':<22}{'média ms':>18}{'p95 ms':>18}{'update':>9}{'draw':>8}"]
    for nome, r in relatorio['cenarios'].items():
        media = f"{r['media_ms']}{delta(nome, 'media_ms', r['media_ms'])}"
        if 'p95_ms' in r:
            cauda = f"{r['p95_ms']}{delta(nome, 'p95_ms', r['p95_ms'])}"
            linhas.append(f"{nome:<22}{media:>18}{cauda:>18}"
                          f"{r['update_media_ms']:>9}{r['draw_media_ms']:>8}")
        else:
            linhas.append(f"{nome:<22}{media:>18}{'máx ' + str(r['max_ms']):>18}")
    return '\n'.join(linhas)


# ------------------------------------------------------------------ #
# CLI
# ------------------------------------------------------------------ #
def main(argv=None):
    parser = argparse.ArgumentParser(description='Mede ms/frame do jogo em cenários fixos.')
    parser.add_argument('--cenario', help='só cenários cujo nome contém este texto')
    parser.add_argument('--escala', type=float, default=1.0, help='multiplica as durações')
    parser.add_argument('--base', default=CAMINHO_BASE, help='arquivo da base de comparação')
    parser.add_argument('--gravar-base', action='store_true', help='grava esta medição como base')
    args = parser.parse_args(argv)
    if args.escala <= 0:
        parser.error('--escala precisa ser positiva')
    if args.gravar_base and (args.cenario or args.escala != 1.0):
        parser.error('--gravar-base exige a rodada completa (sem --cenario e com --escala 1)')

    energia = fonte_de_energia()
    if energia == 'bateria':
        if args.gravar_base:
            print('recusado: na bateria a medida varia até 2x; ligue na tomada para gravar a base.',
                  file=sys.stderr)
            return 2
        print('AVISO: rodando na bateria; a comparação pode acusar ruído.', file=sys.stderr)

    try:
        base = carregar_base(args.base)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2

    t0 = time.perf_counter()
    import source.feats.assets  # noqa: F401  (o import carrega todos os assets)
    import_s = round(time.perf_counter() - t0, 2)

    import pygame
    from source.game import Game
    from source.windows.settings import largura_tela, altura_tela
    game = Game(pygame.display.set_mode((largura_tela, altura_tela)))

    print('medindo (headless)...')
    relatorio = {
        'gerado_em': datetime.now().isoformat(timespec='seconds'),
        'maquina': {'sistema': platform.platform(), 'cpu': platform.processor(),
                    'python': platform.python_version(), 'pygame': pygame.version.ver,
                    'energia': energia},
        'escala': args.escala,
        'import_assets_s': import_s,
        'cenarios': medir_cenarios(game, args.cenario, args.escala),
    }
    relatorio['memoria_pico_mb'] = memoria_pico_mb()

    print(formatar_tabela(relatorio, base))
    if args.gravar_base:
        salvar(relatorio, args.base)
        print(f'base gravada em {args.base}')
        return 0
    if base is None:
        print('sem base para comparar (rode com --gravar-base)')
        return 0
    piores = confirmar_pioras(game, base, relatorio, args.escala)
    for nome, metrica, antigo, novo in piores:
        print(f'PIOROU: {nome}.{metrica} {antigo} -> {novo} ms')
    return 1 if piores else 0


if __name__ == '__main__':
    sys.exit(main())
