"""Contrato de dano único (roteiro E1): `Dano` + `receber_dano(dano)` no jogador e nos inimigos,
os ganchos dos bosses, o evento `dano_causado` e a fonte de projéteis e habilidades."""
import ast
import math
import pathlib

import pygame
import pytest

from source.enemies.standard.grunt import GruntRed
from source.feats.projetil import BurstRifle, PlasmaGun
from source.feats.skills.artilharia import ArtilhariaAviso
from source.systems.dano import (AREA, AURA, CONTATO, DIRETO, PROJETIL, TIPOS_DANO, VOID, Dano,
                                 fonte_do_dono)
from source.systems.entitymanager import entity_manager
from source.systems.eventos import DANO_CAUSADO, eventos
from source.systems.gameclock import relogio

V = pygame.math.Vector2
RAIZ = pathlib.Path(__file__).resolve().parents[2]


def _ouvir_dano():
    recebidos = []
    eventos.assinar(DANO_CAUSADO, lambda **dados: recebidos.append(dados))
    return recebidos


def _grunt(game, deslocamento=V(300, 0)):
    return GruntRed(posicao=game.player.posicao + deslocamento, game=game)


# ── Dano ──────────────────────────────────────────────────────────────────────
def test_dano_guarda_os_campos():
    fonte = object()
    d = Dano(12.5, PROJETIL, fonte, ignora_iframes=True)
    assert (d.valor, d.tipo, d.fonte, d.ignora_iframes) == (12.5, PROJETIL, fonte, True)
    assert Dano(1, CONTATO).fonte is None and not Dano(1, CONTATO).ignora_iframes


def test_dano_e_imutavel():
    d = Dano(10, DIRETO)
    with pytest.raises(AttributeError):
        d.valor = 20


@pytest.mark.parametrize('valor', [-1, -0.001, float('nan'), float('-inf')])
def test_dano_recusa_valor_invalido(valor):
    with pytest.raises(ValueError):
        Dano(valor, DIRETO)


def test_dano_aceita_zero_e_infinito():
    assert Dano(0, DIRETO).valor == 0
    assert math.isinf(Dano(float('inf'), DIRETO).valor)


def test_dano_recusa_tipo_desconhecido():
    with pytest.raises(ValueError, match='tipo de dano desconhecido'):
        Dano(10, 'fogo')


def test_tipos_conhecidos():
    assert TIPOS_DANO == {PROJETIL, CONTATO, AURA, AREA, VOID, DIRETO}


def test_fonte_do_dono(player):
    explicita = object()
    assert fonte_do_dono('INIMIGO', explicita) is explicita
    assert fonte_do_dono('PLAYER') is player
    assert fonte_do_dono('INIMIGO') is None
    assert fonte_do_dono('BOSS') is None


# ── Jogador: escudo × i-frames × ignora_iframes × transbordo ────────────────
@pytest.mark.parametrize('escudo, invencivel, ignora, valor, esperado_escudo, perda_vida', [
    (0,  False, False, 30, 0,  30),   # vida direto
    (50, False, False, 30, 20, 0),    # escudo absorve tudo
    (50, False, False, 80, 0,  30),   # escudo quebra e transborda
    (50, False, False, 50, 0,  0),    # escudo zera exatamente, sem transbordo
    (0,  True,  False, 30, 0,  0),    # i-frames bloqueiam
    (50, True,  False, 80, 50, 0),    # i-frames bloqueiam antes do escudo
    (0,  True,  True,  30, 0,  30),   # ignora_iframes passa
    (50, True,  True,  80, 0,  30),   # ignora_iframes passa e transborda
])
def test_matriz_do_jogador(player, escudo, invencivel, ignora, valor, esperado_escudo, perda_vida):
    if escudo:
        player.adicionar_escudo(escudo)
    player.invencivel = invencivel
    player.receber_dano(Dano(valor, DIRETO, ignora_iframes=ignora))
    assert player.escudo_atual == esperado_escudo
    assert player.vida_atual == player.vida_maxima - perda_vida


