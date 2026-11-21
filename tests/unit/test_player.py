"""Dano, escudo, veículo, espinhos, XP/level-up e buff de cooldown do Player real."""
import pytest

from source.systems.gameclock import relogio


# ── receber_dano ─────────────────────────────────────────────────────────────
def test_dano_direto_na_vida_sem_escudo(player):
    player.receber_dano(100)
    assert player.vida_atual == player.vida_maxima - 100


def test_iframes_bloqueiam_segundo_hit_imediato(player):
    player.receber_dano(100)
    player.receber_dano(100)
    assert player.vida_atual == player.vida_maxima - 100


def test_iframes_expiram_apos_duracao(player):
    player.receber_dano(100)
    relogio.avancar((player.duracao_invencibilidade + 1) / 1000)
    player.atualizar_invencibilidade()
    player.receber_dano(100)
    assert player.vida_atual == player.vida_maxima - 200


def test_dano_direto_ignora_invencibilidade(player):
    player.receber_dano(10)
    player.tomar_dano_direto(10)
    assert player.vida_atual == player.vida_maxima - 20


def test_escudo_absorve_e_transborda_para_vida(player):
    player.adicionar_escudo(50)
    player.receber_dano(80)
    assert player.escudo_atual == 0
    assert player.vida_atual == player.vida_maxima - 30


def test_escudo_absorve_dano_parcial_sem_tocar_vida(player):
    player.adicionar_escudo(50)
    player.receber_dano(20)
    assert player.escudo_atual == 30 and player.vida_atual == player.vida_maxima


def test_veiculo_absorve_todo_o_dano_e_e_destruido(player):
    class VeiculoFake:
        destruido = False

        def destruir(self):
            self.destruido = True

    v = VeiculoFake()
    player.entrar_veiculo(v, vida_maxima=50)
    player.receber_dano(80)
    assert v.destruido and player.vida_veiculo_atual == 0
    assert player.vida_atual == player.vida_maxima   # sem transbordo


def test_morte_clampa_vida_e_remove_sprite(player):
    player.tomar_dano_direto(10 ** 6)
    assert player.vida_atual == 0 and not player.alive()


def test_game_over_quando_vida_zera(novo_jogo):
    novo_jogo.player.tomar_dano_direto(10 ** 6)
    novo_jogo.update(1 / 60)
    assert novo_jogo.estado_do_jogo == 'game_over'


def test_curar_nao_passa_do_maximo(player):
    player.tomar_dano_direto(10)
    player.curar(10 ** 6)
    assert player.vida_atual == player.vida_maxima


# ── Escudo: regeneração ─────────────────────────────────────────────────────
def test_escudo_regenera_apos_tempo_sem_dano(player):
    player.adicionar_escudo(100)
    player.shield_regen, player.velocidade_regen_escudo = 1000, 50
    player.receber_dano(60)
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

    def receber_dano(self, q):
        self.recebido += q


def test_espinhos_contra_atacam_e_entram_em_cooldown(player):
    player.configurar_espinhos(dano=30, cooldown=1000)
    player.espinho_disponivel = True
    alvo = _Alvo()
    player.tomar_dano(alvo, colisao=True)
    assert alvo.recebido == 30 and not player.espinho_disponivel
    player.atualizar_espinhos()
    assert not player.espinho_disponivel
    relogio.avancar(1.0)
    player.atualizar_espinhos()
    assert player.espinho_disponivel


def test_sem_espinhos_configurados_nao_contra_ataca(player):
    alvo = _Alvo()
    player.tomar_dano(alvo, colisao=True)
    assert alvo.recebido == 0


# ── XP / level-up ────────────────────────────────────────────────────────────
def test_xp_insuficiente_nao_sobe_nivel(player):
    player.ganhar_xp(player.experiencia_level_up - 1)
    assert player.contador_niveis == 1 and not player.fila_upgrades


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


def test_upgrade_forcado_sem_armas_vira_level_up(player):
    player.armas.clear()
    player.ativar_upgrade_forcado('assault_rifle')
    assert player.contador_niveis == 2


# ── Buff de cooldown (item café) ─────────────────────────────────────────────
def test_buff_reduz_cooldown_pela_metade_e_restaura(player):
    arma = player.armas['assault_rifle']
    original = arma.cooldown
    player.adicionar_tempo_buff(1.0)
    player.atualizar_buff(0.5)
    player.atualizar_buff(0.1)          # idempotente: não reduz de novo
    assert arma.cooldown == pytest.approx(original / 2)
    player.atualizar_buff(1.0)          # zera o timer
    player.atualizar_buff(0.1)          # remove o buff
    assert arma.cooldown == pytest.approx(original)
    assert not player.buff_cooldown_ativo


def test_buff_ignora_arma_com_cooldown_infinito(player):
    class ArmaPassiva:
        cooldown = float('inf')

    player.armas['passiva'] = ArmaPassiva()
    player.adicionar_tempo_buff(1.0)
    player.atualizar_buff(0.1)
    assert player.armas['passiva'].cooldown == float('inf')
