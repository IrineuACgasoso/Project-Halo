"""Spawner, colisão, itens, pontuação, transição de fase e estados do EventManager."""
import random

import pygame
import pytest

from source.enemies.standard.grunt import GruntRed
from source.feats.assets import ASSETS
from source.feats.grenades import Spike
from source.feats.items import Items
from source.systems.collision import CollisionManager
from source.systems.entitymanager import entity_manager
from source.systems.spawner import spawner as spawner_mod
from source.systems.spawner.spawner_bosses import BOSS_CLASSES, CRONOGRAMA_BOSSES

V = pygame.math.Vector2


# ── Configuração do spawner ─────────────────────────────────────────────────
# Pools e os 3 dicts de bosses: `validar_spawner` (test_validacao.py, roteiro D5).
def test_intervalo_de_spawn_diminui_com_o_tempo_ate_o_piso(novo_jogo):
    novo_jogo.sessao.timer_jogo = 0
    novo_jogo.spawner.update(0.01)
    assert novo_jogo.spawner.intervalo_spawn_atual == pytest.approx(2.5)
    novo_jogo.sessao.timer_jogo = 10_000
    novo_jogo.spawner.update(0.01)
    assert novo_jogo.spawner.intervalo_spawn_atual == 0.5


def test_spawn_respeita_teto_de_inimigos(novo_jogo, monkeypatch):
    monkeypatch.setattr(spawner_mod, 'MAX_INIMIGOS_VIVOS', 3)
    sp = novo_jogo.spawner
    for _ in range(5):
        sp.tempo_proximo_spawn = sp.intervalo_spawn_atual
        sp.update(0.01)
    assert len(entity_manager.inimigos_grupo) == 3


def test_boss_ativo_congela_spawner(novo_jogo):
    sp = novo_jogo.spawner
    sp.spawnar('hunter')
    assert novo_jogo.sessao.boss_atual is not None and novo_jogo.sessao.boss_atual.is_boss
    antes = len(entity_manager.inimigos_grupo)
    sp.tempo_proximo_spawn = 999
    sp.update(1.0)
    assert len(entity_manager.inimigos_grupo) == antes


def test_boss_spawna_no_horario_uma_unica_vez(novo_jogo):
    sp = novo_jogo.spawner
    novo_jogo.sessao.timer_jogo = CRONOGRAMA_BOSSES['hunter']
    sp.update(0.01)
    boss = novo_jogo.sessao.boss_atual
    assert type(boss) is BOSS_CLASSES['hunter'] and sp.boss_flags['hunter']
    novo_jogo.sessao.boss_atual = None
    sp.update(0.01)
    assert novo_jogo.sessao.boss_atual is None


def test_posicao_de_spawn_fora_da_tela_e_dentro_do_alcance(novo_jogo):
    random.seed(3)
    p = novo_jogo.player.posicao
    for _ in range(50):
        d2 = novo_jogo.spawner.calcular_posicao_spawn().distance_squared_to(p)
        assert d2 > (500 - 45) ** 2   # 500 px menos a variação aleatória de ±30 em cada eixo


# ── Colisão ──────────────────────────────────────────────────────────────────
class _Sprite(pygame.sprite.Sprite):
    def __init__(self, rect, **attrs):
        super().__init__()
        self.rect = pygame.Rect(rect)
        for k, v in attrs.items():
            setattr(self, k, v)


def test_alvo_invulneravel_nunca_colide():
    a, b = _Sprite((0, 0, 10, 10)), _Sprite((0, 0, 10, 10), invulneravel=True)
    assert not CollisionManager.custom_collision(a, b)


def test_hitbox_tem_prioridade_sobre_rect():
    a = _Sprite((0, 0, 10, 10))
    b = _Sprite((0, 0, 100, 100), hitbox=pygame.Rect(50, 50, 10, 10))
    assert not CollisionManager.custom_collision(a, b)
    b.hitbox = pygame.Rect(5, 5, 10, 10)
    assert CollisionManager.custom_collision(a, b)


