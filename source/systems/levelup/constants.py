from dataclasses import dataclass, field
from typing import Type, List

from source.feats.weapons import (
    RifleAssalto, Arma_Loop, ArmaLista, MK2_Shield,
    Needler, Shotgun, SpartanLaser, GrenadeLauncher
)
from source.feats.buddies import Arbitro, Cortana, Marine

MAX_ARMAS = 6


@dataclass(frozen=True)
class ArmaInfo:
    id: str
    nome: str
    classe: Type
    grupos: List[str]
    descricao: str


def _registro(*infos: ArmaInfo) -> dict:
    return {info.id: info for info in infos}


ARMAS_REGISTRO = _registro(
    ArmaInfo(
        id='rifle_assalto', nome='Rifle de Assalto', classe=RifleAssalto,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Rifle padrão do UNSC de cadência elevada.'
    ),
    ArmaInfo(
        id='bola_calderanica', nome='Bola Calderânica', classe=Arma_Loop,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Uma esfera de energia que orbita o jogador.'
    ),
    ArmaInfo(
        id='ciclo_de_laminas', nome='Ciclo de Lâminas', classe=ArmaLista,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Lâminas giratórias que cortam inimigos próximos.'
    ),
    ArmaInfo(
        id='mk2_shield', nome='Escudo MK-2', classe=MK2_Shield,
        grupos=['all_sprites', 'auras_grupo', 'inimigos_grupo'],
        descricao='Gera um escudo e causa dano por segundo ao redor do jogador.'
    ),
    ArmaInfo(
        id='arbiter', nome='Árbitro', classe=Arbitro,
        grupos=['all_sprites', 'inimigos_grupo', 'items_grupo'],
        descricao='Um elite aliado que caça inimigos próximos.'
    ),
    ArmaInfo(
        id='cortana', nome='Cortana', classe=Cortana,
        grupos=['all_sprites', 'inimigos_grupo', 'items_grupo'],
        descricao='Busca itens e XP próximos a você.'
    ),
    ArmaInfo(
        id='marine', nome='UNSC Marine', classe=Marine,
        grupos=['all_sprites', 'inimigos_grupo', 'items_grupo'],
        descricao='Leal soldado que auxilia coletando itens e atacando inimigos.'
    ),
    ArmaInfo(
        id='needler', nome='Needler', classe=Needler,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Dispara agulhas teleguiadas que explodem ao acumular.'
    ),
    ArmaInfo(
        id='shotgun', nome='Shotgun', classe=Shotgun,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Arma de disparo próximo de alta letalidade.'
    ),
    ArmaInfo(
        id='spartan_laser', nome='Spartan Laser', classe=SpartanLaser,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Canhão de energia especializado em destruir inimigos fortes.'
    ),
    ArmaInfo(
        id='grenade_launcher', nome='Grenade Launcher', classe=GrenadeLauncher,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Lança poderosas granadas de plasma que dissolvem grandes hordas.'
    ),
)