"""Regressões dos bugs corrigidos em 2026-11-21 (ver docs/log.md). Cada teste falhava antes da correção."""
import os
import sys

import pygame
import pytest

from helpers import MapaSemImagem
from source.data.weapon_data import COMPANION_DATA, VEHICLES_DATA, WEAPON_DATA
from source.enemies.base.enemy_base import BaseEnemy
from source.enemies.bosses.warden.core import BaseWarden
from source.enemies.standard.grunt import GruntRed
from source.enemies.standard.watcher import SuperWatcher
from source.feats.grenades import FuelRodGrenade
from source.feats.skills.artilharia import ArtilhariaAviso
from source.feats.skills.artilharia.config import ArtilhariaConfig
from source.feats.skills.onda_emp.core import OndaEMP
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.systems.levelup import ARMAS_REGISTRO
from source.systems.mapmanager import Mapa
from source.systems.spawner.spawner_bosses import BOSS_CLASSES
from source.systems.spawner.spawner_pools import PHASE_POOLS
from source.windows.ranking import ranking_data

V = pygame.math.Vector2


def _equipar(game, id_arma):
    game.event_manager._aplicar_escolha_de_upgrade(id_arma)
    return game.player.armas[id_arma]


def _inimigo(game, pos, vida=1000):
    e = GruntRed(posicao=V(pos), game=game)
    e.vida, e.escudo_atual = vida, 0
    return e


# ── MRO: método de mixin do inimigo escondido por BaseEnemy (Gravemind.animar, Didact.collision_rect)
def _classes_de_inimigos():
    import source.enemies.bosses.gravemind.core as gm
    classes = {c for c in BOSS_CLASSES.values() if issubclass(c, BaseEnemy)}
    classes |= {c for pool in PHASE_POOLS.values() for c in pool['classes']}
    classes |= {gm.FinalGravemind, gm.ProtoGravemind, SuperWatcher, BaseWarden}
    return sorted(classes, key=lambda c: c.__name__)


@pytest.mark.parametrize('classe', _classes_de_inimigos(), ids=lambda c: c.__name__)
def test_nenhum_mixin_do_inimigo_e_anulado_por_base_enemy(classe):
    base = set(BaseEnemy.__mro__)
    anulados = []
    for mixin in classe.__mro__:
        if mixin in base or mixin is object:
            continue
        for nome in vars(mixin):
            if nome.startswith('__'):
                continue
            dono = next(k for k in classe.__mro__ if nome in vars(k))
            if dono is not mixin and dono in base:
                anulados.append(f'{mixin.__name__}.{nome} (vence {dono.__name__})')
    assert anulados == [], 'coloque o mixin ANTES de BaseEnemy na herança'


def test_didact_colide_pela_hitbox(novo_jogo):
    novo_jogo.spawner.spawnar('didact')
    didact = novo_jogo.boss_atual
    assert didact.collision_rect is didact.hitbox


# ── Bosses: vida de debug esquecida (Jega com vida_base=10)
@pytest.mark.parametrize('nome', sorted(n for n, c in BOSS_CLASSES.items() if issubclass(c, BaseEnemy)))
def test_boss_tem_vida_de_boss(novo_jogo, nome):
    novo_jogo.spawner.spawnar(nome)
    assert novo_jogo.boss_atual.vida_maxima >= 500


# ── Warden
def test_warden_dropa_onde_caiu_o_ultimo_corpo_e_morre(novo_jogo):
    novo_jogo.spawner.spawnar('warden')
    consciencia = novo_jogo.boss_atual
    corpos = list(consciencia.wardens_vivos)
    for corpo in corpos:
        corpo.vida = 0
    novo_jogo.collision_manager.update(1 / 60)
    consciencia.update(1 / 60)
    assert not consciencia.alive()
    assert len(entity_manager.items_grupo) > 0
    ultimo = consciencia.ultima_posicao_corpo
    for item in entity_manager.items_grupo:
        assert V(item.rect.center).distance_to(ultimo) <= 40


def test_corpo_do_warden_sem_manager_morre_sem_erro(novo_jogo):
    corpo = BaseWarden(posicao=novo_jogo.player.posicao + V(300, 0), game=novo_jogo, jogador=novo_jogo.player,
                       variante='default', vida=100, velocidade=80, funcao_atual='COMBATENTE', manager=None)
    corpo.morrer()
    assert not corpo.alive()