def test_jogador_dano_comum_liga_iframes_e_interrompe_regeneracao(player):
    player.regenerando_escudo = True
    player.receber_dano(Dano(10, DIRETO))
    assert player.invencivel and player.tempo_ultimo_dano == relogio.agora()
    assert not player.regenerando_escudo and player.ultimo_dano_sofrido == relogio.agora()


def test_jogador_dano_que_ignora_iframes_nao_os_liga(player):
    player.regenerando_escudo = True
    player.receber_dano(Dano(10, VOID, ignora_iframes=True))
    assert not player.invencivel
    assert not player.regenerando_escudo   # mas interrompe a regeneração


def test_jogador_bloqueado_por_iframes_nao_interrompe_regeneracao(player):
    player.invencivel = True
    player.regenerando_escudo = True
    player.receber_dano(Dano(10, DIRETO))
    assert player.regenerando_escudo


def test_jogador_dano_letal_infinito(player):
    player.adicionar_escudo(100)
    player.receber_dano(Dano(float('inf'), DIRETO))
    assert player.vida_atual == 0 and player.escudo_atual == 0 and not player.alive()


# ── Inimigos ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize('escudo, valor, esperado_escudo, perda_vida', [
    (0,  30, 0,  30),
    (50, 30, 20, 0),
    (50, 80, 0,  30),
])
def test_matriz_do_inimigo(novo_jogo, escudo, valor, esperado_escudo, perda_vida):
    inimigo = _grunt(novo_jogo)
    inimigo.vida = 100
    inimigo.escudo_maximo = inimigo.escudo_atual = escudo
    inimigo.receber_dano(Dano(valor, PROJETIL, novo_jogo.player))
    assert inimigo.escudo_atual == esperado_escudo
    assert inimigo.vida == 100 - perda_vida


def test_inimigo_vida_nao_fica_negativa(novo_jogo):
    inimigo = _grunt(novo_jogo)
    inimigo.receber_dano(Dano(float('inf'), DIRETO))
    assert inimigo.vida == 0


def test_inimigo_nao_tem_iframes(novo_jogo):
    inimigo = _grunt(novo_jogo)
    inimigo.vida = 100
    inimigo.receber_dano(Dano(10, PROJETIL))
    inimigo.receber_dano(Dano(10, PROJETIL))
    assert inimigo.vida == 80


def test_gancho_que_ignora_nao_absorve_nem_emite(novo_jogo):
    inimigo = _grunt(novo_jogo)
    inimigo.vida = 100
    inimigo.ajustar_dano_recebido = lambda valor, dano: None
    recebidos = _ouvir_dano()
    inimigo.receber_dano(Dano(10, PROJETIL))
    assert inimigo.vida == 100 and recebidos == []


def test_gancho_recebe_o_dano_original(novo_jogo):
    inimigo = _grunt(novo_jogo)
    inimigo.vida = 100
    vistos = []
    inimigo.ajustar_dano_recebido = lambda valor, dano: vistos.append((valor, dano)) or valor * 2
    d = Dano(10, AREA)
    inimigo.receber_dano(d)
    assert vistos == [(10, d)] and inimigo.vida == 80


# ── Evento dano_causado ──────────────────────────────────────────────────────
def test_evento_no_inimigo_traz_alvo_dano_e_valor_final(novo_jogo):
    inimigo = _grunt(novo_jogo)
    recebidos = _ouvir_dano()
    d = Dano(10, PROJETIL, novo_jogo.player)
    inimigo.receber_dano(d)
    assert recebidos == [{'alvo': inimigo, 'dano': d, 'valor': 10}]


def test_evento_no_jogador_so_quando_o_dano_entra(player):
    recebidos = _ouvir_dano()
    d = Dano(10, CONTATO)
    player.receber_dano(d)
    player.receber_dano(Dano(10, CONTATO))   # bloqueado pelos i-frames
    assert recebidos == [{'alvo': player, 'dano': d, 'valor': 10}]


