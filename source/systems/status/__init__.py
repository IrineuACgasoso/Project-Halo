"""Sistema de status: buffs e debuffs para o jogador e os inimigos (pedido em 2026-11-21).

Uso:  from source.systems.status import aplicar, Queimadura
      aplicar(inimigo, Queimadura(dps=20, duracao_ms=3000, reducao_cura=0.5), fonte=self)
"""
from .efeitos import (Atordoamento, BuffCadencia, BuffDano, BuffVelocidade, Cegueira, Cura,
                      Defesa, Escudo, Fraqueza, IMUNIDADES_CHEFE, INSTANTANEOS, Lentidao, Queimadura,
                      SO_NO_JOGADOR, TEMPORARIOS, TETO_PORCENTAGEM)
from .status import (StatusEntidade, TICK_QUEIMADURA, aplicar, atualizar_status, limpar_status,
                     multiplicador_de_dano, remover)

__all__ = [
    'Atordoamento', 'BuffCadencia', 'BuffDano', 'BuffVelocidade', 'Cegueira', 'Cura', 'Defesa', 'Escudo',
    'Fraqueza', 'IMUNIDADES_CHEFE', 'INSTANTANEOS', 'Lentidao', 'Queimadura', 'SO_NO_JOGADOR',
    'TEMPORARIOS', 'TETO_PORCENTAGEM', 'StatusEntidade', 'TICK_QUEIMADURA', 'aplicar',
    'atualizar_status', 'limpar_status', 'multiplicador_de_dano', 'remover',
]