# ── Inimigos comuns
def test_super_watcher_usa_variante_omega(novo_jogo):
    w = SuperWatcher(posicao=novo_jogo.player.posicao + V(300, 0), game=novo_jogo)
    assert w.variante == 'omega'
    assert w.image.get_size() == (144, 144)


# ── Armas
@pytest.mark.parametrize('id_arma', sorted(ARMAS_REGISTRO))
def test_arma_mira_no_grupo_de_inimigos(novo_jogo, id_arma):
    """Fuel Rod recebia items_grupo no lugar de inimigos_grupo (ordem errada em ARMAS_REGISTRO)."""
    arma = novo_jogo.player.armas.get(id_arma) or _equipar(novo_jogo, id_arma)
    if hasattr(arma, 'inimigos_grupo'):
        assert arma.inimigos_grupo is entity_manager.inimigos_grupo


def test_nenhum_range_val_lista_nivel_1_inalcancavel():
    """O nível 1 nunca recebe upgrade (nivel começa em 1 e upgrade() incrementa antes)."""
    for dados in (WEAPON_DATA, COMPANION_DATA, VEHICLES_DATA):
        for nome, perfil in dados.items():
            for attr, meta in perfil.stats.items():
                if isinstance(meta.range_val, list):
                    assert 1 not in meta.range_val, f'{nome}.{attr}'


def test_shotgun_usa_stat_spread(novo_jogo):
    shotgun = _equipar(novo_jogo, 'shotgun')
    shotgun.spread = 0
    _inimigo(novo_jogo, novo_jogo.player.posicao + V(200, 0))
    antes = set(entity_manager.projeteis_jogador_grupo)
    assert shotgun.disparar()
    novos = [p for p in entity_manager.projeteis_jogador_grupo if p not in antes]
    assert len(novos) > 1
    assert all(p.direcao == novos[0].direcao for p in novos)


def test_pelican_usa_o_proprio_perfil(novo_jogo):
    pelican = _equipar(novo_jogo, 'pelican')
    assert pelican.nome == 'Pelican'
    assert pelican.sprite_veiculo.vida_maxima == VEHICLES_DATA['pelican'].stats['vida_maxima'].value


ARMAS_DE_RAJADA = ['dizimator', 'needler', 'carabin', 'light_rifle', 'machine_gun']


@pytest.mark.parametrize('id_arma', ARMAS_DE_RAJADA)
def test_rajada_sem_alvo_nao_gasta_cooldown(novo_jogo, id_arma):
    arma = _equipar(novo_jogo, id_arma)
    arma.ultimo_tiro = 0
    arma.update(1 / 60)
    assert arma.ultimo_tiro == 0 and arma.tiros_restantes == 0

    _inimigo(novo_jogo, novo_jogo.player.posicao + V(100, 0))
    relogio.avancar(0.2)                       # passa o throttle de busca (100 ms)
    arma.update(1 / 60)
    assert arma.ultimo_tiro == relogio.agora()


# ── Fuel Rod: impacto + veneno + quique
def test_artilharia_impacto_com_dot(novo_jogo):
    alvo = _inimigo(novo_jogo, novo_jogo.player.posicao + V(400, 0))
    cfg = ArtilhariaConfig(dano=50, raio_explosao=100, duracao=0, dot=True, impacto_com_dot=True,
                           dano_por_segundo=7, duracao_dot=3000)
    aviso = ArtilhariaAviso(alvo.posicao, (entity_manager.all_sprites,), novo_jogo, dono='PLAYER', custom_config=cfg)
    aviso.update(1 / 60)
    assert alvo.vida == 950
    relogio.avancar(1.0)
    aviso.update(1 / 60)
    assert alvo.vida == 943


def test_artilharia_dot_padrao_continua_sem_impacto(novo_jogo):
    alvo = _inimigo(novo_jogo, novo_jogo.player.posicao + V(400, 0))
    cfg = ArtilhariaConfig(dano=50, raio_explosao=100, duracao=0, dot=True, dano_por_segundo=7)
    ArtilhariaAviso(alvo.posicao, (entity_manager.all_sprites,), novo_jogo, dono='PLAYER',
                    custom_config=cfg).update(1 / 60)
    assert alvo.vida == 1000


