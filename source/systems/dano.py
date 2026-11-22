"""Contrato de dano único (roteiro E1).

Todo dano do jogo é um `Dano` entregue a `alvo.receber_dano(dano)`, seja o alvo o jogador ou um inimigo.
- `fonte`: a entidade que causou o dano (o jogador, um inimigo ou None para o mapa). Projéteis,
  granadas e habilidades guardam a fonte de quem os criou. É por ela que o buff de dano de quem
  ataca entra na conta e que o evento `dano_causado` diz quem acertou (memória dos bosses, F3).
- `ignora_iframes`: só o jogador tem i-frames; o dano que os ignora também não os liga.

Uso:  from source.systems.dano import Dano, PROJETIL
      alvo.receber_dano(Dano(10, PROJETIL, fonte=self.fonte))
"""
from dataclasses import dataclass

from source.systems.entitymanager import entity_manager

PROJETIL = 'projetil'   # tiro que acerta o alvo (ProjetilUniversal e filhos)
CONTATO = 'contato'     # corpo a corpo: encostar, investida, atropelamento, espinhos
AURA = 'aura'           # área contínua presa a alguém (MK2, aura de energia)
AREA = 'area'           # habilidade de área: explosão, cone, onda, puxão, feixe contínuo
VOID = 'void'           # zona de void do mapa
DIRETO = 'direto'       # sem meio físico (ex.: o golpe letal do Tartarus)

TIPOS_DANO = frozenset({PROJETIL, CONTATO, AURA, AREA, VOID, DIRETO})


@dataclass(frozen=True, slots=True)
class Dano:
    valor: float
    tipo: str
    fonte: object = None
    ignora_iframes: bool = False

    def __post_init__(self):
        if self.tipo not in TIPOS_DANO:
            raise ValueError(f'tipo de dano desconhecido: {self.tipo!r} (conhecidos: {sorted(TIPOS_DANO)})')
        # `not >=` também recusa NaN. Infinito vale (golpe letal).
        if not self.valor >= 0:
            raise ValueError(f'valor de dano inválido: {self.valor!r} (precisa ser >= 0)')


def fonte_do_dono(dono, fonte=None):
    """A fonte de um projétil ou habilidade. Sem fonte explícita, o que é do jogador é dele (só há um);
    o que é de inimigo fica sem fonte (quem cria deve passar `fonte=self`)."""
    if fonte is not None:
        return fonte
    return entity_manager.player if dono == 'PLAYER' else None
