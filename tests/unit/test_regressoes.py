"""Regressões dos bugs corrigidos em 2026-11-21 (ver docs/log.md). Cada teste falhava antes da correção."""
import inspect
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
from source.feats.weapons import Arma
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
    didact = novo_jogo.sessao.boss_atual
    assert didact.collision_rect is didact.hitbox


# ── Bosses: vida de debug esquecida (Jega com vida_base=10)
# Exceções declaradas (decisão do usuário), com piso próprio para ainda pegar valor de debug:
# o Hunter tem 120 de vida, compensados pela Defesa de 90% fora das costas.
VIDA_MINIMA_BOSS = {'hunter': 100}


@pytest.mark.parametrize('nome', sorted(n for n, c in BOSS_CLASSES.items() if issubclass(c, BaseEnemy)))
def test_boss_tem_vida_de_boss(novo_jogo, nome):
    novo_jogo.spawner.spawnar(nome)
    assert novo_jogo.sessao.boss_atual.vida_maxima >= VIDA_MINIMA_BOSS.get(nome, 500)


# ── Warden
def test_warden_dropa_onde_caiu_o_ultimo_corpo_e_morre(novo_jogo):
    novo_jogo.spawner.spawnar('warden')
    consciencia = novo_jogo.sessao.boss_atual
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
    # Desde a E4 os grupos vêm do entity_manager pelo nome (não há mais lista posicional).
    for nome in ('all_sprites', 'inimigos_grupo', 'items_grupo', 'auras_grupo'):
        assert getattr(arma, nome) is getattr(entity_manager, nome)


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


def _perfil(info):
    return WEAPON_DATA.get(getattr(info.classe, 'NOME_ASSET', None))


def _procura_alvo(classe):
    """O código da classe (ou de uma base dela, como a ArmaDeRajada) chama uma busca de alvo.
    A `Arma` fica de fora: é ela que define as buscas."""
    return any('encontrar_inimigo_' in inspect.getsource(c)
               for c in classe.__mro__ if issubclass(c, Arma) and c is not Arma)


ARMAS_QUE_MIRAM = sorted(i for i, info in ARMAS_REGISTRO.items()
                         if _perfil(info) and _procura_alvo(info.classe))


def test_toda_arma_que_mira_tem_alcance_no_weapon_data():
    assert len(ARMAS_QUE_MIRAM) == 13
    sem_alcance = [i for i in ARMAS_QUE_MIRAM if 'raio_maximo' not in _perfil(ARMAS_REGISTRO[i]).stats]
    assert sem_alcance == []


@pytest.mark.parametrize('id_arma', ARMAS_QUE_MIRAM)
def test_alcance_da_arma_vem_do_stat(novo_jogo, id_arma):
    """Light Rifle mirava com RAIO_ALVO fixo (1000): o card mostrava 'Alcance' subindo e nada mudava.
    Mudar o stat (upgrade ou weapon_data) precisa mudar o alcance de verdade."""
    arma = _equipar(novo_jogo, id_arma)
    base = arma.raio_maximo
    _inimigo(novo_jogo, novo_jogo.player.posicao + V(base + 25, 0))
    assert not arma.disparar()

    arma.raio_maximo = base + 50
    assert arma.disparar()


@pytest.mark.parametrize('id_arma', [i for i in ARMAS_QUE_MIRAM
                                     if _perfil(ARMAS_REGISTRO[i]).stats['raio_maximo'].increase])
def test_upgrade_de_alcance_soma_no_stat(novo_jogo, id_arma):
    arma = _equipar(novo_jogo, id_arma)
    base = arma.raio_maximo
    arma.upgrade()
    assert arma.raio_maximo == base + _perfil(ARMAS_REGISTRO[id_arma]).stats['raio_maximo'].increase


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
    assert hud.foco_barra_vida is novo_jogo.sessao.boss_atual


# ── Paredes: inimigo longe do jogador atravessava paredes (recebia só as paredes perto DO JOGADOR)
def _distancia_ao_segmento(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared()))
    return p.distance_to(a + t * ab)


def _segmento_longe_do_jogador(mapa, pos_jogador):
    """Um segmento longo cuja parede inteira está fora da caixa de ±500 px em volta do jogador
    (o filtro antigo, `get_paredes_proximas`, que a C1 removeu)."""
    for parede in mapa.paredes:
        pts = parede['pontos']
        x0, x1 = min(p.x for p in pts) - 600, max(p.x for p in pts) + 600
        y0, y1 = min(p.y for p in pts) - 600, max(p.y for p in pts) + 600
        if x0 <= pos_jogador.x <= x1 and y0 <= pos_jogador.y <= y1:
            continue
        for a, b in zip(pts, pts[1:]):
            if a.distance_to(b) > 120:
                return V(a), V(b)
    raise AssertionError('o mapa da fase 0 não tem parede longe do spawn do jogador')


def test_inimigo_longe_do_jogador_colide_com_a_parede_perto_dele(novo_jogo):
    a, b = _segmento_longe_do_jogador(novo_jogo.mapa, novo_jogo.player.posicao)
    normal = (b - a).rotate(90).normalize()
    inimigo = _inimigo(novo_jogo, (a + b) / 2 + normal * 5)   # 5 px de uma parede, raio 15
    assert _distancia_ao_segmento(inimigo.posicao, a, b) < inimigo.raio_colisao_mapa

    novo_jogo.update(1 / 60)

    assert _distancia_ao_segmento(inimigo.posicao, a, b) >= inimigo.raio_colisao_mapa - 0.5