def _granada_fuel_rod(game, quiques):
    p = game.player.posicao
    return FuelRodGrenade(posicao_inicial=p, posicao_alvo=p + V(300, 0), grupos=(entity_manager.all_sprites,),
                          game=game, dono='PLAYER', inimigos_grupo=entity_manager.inimigos_grupo,
                          custom_config=ArtilhariaConfig(), quiques=quiques)


def test_fuel_rod_quica_para_inimigo_proximo(novo_jogo):
    granada = _granada_fuel_rod(novo_jogo, quiques=1)
    alvo = _inimigo(novo_jogo, granada.target_pos + V(150, 0))
    granada._explodir_sem_grude()
    assert granada.alive() and granada.quiques == 0
    assert granada.target_pos == alvo.posicao
    granada._explodir_sem_grude()               # sem quiques: explode
    assert not granada.alive()
    assert any(isinstance(s, ArtilhariaAviso) for s in entity_manager.all_sprites)


def test_fuel_rod_sem_alvo_por_perto_explode(novo_jogo):
    granada = _granada_fuel_rod(novo_jogo, quiques=3)
    _inimigo(novo_jogo, granada.target_pos + V(2000, 0))
    granada._explodir_sem_grude()
    assert not granada.alive()


def test_fuel_rod_liga_stats_de_upgrade(novo_jogo):
    fuel = _equipar(novo_jogo, 'fuel_rod')
    _inimigo(novo_jogo, novo_jogo.player.posicao + V(300, 0))
    assert fuel.disparar()
    granada = next(s for s in entity_manager.all_sprites if isinstance(s, FuelRodGrenade))
    cfg = granada.custom_config
    assert cfg.dot and cfg.impacto_com_dot
    assert (cfg.dano, cfg.dano_por_segundo, cfg.duracao_dot) == (fuel.dano, fuel.dot, fuel.duracao)
    assert granada.quiques == fuel.quique


# ── Onda EMP: jogador colado no centro não era atingido (raio negativo ao quadrado)
def test_emp_atinge_jogador_no_centro(novo_jogo):
    p = novo_jogo.player
    onda = OndaEMP(p.posicao + V(2, 0), (entity_manager.all_sprites,), novo_jogo, atacante=p)
    onda.cfg = type(onda.cfg)(**{**vars(onda.cfg), 'velocidade_expansao': 600})
    vida = p.vida_atual
    onda.update(0.05)                           # dt máximo do jogo: a borda "pula" o centro
    assert onda.atingiu_jogador and p.vida_atual < vida


# ── Mapa / ranking
def test_spawn_manual_na_origem_e_respeitado():
    mapa = MapaSemImagem()
    mapa.player_spawn_manual = V(0, 0)
    assert Mapa.get_player_spawn_pos(mapa) == V(0, 0)


def test_ranking_no_exe_vai_para_appdata(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setenv('APPDATA', str(tmp_path))
    assert ranking_data.caminho_padrao_ranking() == os.path.join(str(tmp_path), 'ProjectHalo', 'ranking.json')


def test_ranking_em_dev_usa_arquivo_do_repo():
    assert ranking_data.caminho_padrao_ranking() == os.path.abspath(os.path.join('assets', 'data', 'ranking.json'))


# ── HUD
def test_hud_foco_do_boss_usa_relogio_de_jogo(novo_jogo, monkeypatch):
    """Usava pygame.time.get_ticks(): a barra do boss dependia do relógio de parede, e a
    contagem de alocações da catraca (A2) variava entre rodadas iguais."""
    hud = novo_jogo.hud
    monkeypatch.setattr(pygame.time, 'get_ticks', lambda: 10 ** 9)   # parede "andou" muito
    hud._ultimo_check_boss = relogio.agora()
    hud.foco_barra_vida = None
    novo_jogo.spawner.spawnar('hunter')

    hud._atualizar_boss_foco()
    assert hud.foco_barra_vida is None   # jogo parado: ainda dentro do intervalo
    relogio.avancar(hud._intervalo_check_boss / 1000)
    hud._atualizar_boss_foco()
    assert hud.foco_barra_vida is novo_jogo.boss_atual