def test_projetil_inimigo_usa_hitbox_do_jogador():
    jogador = _Sprite((0, 0, 100, 100), hitbox=pygame.Rect(40, 40, 20, 20))
    assert not CollisionManager.colisao_hitbox_jogador(jogador, _Sprite((0, 0, 10, 10)))
    assert CollisionManager.colisao_hitbox_jogador(jogador, _Sprite((45, 45, 5, 5)))


def test_inimigo_morto_e_removido_e_dropa(novo_jogo):
    random.seed(0)
    inimigo = GruntRed(posicao=novo_jogo.player.posicao + V(300, 0), game=novo_jogo)
    inimigo.receber_dano(inimigo.vida + inimigo.escudo_atual + 1)
    novo_jogo.collision_manager.update(1 / 60)
    assert not inimigo.alive()
    assert len(entity_manager.items_grupo) >= 1     # exp_shard tem 100% de chance


def test_dano_no_inimigo_consome_escudo_antes_da_vida(novo_jogo):
    inimigo = GruntRed(posicao=novo_jogo.player.posicao + V(300, 0), game=novo_jogo)
    inimigo.escudo_maximo = inimigo.escudo_atual = 20
    inimigo.vida = 100
    inimigo.receber_dano(15)
    assert inimigo.escudo_atual == 5 and inimigo.vida == 100
    inimigo.receber_dano(30)
    assert inimigo.escudo_atual == 0 and inimigo.vida == 75
    inimigo.receber_dano(1000)
    assert inimigo.vida == 0


def test_dificuldade_escala_com_nivel_do_jogador(novo_jogo):
    pos = novo_jogo.player.posicao + V(300, 0)
    base = GruntRed(posicao=pos, game=novo_jogo)
    novo_jogo.player.contador_niveis = 11
    forte = GruntRed(posicao=pos, game=novo_jogo)
    # enemy_scaling: mult = 1 + nivel/10 (vida e dano) -> nível 1: 1.1, nível 11: 2.1
    assert forte.vida_maxima == pytest.approx(base.vida_maxima / 1.1 * 2.1)
    assert forte.dano == pytest.approx(base.dano / 1.1 * 2.1)


# ── Itens ────────────────────────────────────────────────────────────────────
def test_drop_fixo_100_por_cento(novo_jogo):
    Items.spawn_drop(V(0, 0), (entity_manager.items_grupo,), exp_shard=(3, 100, 100))
    assert len(entity_manager.items_grupo) == 3


def test_drop_probabilidade_zero_nao_gera(novo_jogo):
    Items.spawn_drop(V(0, 0), (entity_manager.items_grupo,), life_orb=(1, 0, 100))
    # roll uniforme em [0, 100] só é <= 0 com probabilidade nula
    assert len(entity_manager.items_grupo) == 0


def test_drop_variavel_completa_soma_na_opcao_mais_provavel(novo_jogo, monkeypatch):
    monkeypatch.setattr(random, 'uniform', lambda a, b: b)   # pior caso: roll no topo da escala
    Items.spawn_drop(V(0, 0), (entity_manager.items_grupo,), big_shard=((2, 5), (10, 20), 100))
    assert len(entity_manager.items_grupo) == 5


def test_config_de_drop_invalida_e_ignorada(novo_jogo):
    Items.spawn_drop(V(0, 0), (entity_manager.items_grupo,), exp_shard=(1, 100), cafe='x')
    assert len(entity_manager.items_grupo) == 0


@pytest.mark.parametrize('tipo, efeito', [
    ('exp_shard', lambda p, a: p.experiencia_atual == a['xp'] + 10),
    ('big_shard', lambda p, a: p.experiencia_atual == a['xp'] + 50),
    ('life_orb', lambda p, a: p.vida_atual == p.vida_maxima),
])
def test_coletar_item_aplica_efeito(player, tipo, efeito):
    player.tomar_dano_direto(100)
    antes = {'xp': player.experiencia_atual}
    item = Items(player.posicao, tipo, (entity_manager.items_grupo,))
    item.coletar(player)
    assert efeito(player, antes)
    assert player.coletaveis[tipo] == 1


def test_item_upgrade_mira_arma_do_jogador(player):
    item = Items(player.posicao, 'upgrade', (entity_manager.items_grupo,))
    assert item.id_arma_alvo == 'assault_rifle'