# ── Overrides dos bosses (ganchos) ───────────────────────────────────────────
def _boss(game, nome):
    game.spawner.spawnar(nome)
    return game.sessao.boss_atual


def _vida_tirada(alvo, dano):
    antes = alvo.vida
    alvo.receber_dano(dano)
    return antes - alvo.vida


@pytest.mark.parametrize('estado_fase, imune, com_sentinelas, esperado', [
    ('FASE1', False, False, 100),
    ('RAGE_F2', False, True, 40),      # sentinelas majors seguram 60%
    ('RAGE_F2', False, False, 100),
    ('TRANSICAO', False, False, 0),    # terminais ativos: ignora
    ('FASE1', True, False, 0),         # imune: ignora
])
def test_guilty(novo_jogo, estado_fase, imune, com_sentinelas, esperado):
    guilty = _boss(novo_jogo, 'guilty')
    guilty.estado_fase, guilty.imune = estado_fase, imune
    guilty.escudo_atual = 0
    guilty.sentinelas_majors = [_grunt(novo_jogo)] if com_sentinelas else []
    assert _vida_tirada(guilty, Dano(100, PROJETIL)) == pytest.approx(esperado)


@pytest.mark.parametrize('estado, olhando, jogador_dx, esperado', [
    ('stun', 'right', -100, 400),    # costas: x4
    ('stun', 'left', 100, 400),
    ('stun', 'right', 100, 100),     # de frente
    ('run', 'right', -100, 100),     # fora do stun
])
def test_hunter_pelas_costas(novo_jogo, estado, olhando, jogador_dx, esperado):
    hunter = _boss(novo_jogo, 'hunter')
    hunter.estado_habilidade, hunter.estado_animacao = estado, olhando
    hunter.escudo_atual = 0
    hunter.vida = 10 ** 6
    novo_jogo.player.posicao.update(hunter.posicao + V(jogador_dx, 0))
    assert _vida_tirada(hunter, Dano(100, PROJETIL)) == esperado


def test_scarab_defensivo_so_no_escudo_e_pernas_x5(novo_jogo):
    scarab = _boss(novo_jogo, 'scarab')
    scarab.estado_combate = 'MOVENDO'
    escudo, vida = scarab.escudo_atual, scarab.vida
    novo_jogo.player.posicao.update(scarab.posicao + V(0, -100))   # acima: sem bônus
    scarab.receber_dano(Dano(100, PROJETIL))
    assert scarab.escudo_atual == escudo - 100
    novo_jogo.player.posicao.update(scarab.posicao + V(0, 100))    # abaixo: pernas x5
    scarab.receber_dano(Dano(100, PROJETIL))
    assert scarab.escudo_atual == escudo - 600 and scarab.vida == vida


def test_scarab_escudo_quebrado_atordoa_sem_transbordar(novo_jogo):
    scarab = _boss(novo_jogo, 'scarab')
    scarab.estado_combate = 'MOVENDO'
    scarab.escudo_atual = 50
    vida = scarab.vida
    novo_jogo.player.posicao.update(scarab.posicao + V(0, -100))
    scarab.receber_dano(Dano(500, PROJETIL))
    assert scarab.escudo_atual == 0 and scarab.vida == vida
    assert scarab.estado_combate == 'STUNNED'


@pytest.mark.parametrize('olhando, jogador_dx, esperado', [
    ('right', -100, 1000),   # costas: x10
    ('left', 100, 1000),
    ('right', 100, 100),
])
def test_scarab_atordoado_pelas_costas(novo_jogo, olhando, jogador_dx, esperado):
    scarab = _boss(novo_jogo, 'scarab')
    scarab.iniciar_stun()
    scarab.estado_animacao = olhando
    scarab.escudo_atual = 0
    novo_jogo.player.posicao.update(scarab.posicao + V(jogador_dx, 0))
    assert _vida_tirada(scarab, Dano(100, PROJETIL)) == esperado


