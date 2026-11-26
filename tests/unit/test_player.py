"""Dano, escudo, veículo, espinhos, XP/level-up e buff de cadência do Player real."""

import pygame

from source.systems.estados import LEVEL_UP
from source.systems.gameclock import relogio
from source.systems.levelup import ARMAS_REGISTRO, MAX_ARMAS
from source.systems.dano import Dano, DIRETO


# ── receber_dano (a matriz completa do contrato está em test_dano.py) ──
def test_dano_direto_na_vida_sem_escudo(player):
    player.receber_dano(Dano(100, DIRETO))
    assert player.vida_atual == player.vida_maxima - 100


def test_iframes_bloqueiam_segundo_hit_imediato(player):
    player.receber_dano(Dano(100, DIRETO))
    player.receber_dano(Dano(100, DIRETO))
    assert player.vida_atual == player.vida_maxima - 100


def test_iframes_expiram_apos_duracao(player):
    player.receber_dano(Dano(100, DIRETO))
    relogio.avancar((player.duracao_invencibilidade + 1) / 1000)
    player.atualizar_invencibilidade()
    player.receber_dano(Dano(100, DIRETO))
    assert player.vida_atual == player.vida_maxima - 200


def test_escudo_absorve_e_transborda_para_vida(player):
    player.adicionar_escudo(50)
    player.receber_dano(Dano(80, DIRETO))
    assert player.escudo_atual == 0
    assert player.vida_atual == player.vida_maxima - 30


def test_veiculo_absorve_todo_o_dano_e_e_destruido(player):
    class VeiculoFake:
        destruido = False

        def destruir(self):
            self.destruido = True

    v = VeiculoFake()
    player.entrar_veiculo(v, vida_maxima=50)
    player.receber_dano(Dano(80, DIRETO))
    assert v.destruido and player.vida_veiculo_atual == 0
    assert player.vida_atual == player.vida_maxima   # sem transbordo


def test_morte_clampa_vida_e_remove_sprite(player):
    player.receber_dano(Dano(10 ** 6, DIRETO, ignora_iframes=True))
    assert player.vida_atual == 0 and not player.alive()


def test_game_over_quando_vida_zera(novo_jogo):
    novo_jogo.player.receber_dano(Dano(10 ** 6, DIRETO, ignora_iframes=True))
    novo_jogo.update(1 / 60)
    assert novo_jogo.estado_do_jogo == 'game_over'


def test_level_up_cura_metade_e_enche_o_escudo(player):
    player.adicionar_escudo(80)
    player.escudo_atual = 30
    player.receber_dano(Dano(400, DIRETO, ignora_iframes=True))   # escudo 0, vida 500 - 370
    vida = player.vida_atual
    player.level_up()
    assert player.vida_atual == vida + player.vida_maxima / 2
    assert player.escudo_atual == 80


# ── Escudo: regeneração ─────────────────────────────────────────────────────
def test_escudo_regenera_apos_tempo_sem_dano(player):
    player.adicionar_escudo(100)
    player.shield_regen, player.velocidade_regen_escudo = 1000, 50
    player.receber_dano(Dano(60, DIRETO))
    player.atualizar_escudo(1.0)
    assert player.escudo_atual == 40               # ainda no delay
    relogio.avancar(1.0)
    player.atualizar_escudo(1.0)
    assert player.escudo_atual == 90
    player.atualizar_escudo(1.0)
    assert player.escudo_atual == 100 and not player.regenerando_escudo   # clamp


# ── Espinhos (Mjolnir Punch) ─────────────────────────────────────────────────
class _Alvo:
    dano = 5

    def __init__(self):
        self.recebido = 0
        self.posicao = pygame.math.Vector2(0, 0)
        self.rect = pygame.Rect(0, 0, 10, 10)

    def receber_dano(self, dano):
        self.recebido += dano.valor


def test_espinhos_contra_atacam_e_entram_em_cooldown(player):
    player.configurar_espinhos(dano=30, cooldown=1000)
    player.espinho_disponivel = True
    alvo = _Alvo()
    player.contra_atacar_com_espinhos(alvo)
    assert alvo.recebido == 30 and not player.espinho_disponivel
    player.atualizar_espinhos()
    assert not player.espinho_disponivel
    relogio.avancar(1.0)
    player.atualizar_espinhos()
    assert player.espinho_disponivel


