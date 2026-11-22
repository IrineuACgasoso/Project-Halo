"""Validação central dos dados do jogo (roteiro D5).

`validar_tudo()` devolve a lista de erros (vazia = dados válidos). Roda na suíte
(`tests/unit/test_validacao.py`) e na abertura do jogo com `MCE_DEBUG=1` (`main.py`).
Cada validador recebe os dados como parâmetro (padrão: os do jogo), para que os testes possam
quebrá-los de propósito. Os validadores não decodificam imagens nem iniciam o pygame.
"""
import json
import os
from numbers import Real

import pygame

from source.data.enemy_data import INIMIGOS, PerfilInimigo
from source.data.manifesto_assets import MANIFESTO, Imagem
from source.data.weapon_data import COMPANION_DATA, VEHICLES_DATA, WEAPON_DATA, WeaponStats
from source.enemies.base.boss import BossBase, FaseBoss
from source.enemies.base.enemy_base import BaseEnemy
from source.feats.weapons.baseweapon import Arma
from source.systems.levelup.constants import (ARMAS_REGISTRO, NIVEL_MAXIMO_POR_RARIDADE, PALETA_RARIDADE,
                                              PESO_SORTEIO_POR_RARIDADE)
from source.systems.mapmanager.map_loader import MapLoader
from source.systems.spawner.spawner_bosses import BOSS_CLASSES, CRONOGRAMA_BOSSES, PHASE_BOSSES
from source.systems.spawner.spawner_pools import DEFAULT_POOL, PHASE_POOLS
from source.utils.paths import path

# Os tipos de item que `Items._aplicar_efeito` sabe aplicar (feats/items/items.py).
ITENS_DE_DROP = ('exp_shard', 'big_shard', 'life_orb', 'upgrade')


def _numero(valor):
    return isinstance(valor, Real) and not isinstance(valor, bool)


def _inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


# ------------------------------------------------------------------ #
# Armas, companheiros e veículos
# ------------------------------------------------------------------ #
def validar_armas(armas=None, companheiros=None, veiculos=None, registro=None, niveis_maximos=None,
                  pesos=None):
    armas = WEAPON_DATA if armas is None else armas
    companheiros = COMPANION_DATA if companheiros is None else companheiros
    veiculos = VEHICLES_DATA if veiculos is None else veiculos
    registro = ARMAS_REGISTRO if registro is None else registro
    niveis_maximos = NIVEL_MAXIMO_POR_RARIDADE if niveis_maximos is None else niveis_maximos
    pesos = PESO_SORTEIO_POR_RARIDADE if pesos is None else pesos
    erros = []

    # Raridade (roteiro E6): toda raridade com cor também tem nível máximo e peso no sorteio
    for nome_dic, dic in (('NIVEL_MAXIMO_POR_RARIDADE', niveis_maximos), ('PESO_SORTEIO_POR_RARIDADE', pesos)):
        for raridade in sorted(set(PALETA_RARIDADE) ^ set(dic)):
            onde = 'falta em' if raridade in PALETA_RARIDADE else 'sobra em'
            erros.append(f'raridade "{raridade}": {onde} {nome_dic} (as chaves são as de PALETA_RARIDADE)')
    for raridade, nivel in sorted(niveis_maximos.items()):
        if not _inteiro(nivel) or nivel < 1:
            erros.append(f'raridade "{raridade}": nível máximo {nivel!r} (precisa ser inteiro >= 1)')
    for raridade, peso in sorted(pesos.items()):
        if not _numero(peso) or not 0 < peso < float('inf'):   # NaN também falha
            erros.append(f'raridade "{raridade}": peso no sorteio {peso!r} (precisa ser > 0 e finito)')

    categorias = {'armas': armas, 'companheiros': companheiros, 'veículos': veiculos}
    nomes = list(categorias.items())
    for i, (cat_a, dados_a) in enumerate(nomes):
        for cat_b, dados_b in nomes[i + 1:]:
            for nome in sorted(set(dados_a) & set(dados_b)):
                erros.append(f'dados: "{nome}" está em {cat_a} e em {cat_b} (o perfil é buscado só pelo nome)')

    for dados in categorias.values():
        for nome, perfil in dados.items():
            for atributo, meta in perfil.stats.items():
                local = f'dados: {nome}.{atributo}'
                if not isinstance(meta, WeaponStats):
                    erros.append(f'{local} não é WeaponStats')
                elif meta.increase and meta.increase < 0 and meta.label and meta.min_val is None:
                    # não há teto de nível: sem piso, um cooldown chega a 0 ou fica negativo
                    erros.append(f'{local} diminui a cada nível e não tem min_val')

    perfis = {**armas, **companheiros, **veiculos}
    for id_arma, info in registro.items():
        local = f'ARMAS_REGISTRO["{id_arma}"]'
        if info.id != id_arma:
            erros.append(f'{local}: id "{info.id}" diferente da chave')
        if info.raridade not in PALETA_RARIDADE:
            erros.append(f'{local}: raridade "{info.raridade}" fora de PALETA_RARIDADE')
        nome_asset = getattr(info.classe, 'NOME_ASSET', None)
        if nome_asset not in perfis:
            erros.append(f'{local}: {info.classe.__name__}.NOME_ASSET "{nome_asset}" sem perfil em weapon_data')
        elif _inteiro(niveis_maximos.get(info.raridade)) and niveis_maximos[info.raridade] >= 1:
            # máximo inválido já foi acusado acima: sem erros em cascata
            erros += _pisos_que_nao_batem(nome_asset, perfis[nome_asset], niveis_maximos[info.raridade])
    return erros