# ── Telas: colaboradores desenhava self.imagem, mas o atributo é self.image
def test_tela_de_colaboradores_desenha_sem_erro(game):
    """AttributeError a cada frame: o Renderer engolia o erro e mostrava 'Erro ao renderizar'."""
    game.tela_colaboradores.draw(game.tela)


# ── Gravemind
def test_nevoa_do_gravemind_passa_pelo_contrato_de_dano(novo_jogo):
    """MiasmaGas fazia `vida_atual -= 300` direto: ignorava escudo e veículo e não matava o jogador."""
    from source.enemies.bosses.gravemind.vfx import MiasmaGas
    from source.systems.dano import AREA
    from source.systems.eventos import DANO_CAUSADO, eventos

    player = novo_jogo.player
    boss = _inimigo(novo_jogo, player.posicao + V(2000, 0))
    nevoa = MiasmaGas(boss.posicao, raio_seguro=100, game=novo_jogo,
                      grupos=(entity_manager.all_sprites,), boss=boss)
    player.adicionar_escudo(1000)
    recebidos = []
    eventos.assinar(DANO_CAUSADO, lambda **d: recebidos.append(d))
    relogio.avancar(1.0)
    nevoa.update(1 / 60)
    assert player.escudo_atual == 700 and player.vida_atual == player.vida_maxima
    assert recebidos[0]['dano'].tipo == AREA and recebidos[0]['dano'].fonte is boss


# ── Cura em jogador morto
def test_orbe_de_vida_no_frame_da_morte_nao_ressuscita(novo_jogo):
    """Morrer (contato) e pegar um orbe de vida no mesmo frame devolvia a vida a um jogador já fora
    dos grupos de sprite: a partida seguia com ele invisível, sem game over."""
    from source.feats.items import Items
    from source.systems.dano import Dano, DIRETO
    from source.systems.estados import GAME_OVER

    player = novo_jogo.player
    player.receber_dano(Dano(10 ** 6, DIRETO, ignora_iframes=True))
    Items(player.posicao, 'life_orb', (entity_manager.items_grupo,)).coletar(player)
    assert player.vida_atual == 0
    novo_jogo.update(1 / 60)
    assert novo_jogo.estado_do_jogo == GAME_OVER


def test_level_up_no_frame_da_morte_nao_ressuscita(novo_jogo):
    from source.systems.dano import Dano, DIRETO

    player = novo_jogo.player
    player.receber_dano(Dano(10 ** 6, DIRETO, ignora_iframes=True))
    player.ganhar_xp(player.experiencia_level_up)
    assert player.vida_atual == 0


# ── Troca de fase (achado na E5)
def test_companheiros_vao_para_o_spawn_do_mapa_novo(novo_jogo):
    """Liam o spawn do mapa ANTIGO (antes de trocar o mapa) e cruzavam o mapa voando até o jogador."""
    from source.feats.buddies import Companheiro

    for id_arma in ('arbiter', 'cortana', 'marine', 'noble'):
        novo_jogo.event_manager._aplicar_escolha_de_upgrade(id_arma)
    spawn_antigo = V(novo_jogo.mapa.get_player_spawn_pos())
    novo_jogo.stage_manager._trocar_dados_fase()
    spawn = V(novo_jogo.mapa.get_player_spawn_pos())
    assert spawn != spawn_antigo   # senão o teste não distingue os dois mapas
    companheiros = [s for s in entity_manager.all_sprites if isinstance(s, Companheiro)]
    assert len(companheiros) == 4
    assert all(c.posicao == spawn and c.rect.center == (round(spawn.x), round(spawn.y))
               for c in companheiros)
    assert novo_jogo.player.posicao == spawn


@pytest.mark.parametrize('id_veiculo', ['warhog', 'pelican'])
@pytest.mark.parametrize('embarcado', [True, False])
def test_veiculo_sobrevive_a_troca_de_fase(novo_jogo, id_veiculo, embarcado):
    """O veículo saía dos grupos (kill) na troca de fase, mas a arma continuava atualizando o sprite:
    invisível, seguia atirando e atropelando, e o jogador continuava "no veículo"."""
    novo_jogo.event_manager._aplicar_escolha_de_upgrade(id_veiculo)
    veiculo = novo_jogo.player.armas[id_veiculo].sprite_veiculo
    if embarcado:
        veiculo.entrar()
    novo_jogo.stage_manager._trocar_dados_fase()
    assert veiculo.alive() and veiculo in entity_manager.all_sprites   # desenhado de novo
    assert veiculo.embarcado == embarcado and novo_jogo.player.in_veicule == embarcado
    spawn = V(novo_jogo.mapa.get_player_spawn_pos())
    assert veiculo.posicao == spawn   # estacionado: vem junto, não fica nas coordenadas do mapa velho
    novo_jogo.update(1 / 60)
    assert veiculo.alive()
    if embarcado:
        assert veiculo.posicao == novo_jogo.player.posicao