# ── Granadas inimigas ────────────────────────────────────────────────────────
# Regressão: Player.sprites (dict de animação) era tratado como Group -> TypeError.
def test_granada_mirando_o_jogador_voa_sem_erro(novo_jogo):
    p = novo_jogo.player
    granada = Spike(posicao_inicial=p.posicao + V(400, 0), posicao_alvo=p.posicao,
                    grupos=(entity_manager.all_sprites,), jogador=p, game=novo_jogo,
                    dono='INIMIGO', preset='jega_spike')
    granada.update(1 / 60)


# ── Game / StageManager / EventManager ───────────────────────────────────────
def test_pontuacao_final_pondera_coletaveis(novo_jogo):
    p = novo_jogo.player
    p.experiencia_atual = 7
    p.coletaveis.update(exp_shard=2, big_shard=1, life_orb=1, cafe=1)
    novo_jogo._calcular_pontuacao_final()
    assert p.pontuacao == 7 + 2 * 1 + 1 * 2 + 1 * 3 + 1 * 10


def test_ultima_fase_encerra_campanha_em_vez_de_crashar(novo_jogo):
    novo_jogo.sessao.fase_atual = max(int(k) for k in ASSETS['maps'])
    assert not novo_jogo.existe_proxima_fase()
    novo_jogo.stage_manager.iniciar_transicao()
    assert novo_jogo.estado_do_jogo == 'game_over'
    assert not novo_jogo.stage_manager.transicao_ativa


def test_transicao_troca_de_fase_preservando_player_e_armas(novo_jogo):
    sm = novo_jogo.stage_manager
    GruntRed(posicao=novo_jogo.player.posicao + V(300, 0), game=novo_jogo)
    sm.iniciar_transicao()
    for _ in range(200):
        sm.update(1 / 60)
    assert novo_jogo.sessao.fase_atual == 1 and not sm.transicao_ativa
    assert novo_jogo.player.alive() and 'assault_rifle' in novo_jogo.player.armas
    assert len(entity_manager.inimigos_grupo) == 0
    assert novo_jogo.camera.mapa is novo_jogo.mapa
    assert novo_jogo.player.posicao == novo_jogo.mapa.get_player_spawn_pos()


def test_boss_derrotado_agenda_portal(novo_jogo):
    novo_jogo.spawner.spawnar('hunter')
    novo_jogo.sessao.boss_atual.kill()
    novo_jogo.update(1 / 60)
    assert novo_jogo.sessao.boss_atual is None and novo_jogo.sessao.spawnar_portal_em_breve
    for _ in range(130):
        novo_jogo.update(1 / 60)
    assert novo_jogo.sessao.portal_atual is not None


def _tecla(key, mod=0):
    return pygame.event.Event(pygame.KEYDOWN, key=key, mod=mod)


def test_esc_pausa_o_jogo(novo_jogo):
    novo_jogo.event_manager.tratar_jogando(_tecla(pygame.K_ESCAPE))
    assert novo_jogo.estado_do_jogo == 'pausa'


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    'BUG conhecido (achado na B4): tocar o portal da última fase e morrer no mesmo update chama '
    '_encerrar_partida duas vezes (finalizar_campanha e _checar_game_over), somando a pontuação '
    'final em dobro.'))
def test_fim_de_campanha_e_morte_no_mesmo_update_pontua_uma_vez(novo_jogo, monkeypatch):
    from source.feats.effects import Portal
    monkeypatch.setattr(novo_jogo, 'estados_estritos', False)   # 2ª ida a game_over seria exceção
    p = novo_jogo.player
    novo_jogo.sessao.fase_atual = max(int(k) for k in ASSETS['maps'])
    novo_jogo.sessao.portal_atual = Portal(p.posicao, entity_manager.all_sprites)
    p.experiencia_atual = 7
    p.vida_atual = 0
    pontos_antes = p.pontuacao
    novo_jogo.update(1 / 60)
    assert novo_jogo.estado_do_jogo == 'game_over'
    assert p.pontuacao == pontos_antes + 7