def _pisos_que_nao_batem(nome_asset, perfil, nivel_maximo):
    """Stat que desce até um `min_val` precisa chegar a ele EXATAMENTE no último upgrade até o nível
    máximo da raridade: valor + subidas × increase == min_val. Se não chega, o piso é de mentira; se
    passa, o limite do `aplicar_upgrades` trava o stat antes e os níveis seguintes não dão nada."""
    erros = []
    for atributo, meta in perfil.stats.items():
        if not isinstance(meta, WeaponStats) or not meta.label or meta.min_val is None:
            continue
        if not _numero(meta.increase) or meta.increase >= 0 or not _numero(meta.value):
            continue
        subidas = sum(1 for nivel in range(2, nivel_maximo + 1) if Arma._deve_melhorar(meta.range_val, nivel))
        final = meta.value + subidas * meta.increase
        if final != meta.min_val:
            situacao = 'nunca chega a ele' if final > meta.min_val else 'passa dele e trava antes do fim'
            erros.append(f'dados: {nome_asset}.{atributo}: min_val {meta.min_val} não bate com o nível máximo '
                         f'{nivel_maximo} ({meta.value:g} {meta.increase:+g} × {subidas} = {final:g}: {situacao})')
    return erros


# ------------------------------------------------------------------ #
# Spawner: pools e bosses
# ------------------------------------------------------------------ #
def validar_spawner(pools=None, pool_padrao=None, bosses_por_fase=None, classes_de_boss=None,
                    cronograma=None):
    pools = PHASE_POOLS if pools is None else pools
    pool_padrao = DEFAULT_POOL if pool_padrao is None else pool_padrao
    bosses_por_fase = PHASE_BOSSES if bosses_por_fase is None else bosses_por_fase
    classes_de_boss = BOSS_CLASSES if classes_de_boss is None else classes_de_boss
    cronograma = CRONOGRAMA_BOSSES if cronograma is None else cronograma
    erros = []

    for fase, pool in [*sorted(pools.items()), ('padrão', pool_padrao)]:
        local = f'pool da fase {fase}'
        classes, pesos = pool.get('classes', []), pool.get('pesos', [])
        if not classes or len(classes) != len(pesos):
            erros.append(f'{local}: {len(classes)} classes e {len(pesos)} pesos (precisam ser iguais e > 0)')
        for peso in pesos:
            if not _numero(peso) or peso <= 0:
                erros.append(f'{local}: peso {peso!r} (precisa ser > 0)')
        for classe in classes:
            if not (isinstance(classe, type) and issubclass(classe, BaseEnemy)):
                erros.append(f'{local}: {classe!r} não é um inimigo (BaseEnemy)')

    # Boss novo precisa estar nos 3 dicts (CLAUDE.md)
    na_fase = {nome for nomes in bosses_por_fase.values() for nome in nomes}
    for nome in sorted(na_fase | set(classes_de_boss) | set(cronograma)):
        faltando = [dic for dic, chaves in (('PHASE_BOSSES', na_fase), ('BOSS_CLASSES', classes_de_boss),
                                            ('CRONOGRAMA_BOSSES', cronograma)) if nome not in chaves]
        if faltando:
            erros.append(f'boss "{nome}": falta em {", ".join(faltando)}')
    for nome, segundos in sorted(cronograma.items()):
        if not _numero(segundos) or segundos <= 0:
            erros.append(f'boss "{nome}": horário {segundos!r} (precisa ser > 0 s)')
    tempos = [(cronograma[nome], fase, nome) for fase, nomes in sorted(bosses_por_fase.items())
              for nome in nomes if _numero(cronograma.get(nome))]
    for (t1, f1, n1), (t2, f2, n2) in zip(tempos, tempos[1:]):
        if t2 < t1:
            erros.append(f'boss "{n2}" (fase {f2}, {t2} s) vem antes de "{n1}" (fase {f1}, {t1} s)')
    return erros