def test_consciencia_do_warden_ignora_dano(novo_jogo):
    consciencia = _boss(novo_jogo, 'warden')
    corpos = sum(w.vida for w in consciencia.wardens_vivos)
    recebidos = _ouvir_dano()
    consciencia.receber_dano(Dano(10 ** 6, PROJETIL))
    assert consciencia.vida == corpos and recebidos == []


# ── Fonte: quem causou ───────────────────────────────────────────────────────
def test_projetil_do_jogador_tem_o_jogador_como_fonte(player):
    p = BurstRifle(posicao_inicial=player.posicao, grupos=(entity_manager.all_sprites,), jogador=player,
                   game=player.game, dono='PLAYER', tamanho=(24, 24), dano=7, velocidade=100,
                   direcao_spread=V(1, 0))
    assert p.fonte is player


def test_projetil_inimigo_acerta_o_jogador_com_a_fonte(novo_jogo):
    grunt = _grunt(novo_jogo)
    recebidos = _ouvir_dano()
    p = PlasmaGun(posicao_inicial=novo_jogo.player.posicao, grupos=(entity_manager.all_sprites,),
                  jogador=novo_jogo.player, game=novo_jogo, dono='INIMIGO', tamanho=(20, 20), dano=9,
                  velocidade=0, direcao_spread=V(1, 0), vai_rotacionar=False, fonte=grunt)
    p.ao_atingir_alvo(novo_jogo.player)
    assert recebidos[0]['dano'] == Dano(9, PROJETIL, grunt)


def test_tiro_real_de_um_grunt_leva_a_fonte(novo_jogo):
    grunt = _grunt(novo_jogo)
    antes = set(entity_manager.projeteis_inimigos_grupo)
    grunt.plasma()
    novos = set(entity_manager.projeteis_inimigos_grupo) - antes
    assert novos and all(p.fonte is grunt for p in novos)


def test_artilharia_aplica_com_a_fonte_e_ignora_iframes(novo_jogo):
    grunt = _grunt(novo_jogo)
    player = novo_jogo.player
    player.invencivel = True
    recebidos = _ouvir_dano()
    aviso = ArtilhariaAviso(posicao=player.posicao, grupos=(entity_manager.all_sprites,), game=novo_jogo,
                            dono='INIMIGO', fonte=grunt)
    aviso._aplicar_dano_em_area(25)
    assert recebidos[0]['dano'] == Dano(25, AREA, grunt, ignora_iframes=True)


def test_contato_usa_dano_do_inimigo_e_aciona_espinhos_mesmo_com_iframes(novo_jogo):
    player = novo_jogo.player
    grunt = _grunt(novo_jogo, V(0, 0))
    grunt.invencivel = False
    player.configurar_espinhos(dano=30, cooldown=1000)
    player.espinho_disponivel = True
    player.invencivel = True
    grunt.vida = vida_grunt = 100
    recebidos = _ouvir_dano()
    novo_jogo.collision_manager.update(1 / 60)
    assert grunt.vida == vida_grunt - 30          # espinho voltou mesmo nos i-frames
    assert recebidos[0]['dano'] == Dano(30, CONTATO, player)


def _chamadas_de_ataque_sem_fonte():
    """Chamadas com `dono=` de inimigo (não 'PLAYER') que não passam `fonte=`."""
    faltando = []
    for caminho in (RAIZ / 'source').rglob('*.py'):
        arvore = ast.parse(caminho.read_text(encoding='utf-8'))
        for no in ast.walk(arvore):
            if not isinstance(no, ast.Call) or not isinstance(no.func, ast.Name):
                continue
            kws = {k.arg: k.value for k in no.keywords}
            dono = kws.get('dono')
            if dono is None or 'fonte' in kws:
                continue
            if isinstance(dono, ast.Constant) and dono.value == 'PLAYER':
                continue
            faltando.append(f'{caminho.relative_to(RAIZ).as_posix()}:{no.lineno} {no.func.id}')
    return faltando


def test_todo_ataque_inimigo_passa_a_fonte():
    """Sem fonte, o buff de dano do atacante e a memória dos bosses não veem o golpe."""
    assert _chamadas_de_ataque_sem_fonte() == []
