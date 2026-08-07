from dataclasses import dataclass, field
from typing import Type, List

from source.feats.weapons import (
    RifleAssalto, BrickLauch, EnergySword, MK2_Shield,
    Needler, Shotgun, SpartanLaser, GrenadeLauncher,
    SniperRifle, SidekickPistol, LightRifle, CarabinRifle,
    MachineGun, MjolnirPunch, Dizimator
)
from source.feats.buddies import Arbitro, Cortana, Marine

MAX_ARMAS = 6

# ─── PALETA DE CORES POR RARIDADE (Borda RGB, Fundo RGBA) ───
PALETA_RARIDADE = {
    'comum':     {'borda': (210, 215, 220),       'fundo': (35, 37, 40, 140)},
    'incomum':   {'borda': (46, 204, 113),        'fundo': (10, 45, 20, 140)},
    'rara':      {'borda': (52, 152, 219),        'fundo': (10, 35, 70, 140)},
    'epica':     {'borda': (155, 89, 182),        'fundo': (35, 15, 60, 140)},
    'lendaria':  {'borda': (241, 196, 15),        'fundo': (60, 45, 10, 140)}
}

PALETA_NIVEL = {
    1:  (140, 200, 255),
    5:  (180, 180, 180),
    10: (255, 215, 0),
    15: (255, 100, 210),
    20: (255, 30, 80)
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
        id='carabin_rifle', nome='Carabin Rifle', classe=CarabinRifle,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Dispara plasma teleguiados eficiente contra escudos.', raridade='rara'
    ),
    ArmaInfo(
        id='brick', nome='Tijolo', classe=BrickLauch,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Arma canônicamente associada ao Master Chief.', raridade='lendaria'
    ),
    ArmaInfo(
        id='energy_sword', nome='Energy Sword', classe=EnergySword,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Lâminas de energia para ataques de curta distância.', raridade='epica'
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
        descricao='Leal soldado que auxilia coletando itens e atacando inimigos.', raridade='rara'
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
        descricao='Lança poderosas granadas de plasma que dissolvem grandes hordas.', raridade='rara'
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
    ArmaInfo(
        id='light_rifle', nome='Light Rifle', classe=LightRifle,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Rifle de supressão contínua, perfeito para destruir inimigos fortes.', raridade='lendaria'
    ),
    ArmaInfo(
        id='machine_gun', nome='Machine Gun', classe=MachineGun,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Altíssima cadência e um dano constante. Cuidado com o superaquecimento!', raridade='lendaria'
    ),
    ArmaInfo(
        id='mjolnir_punch', nome='Mjolnir Punch', classe=MjolnirPunch,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Contra-ataque Spartan rápido que neutraliza rapidamente pequenas ameaças.', raridade='comum'
    ),
    ArmaInfo(
        id='dizimator', nome='Dizimator', classe=Dizimator,
        grupos=['all_sprites', 'projeteis_jogador_grupo', 'inimigos_grupo'],
        descricao='Arma de alto calibre que atira rajadas poderosas a curtas distâncias.', raridade='incomum'
    ),
)