def validar_motor_de_bosses(classes_de_boss=None):
    """Bosses sobre a BossBase (roteiro F1): fases em ordem e faixas de cooldown sorteáveis."""
    classes_de_boss = BOSS_CLASSES if classes_de_boss is None else classes_de_boss
    erros = []
    for nome, classe in sorted(classes_de_boss.items()):
        if not (isinstance(classe, type) and issubclass(classe, BossBase)):
            continue
        local = f'boss "{nome}"'
        fases = classe.FASES
        if not fases or not all(isinstance(f, FaseBoss) for f in fases):
            erros.append(f'{local}: FASES precisa ser uma sequência não vazia de FaseBoss')
            continue
        if fases[0].limiar_vida != 1.0:
            erros.append(f'{local}: a 1ª fase precisa ter limiar_vida 1.0 (tem {fases[0].limiar_vida})')
        for anterior, fase in zip(fases, fases[1:]):
            if fase.limiar_vida >= anterior.limiar_vida:
                erros.append(f'{local}: limiar da fase "{fase.nome}" ({fase.limiar_vida}) não é menor '
                             f'que o de "{anterior.nome}" ({anterior.limiar_vida})')
        for habilidade, faixa in sorted(classe.COOLDOWNS.items()):
            if not (isinstance(faixa, tuple) and len(faixa) == 2 and all(_inteiro(v) for v in faixa)
                    and 0 <= faixa[0] <= faixa[1]):
                erros.append(f'{local}: cooldown de "{habilidade}" {faixa!r} (precisa ser (min, max) '
                             'inteiros com 0 <= min <= max)')
        for habilidade, ms in sorted(classe.COOLDOWN_INICIAL.items()):
            if habilidade not in classe.COOLDOWNS:
                erros.append(f'{local}: cooldown inicial de "{habilidade}" sem faixa em COOLDOWNS')
            if not _inteiro(ms) or ms < 0:
                erros.append(f'{local}: cooldown inicial de "{habilidade}" {ms!r} (precisa ser inteiro >= 0)')
    return erros


