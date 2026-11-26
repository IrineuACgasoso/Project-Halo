"""Partículas e efeitos visuais reaproveitados no jogo todo, um arquivo por efeito:

- `motor`: o motor (Particula, emitir, emitir_leque, caches de imagem e o teto global);
- `poeira`: terra que salta do chão, nuvens de impacto (área, retângulo, anel) e rastro de corrida;
- `quebra_escudo`: o efeito padrão de todo escudo que acaba;
- `fogo`: quem está com queimadura (desenhado pelo Renderer);
- `lentidao`: quem está lento, corpo azulado e pés em câmera lenta (desenhado pelo Renderer);
- `energia`: energia que vaza do chão durante um aviso e é liberada no fim; vórtice que suga;
- `explosao`: clarão, faíscas e poeira de um impacto.

O motor é reexportado aqui (`from source.feats.particulas import emitir_leque`); os efeitos se
importam do próprio arquivo (`from source.feats.particulas.poeira import anel_de_poeira`)."""
from .motor import (NIVEIS_ALPHA, TETO_PARTICULAS, Particula, emitir, emitir_leque, imagem_pixel, preparar,
                    variante_alpha, variantes_alpha)

__all__ = ['NIVEIS_ALPHA', 'TETO_PARTICULAS', 'Particula', 'emitir', 'emitir_leque', 'imagem_pixel', 'preparar',
           'variante_alpha', 'variantes_alpha']
