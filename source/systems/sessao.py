"""Estado de UMA partida (roteiro B3).

Nasce em `Game.iniciar_novo_jogo` e é descartada no fim: o restart é um objeto novo, então nada
de uma partida sobra para a próxima. Tudo que vale só durante a partida entra aqui, não no `Game`.
"""
from dataclasses import dataclass
from typing import Any


@dataclass
class SessaoJogo:
    timer_jogo: float = 0.0              # s de jogo livre (sem boss, portal nem transição): agenda os bosses
    fase_atual: int = 0
    boss_atual: Any = None               # boss vivo da fase; None libera o spawner e o timer
    portal_atual: Any = None
    spawnar_portal_em_breve: bool = False
    timer_portal: int = 0                # relogio.agora() da morte do boss: o portal nasce 2000 ms depois
    tela_de_upgrade_ativa: Any = None    # TelaDeUpgrade aberta no estado level_up
    gravemind_reborns: int = 3           # renascimentos que o Gravemind ainda tem