# ------------------------------------------------------------------ #
# Inimigos comuns
# ------------------------------------------------------------------ #
def _erros_de_drop(config):
    """Mesmo formato que `Items.spawn_drop` entende; o que ele não entende é ignorado em silêncio."""
    if not isinstance(config, (tuple, list)) or len(config) != 3:
        return ['precisa ser (quantidade, chance, escala)']
    quantidade, chance, escala = config
    if not _numero(escala) or escala <= 0:
        return [f'escala {escala!r} (precisa ser > 0)']
    if isinstance(quantidade, (tuple, list)):   # quantidade variável: ((1, 2), (90, 10), 100)
        erros = []
        if not quantidade or not isinstance(chance, (tuple, list)) or len(chance) != len(quantidade):
            erros.append('quantidades e chances precisam ter o mesmo tamanho (> 0)')
        if not all(_inteiro(q) and q >= 1 for q in quantidade):
            erros.append(f'quantidades {quantidade!r} (inteiros >= 1)')
        if isinstance(chance, (tuple, list)) and not all(_numero(c) and c >= 0 for c in chance):
            erros.append(f'chances {chance!r} (precisam ser >= 0)')
        return erros
    erros = []
    if not _inteiro(quantidade) or quantidade < 1:
        erros.append(f'quantidade {quantidade!r} (inteiro >= 1)')
    if not _numero(chance) or not 0 < chance <= escala:
        erros.append(f'chance {chance!r} (precisa estar entre 0 e a escala {escala})')
    return erros


def validar_inimigos(inimigos=None):
    inimigos = INIMIGOS if inimigos is None else inimigos
    erros = []
    for nome, perfil in inimigos.items():
        local = f'INIMIGOS["{nome}"]'
        if not isinstance(perfil, PerfilInimigo):
            erros.append(f'{local} não é PerfilInimigo')
            continue
        if not _numero(perfil.vida) or perfil.vida <= 0:
            erros.append(f'{local}: vida {perfil.vida!r} (precisa ser > 0)')
        if not _numero(perfil.dano) or perfil.dano < 0:
            erros.append(f'{local}: dano {perfil.dano!r} (precisa ser >= 0)')
        if not _numero(perfil.velocidade) or perfil.velocidade <= 0:
            erros.append(f'{local}: velocidade {perfil.velocidade!r} (precisa ser > 0)')
        for cooldown, faixa in perfil.cooldowns.items():
            # novo_cooldown usa random.randint: inteiros, mín <= máx
            if (not isinstance(faixa, tuple) or len(faixa) != 2 or not all(_inteiro(v) for v in faixa)
                    or not 0 < faixa[0] <= faixa[1]):
                erros.append(f'{local}: cooldown "{cooldown}" {faixa!r} (precisa ser (mín, máx) em ms, 0 < mín <= máx)')
        for item, config in perfil.drops.items():
            if item not in ITENS_DE_DROP:
                erros.append(f'{local}: drop de item desconhecido "{item}" (conhecidos: {", ".join(ITENS_DE_DROP)})')
            for erro in _erros_de_drop(config):
                erros.append(f'{local}: drop "{item}": {erro}')
    return erros


# ------------------------------------------------------------------ #
# Manifesto de imagens
# ------------------------------------------------------------------ #
def _folhas(no, onde='MANIFESTO'):
    """(onde, folha) de cada folha da árvore. Ao contrário de `manifesto_assets.folhas`, não
    quebra numa folha que não é Imagem (é justamente ela que a validação precisa apontar)."""
    if isinstance(no, dict):
        for chave, filho in no.items():
            yield from _folhas(filho, f'{onde}[{chave!r}]')
    elif isinstance(no, list):
        for i, filho in enumerate(no):
            yield from _folhas(filho, f'{onde}[{i}]')
    else:
        yield onde, no


