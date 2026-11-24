"""Fuel Rod: quique só quando o alvo morre antes do impacto, e poça que aplica queimadura."""
import pygame
import pytest

from helpers import DT
from source.enemies.standard.grunt import GruntRed
from source.feats.grenades import FuelRodGrenade
from source.feats.skills.artilharia import ArtilhariaAviso, PocaDePlasma
from source.feats.skills.artilharia.config import ARTILHARIA_PRESETS, ArtilhariaConfig
from source.systems.entitymanager import entity_manager
from source.systems.gameclock import relogio
from source.systems.status import Queimadura, atualizar_status

V = pygame.math.Vector2
PRESET = ARTILHARIA_PRESETS['fuel_rod']


def _inimigo(game, posicao):
    inimigo = GruntRed(posicao=V(posicao), game=game)
    inimigo.vida = inimigo.vida_maxima = 1000
    inimigo.escudo_atual = 0
    inimigo.invencivel = False      # sem a proteção de spawn
    return inimigo


def _carga(game, alvo, quiques):
    p = V(game.player.posicao)
    return FuelRodGrenade(posicao_inicial=p, posicao_alvo=alvo.posicao, grupos=(entity_manager.all_sprites,),
                          game=game, dono='PLAYER', inimigos_grupo=entity_manager.inimigos_grupo,
                          quiques=quiques, alvo=alvo)


def _voar(carga, limite=600):
    """Até grudar ou explodir."""
    while limite and carga.alive() and not carga.grudado:
        relogio.avancar(DT)
        carga.update(DT)
        limite -= 1
    assert limite


def _avisos():
    return [s for s in entity_manager.all_sprites if isinstance(s, ArtilhariaAviso)]


def _levar_para_longe(inimigo):
    inimigo.posicao += V(0, 5000)
    inimigo.sync_rect()


# ── Quique ───────────────────────────────────────────────────────────────────
def test_alvo_morto_quica_ate_grudar_em_outro(novo_jogo):
    p = novo_jogo.player.posicao
    alvo, outro = _inimigo(novo_jogo, p + V(400, 0)), _inimigo(novo_jogo, p + V(600, 60))
    carga = _carga(novo_jogo, alvo, quiques=2)
    alvo.kill()
    _voar(carga)
    assert carga.grudado and carga.alvo is outro and carga.quiques == 1


def test_sem_ninguem_por_perto_gasta_os_quiques_e_explode_mais_longe(novo_jogo):
    alvo = _inimigo(novo_jogo, novo_jogo.player.posicao + V(400, 0))
    carga = _carga(novo_jogo, alvo, quiques=2)
    queda = V(carga.target_pos)
    alvo.vida = 0               # morto que ainda não saiu do mundo também conta
    _levar_para_longe(alvo)
    _voar(carga)
    assert carga.quiques == 0 and not carga.alive()
    (aviso,) = _avisos()
    assert aviso.posicao.distance_to(queda) == pytest.approx(2 * FuelRodGrenade.SALTO_SEM_ALVO)


@pytest.mark.parametrize('quiques, alvo_morre', [(3, False), (0, True)])
def test_explode_onde_caiu_se_o_alvo_so_fugiu_ou_sem_quiques(novo_jogo, quiques, alvo_morre):
    alvo = _inimigo(novo_jogo, novo_jogo.player.posicao + V(400, 0))
    carga = _carga(novo_jogo, alvo, quiques)
    queda = V(carga.target_pos)
    _levar_para_longe(alvo)
    if alvo_morre:
        alvo.kill()
    _voar(carga)
    assert carga.quiques == quiques and [a.posicao for a in _avisos()] == [queda]


def test_nao_quica_no_invisivel(novo_jogo):
    alvo = _inimigo(novo_jogo, novo_jogo.player.posicao + V(400, 0))
    carga = _carga(novo_jogo, alvo, quiques=1)
    assert carga._alvo_do_quique() is alvo
    alvo.alpha_atual = 0
    assert carga._alvo_do_quique() is None


# ── Poça ─────────────────────────────────────────────────────────────────────
def _poca(game, **cfg):
    config = ArtilhariaConfig(**{**vars(PRESET), 'duracao': 0, **cfg})
    return PocaDePlasma(V(600, 600), (entity_manager.all_sprites,), game, dono='PLAYER', preset='fuel_rod',
                        custom_config=config)


def _passos(sprites, segundos):
    for _ in range(round(segundos / DT)):
        relogio.avancar(DT)
        atualizar_status(DT)
        for s in sprites:
            s.update(DT)


def test_poca_da_o_impacto_e_queima_so_quem_esta_dentro(novo_jogo):
    perto = _inimigo(novo_jogo, (600, 600))
    longe = _inimigo(novo_jogo, (600 + PRESET.raio_explosao + 1, 600))
    poca = _poca(novo_jogo, dano=25, dano_por_segundo=40, duracao_dot=2000, queimadura_ms=1000)
    _passos([poca], 0.1)
    assert perto.vida == 975 and perto.status.tem(Queimadura)      # a poça em si só aplica o debuff
    _passos([poca], 3.9)                                           # 2 s na poça + 1 s de queimadura depois
    assert not poca.alive() and not perto.status.tem(Queimadura)
    assert 975 - perto.vida == pytest.approx(40 * 3, abs=40 * 0.3)
    assert longe.vida == 1000


def test_pocas_sobrepostas_nao_somam(novo_jogo):
    alvo = _inimigo(novo_jogo, (600, 600))
    _passos([_poca(novo_jogo), _poca(novo_jogo)], 0.5)
    assert len(alvo.status.ativos()) == 1


def test_invulneravel_nao_pega_fogo(novo_jogo):
    alvo = _inimigo(novo_jogo, (600, 600))
    alvo.is_invulneravel = True
    _passos([_poca(novo_jogo)], 0.5)
    assert not alvo.status.tem(Queimadura)