# ── XP / level-up ────────────────────────────────────────────────────────────


def test_level_up_aplica_bonus_e_abre_tela(player):
    nivel, vida_max, vel = player.contador_niveis, player.vida_maxima, player.velocidade
    player.ganhar_xp(player.experiencia_level_up)
    assert player.contador_niveis == nivel + 1
    assert player.vida_maxima == vida_max + 25
    assert player.velocidade == vel + 10
    assert player.pontuacao == 100
    assert player.experiencia_level_up == player.experiencia_level_up_base + 10 * player.contador_niveis
    assert player.game.estado_do_jogo == 'level_up'
    assert player.game.sessao.tela_de_upgrade_ativa is not None


def test_ganho_grande_processa_varios_niveis_e_enfileira_telas(player):
    player.ganhar_xp(10_000)
    assert player.contador_niveis > 5
    assert player.experiencia_atual < player.experiencia_level_up
    # uma tela aberta, o resto aguardando na fila
    assert len(player.fila_upgrades) == player.contador_niveis - 2


def test_upgrade_forcado_usa_arma_informada(player):
    player.ativar_upgrade_forcado('assault_rifle')
    tela = player.game.sessao.tela_de_upgrade_ativa
    assert tela.modo_unico and tela.ids_das_opcoes == ['assault_rifle']


# ── Nível máximo (roteiro E6): nenhuma tela vazia nem upgrade de arma no máximo ──
def _maximizar(arma):
    while arma.upgrade():
        pass
    return arma


def _arsenal_cheio_no_maximo(player):
    player.armas.clear()
    for id_arma in sorted(ARMAS_REGISTRO)[:MAX_ARMAS]:
        player.armas[id_arma] = _maximizar(ARMAS_REGISTRO[id_arma].criar(player, player.game))


def _sem_tela(player):
    return (player.game.estado_do_jogo != LEVEL_UP and player.game.sessao.tela_de_upgrade_ativa is None
            and not player.fila_upgrades)


def test_level_up_sem_opcoes_nao_abre_tela_e_o_nivel_sobe(player):
    _arsenal_cheio_no_maximo(player)
    nivel, vida_max = player.contador_niveis, player.vida_maxima
    player.ganhar_xp(player.experiencia_level_up)
    assert player.contador_niveis == nivel + 1 and player.vida_maxima == vida_max + 25
    assert _sem_tela(player)


def test_upgrade_forcado_na_fila_revalida_a_arma(player):
    # 2 itens da mesma arma a 1 nível do máximo: a 1ª tela a leva ao máximo; a 2ª, na fila,
    # não pode oferecer a arma no máximo (vai para outra ou não abre).
    rifle = player.armas['assault_rifle']
    while rifle.nivel < rifle.nivel_maximo - 1:
        rifle.upgrade()
    player.ativar_upgrade_forcado('assault_rifle')
    player.ativar_upgrade_forcado('assault_rifle')
    assert player.fila_upgrades == ['assault_rifle']
    player.game.event_manager.tratar_level_up(_enter())
    assert rifle.no_maximo and _sem_tela(player)


def _enter():
    return pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0)


# ── Escudo de fábrica e MK-2 ─────────────────────────────────────────────────
def test_escudo_de_fabrica_fixo_e_o_mk2_o_melhora(novo_jogo):
    p = novo_jogo.player
    base = (p.escudo_maximo, p.shield_regen, p.velocidade_regen_escudo)
    assert p.escudo_atual == p.escudo_maximo > 0 and min(base) > 0   # nasce com escudo regenerativo
    p.level_up()
    assert (p.escudo_maximo, p.shield_regen, p.velocidade_regen_escudo) == base   # o nível do jogador não mexe
    mk2 = ARMAS_REGISTRO['mk2_shield'].criar(p, novo_jogo)
    p.armas['mk2_shield'] = mk2
    mk2.equipar()
    assert p.escudo_maximo == base[0]                 # MK-2 nível 1 = o de fábrica
    mk2.upgrade()
    assert p.escudo_maximo > base[0] and p.velocidade_regen_escudo > base[2]