def validar_manifesto(manifesto=None):
    manifesto = MANIFESTO if manifesto is None else manifesto
    erros, arquivos_vistos = [], set()
    for onde, imagem in _folhas(manifesto):
        if not isinstance(imagem, Imagem):
            erros.append(f'manifesto: {onde} = {imagem!r} não é Imagem')
            continue
        if imagem.escala is not None and not (len(imagem.escala) == 2 and all(
                _inteiro(v) and v > 0 for v in imagem.escala)):
            erros.append(f'manifesto: {onde} ("{imagem.arquivo}") com escala {imagem.escala!r} '
                         '(largura e altura > 0)')
        if imagem.arquivo in arquivos_vistos:   # o mesmo arquivo em várias escalas: confere 1 vez
            continue
        arquivos_vistos.add(imagem.arquivo)
        if '\\' in imagem.arquivo or imagem.arquivo.startswith('/'):
            erros.append(f'manifesto: "{imagem.arquivo}" precisa ser relativo a assets/img e usar "/"')
        elif not os.path.isfile(path('assets', 'img', *imagem.arquivo.split('/'))):
            erros.append(f'manifesto: arquivo ausente assets/img/{imagem.arquivo}')
    return erros


# ------------------------------------------------------------------ #
# Mapas (.tmj do Tiled)
# ------------------------------------------------------------------ #
class _LeitorDeMapa(MapLoader):
    """O loader do jogo, sem a imagem de fundo: lê só o .tmj."""

    def __init__(self, caminho):
        self.paredes, self.pontos_de_spawn = [], []
        self.zonas_void, self.void_points, self.navigation_zones = [], [], []
        self.player_spawn_manual = self.portal_pos = None
        self.carregar_json(caminho)


def caminho_do_mapa(chave):
    return path('assets', 'img', 'map', str(chave), f'm{chave}.tmj')


def validar_mapas(chaves=None, pools=None, bosses_por_fase=None):
    """Camadas obrigatórias (Colisoes e SpawnPoints, com objetos) e posições dentro do mapa.
    SpawnPlayer e Portal são opcionais: sem eles, o jogo usa o centro do mapa (`Mapa`).
    O tamanho vem do .tmj; o jogo usa o da imagem de fundo, que não é decodificada aqui."""
    chaves = list(MANIFESTO['maps']) if chaves is None else chaves
    pools = PHASE_POOLS if pools is None else pools
    bosses_por_fase = PHASE_BOSSES if bosses_por_fase is None else bosses_por_fase
    erros = []
    for chave in chaves:
        local = f'mapa {chave}'
        caminho = caminho_do_mapa(chave)
        try:
            with open(caminho, encoding='utf-8') as f:
                dados = json.load(f)
            largura = dados['width'] * dados['tilewidth']
            altura = dados['height'] * dados['tileheight']
            mapa = _LeitorDeMapa(caminho)
        except (OSError, ValueError, KeyError, TypeError) as erro:
            erros.append(f'{local}: .tmj ilegível ({caminho}: {type(erro).__name__}: {erro})')
            continue
        if not mapa.paredes:
            erros.append(f'{local}: sem paredes (camada "Colisoes" ausente ou vazia)')
        if not mapa.pontos_de_spawn:
            erros.append(f'{local}: sem pontos de spawn (camada "SpawnPoints" ausente ou vazia)')
        centro = pygame.math.Vector2(largura / 2, altura / 2)
        posicoes = [('spawn do jogador', mapa.player_spawn_manual or centro),
                    ('portal', mapa.portal_pos or centro)]
        posicoes += [(f'ponto de spawn {i}', p) for i, p in enumerate(mapa.pontos_de_spawn)]
        for nome, pos in posicoes:
            if not (0 <= pos.x <= largura and 0 <= pos.y <= altura):
                erros.append(f'{local}: {nome} em ({pos.x:.0f}, {pos.y:.0f}), fora do mapa {largura}x{altura}')
        fase = int(chave)
        if fase not in pools:
            erros.append(f'{local}: fase {fase} sem pool em PHASE_POOLS')
        if fase not in bosses_por_fase:
            erros.append(f'{local}: fase {fase} sem boss em PHASE_BOSSES')
    return erros


def validar_tudo():
    """Todos os erros de dados do jogo, numa lista só (vazia = tudo certo)."""
    return (validar_armas() + validar_spawner() + validar_motor_de_bosses() + validar_inimigos()
            + validar_manifesto() + validar_mapas())
