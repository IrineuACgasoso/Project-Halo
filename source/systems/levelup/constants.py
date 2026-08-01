from dataclasses import dataclass, field
from typing import Type, List

from source.feats.weapons import (
    RifleAssalto, Arma_Loop, ArmaLista, MK2_Shield,
    Needler, Shotgun, SpartanLaser, GrenadeLauncher,
    SniperRifle, SidekickPistol
)
from source.feats.buddies import Arbitro, Cortana, Marine

MAX_ARMAS = 6

# ─── PALETA DE CORES POR RARIDADE (Borda RGB, Fundo RGBA) ───
PALETA_RARIDADE = {
    'comum':     {'borda': (210, 215, 220),       'fundo': (35, 37, 40, 140)},
    'incomum':   {'borda': (46, 204, 113),        'fundo': (10, 45, 20, 140)},
    'raro':      {'borda': (52, 152, 219),        'fundo': (10, 35, 70, 140)},
    'epica':     {'borda': (155, 89, 182),        'fundo': (35, 15, 60, 140)},
    'lendaria':  {'borda': (241, 196, 15),        'fundo': (60, 45, 10, 140)}
}

@dataclass(frozen=True)
class ArmaInfo:
    id: str
    nome: str
    classe: Type
    grupos: List[str]
    descricao: str
    raridade: str = 'comum'  # Parâmetro adicionado para o controle de cor


def _registro(*infos: ArmaInfo) -> dict:
    return {info.id: info for info in infos}


# Adicione as raridades correspondentes que desejar para o seu arsenal
ARMAS_REGISTRO = _registro(
    ArmaInfo(
        id='rifle_assalto', nome='Rifle de Assalto', classe=RifleAssalto,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Rifle padrão do UNSC de cadência elevada.', raridade='comum'
    ),
    ArmaInfo(
        id='needler', nome='Needler', classe=Needler,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Dispara agulhas teleguiadas que explodem ao acumular.', raridade='incomum'
    ),
    ArmaInfo(
        id='bola_calderanica', nome='Bola Calderânica', classe=Arma_Loop,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Uma esfera de energia que orbita o jogador.', raridade='comum'
    ),
    ArmaInfo(
        id='ciclo_de_laminas', nome='Ciclo de Lâminas', classe=ArmaLista,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Lâminas giratórias que cortam inimigos próximos.', raridade='comum'
    ),
    ArmaInfo(
        id='mk2_shield', nome='Escudo MK-2', classe=MK2_Shield,
        grupos=['all_sprites', 'auras_grupo', 'inimigos_grupo'],
        descricao='Gera um escudo e causa dano por segundo ao redor do jogador.', raridade='comum'
    ),
    ArmaInfo(
        id='arbiter', nome='Árbitro', classe=Arbitro,
        grupos=['all_sprites', 'inimigos_grupo', 'items_grupo'],
        descricao='Um elite aliado que caça inimigos próximos.', raridade='epica'
    ),
    ArmaInfo(
        id='cortana', nome='Cortana', classe=Cortana,
        grupos=['all_sprites', 'inimigos_grupo', 'items_grupo'],
        descricao='Busca itens e XP próximos a você.', raridade='lendaria'
    ),
    ArmaInfo(
        id='marine', nome='UNSC Marine', classe=Marine,
        grupos=['all_sprites', 'inimigos_grupo', 'items_grupo'],
        descricao='Leal soldado que auxilia coletando itens e atacando inimigos.', raridade='raro'
    ),
    ArmaInfo(
        id='shotgun', nome='Shotgun', classe=Shotgun,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Arma de disparo próximo de alta letalidade.', raridade='incomum'
    ),
    ArmaInfo(
        id='spartan_laser', nome='Spartan Laser', classe=SpartanLaser,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Canhão de energia especializado em destruir inimigos fortes.', raridade='lendaria'
    ),
    ArmaInfo(
        id='grenade_launcher', nome='Grenade Launcher', classe=GrenadeLauncher,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Lança poderosas granadas de plasma que dissolvem grandes hordas.', raridade='raro'
    ),
    ArmaInfo(
        id='sniper_rifle', nome='Sniper Rifle', classe=SniperRifle,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Rifle de precisão UNSC, cadência lenta e dano devastador.', raridade='epica'
    ),
    ArmaInfo(
        id='sidekick_pistol', nome='Sidekick Pistol', classe=SidekickPistol,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Pistola padrão de elite, causa um grande dano com uma frequência alta.', raridade='comum'
    ),
)