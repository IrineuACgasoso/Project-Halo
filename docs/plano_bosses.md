# Plano: bosses inteligentes, vistosos e baratos

**Status:** aprovado (2026-11-21). A **ordem** de execução agora é a de `docs/roteiro_reformulacao.md`: a etapa 0 daqui virou C1, e as etapas 1 a 6 viraram F1 a F7. Este arquivo continua sendo o desenho técnico. Este plano substitui `source/docs/BOSS_CREATION.md`. As ideias boas daquele documento entram aqui: rotinas geradoras, fases em dataclass e sorteio por pesos.

## 1. Diagnóstico (medido, não estimado)
Medição: 20 s de luta headless com update e draw, 5 armas equipadas e o script de perfil da sessão de 2026-11-21. O orçamento é de **16,6 ms/frame** (60 FPS).

| Cenário | ms/frame | Observação |
|---|---|---|
| Arbiter, Harbinger, Atriox, Didact | 2,9 a 4,4 | bosses sozinhos são baratos |
| Warden, Gravemind | 5,9 a 6,8 | os mais caros, ainda dentro do orçamento |
| **Horda com 150 inimigos** | **31** | ❌ cerca de 32 FPS |

- **Gargalo:** cerca de 70% do frame da horda vai para `EnemyCollision.aplicar_colisao_mapa`. Cada inimigo testa **todos** os segmentos de parede próximos **do jogador** (raio de 1000 px), 2 iterações por frame, com `projetar_fora_da_linha` em Python puro. São cerca de 8,8 milhões de chamadas em 20 s.
- **Consequência:** um boss com invocações, projéteis e partículas só fica caro porque **soma** com a horda. Por isso o primeiro passo é dar folga ao frame.

**Estilos atuais de boss:**
- máquina de estados por string com timestamps (Tartarus, e as cópias Atriox e Escharum);
- `ia.py` próprio (Harbinger, Jega);
- rotinas geradoras (Arbiter, ainda sem commit).

Hoje anti-stuck, teleporte, invocação e fases estão reimplementados em cada boss.

## 2. Princípios
1. **Decidir raramente, executar barato.** A IA só "pensa" quando o boss está livre, cerca de 1 vez a cada 0,5 a 1 s. Cada frame só avança a rotina ativa.
2. **Perceber uma vez por frame, ou menos.** Um `ContextoCombate` é calculado uma única vez e lido por todas as decisões. Percepções caras (linha de visão, leitura de projéteis) rodam com um intervalo fixo, de 100 a 250 ms.
3. **Nada de alocação por frame.** Superfícies, máscaras, flips e rotações são preparados na carga e guardados em cache. Partículas e rastros vêm de um pool com teto global.
4. **Todo ataque tem telegraph legível e uma janela de punição.** A inteligência vem de *escolher bem*, não de ser injusto.
5. **Dados separados da lógica.** Os números ficam no `config.py` (dataclasses frozen). A lógica fica nas rotinas.

## 3. Arquitetura proposta
```
source/enemies/base/boss/
├── boss_base.py      # BossBase(BaseEnemy): ciclo do frame, rotina ativa, cooldowns, fases, interrupção
├── contexto.py       # ContextoCombate: dist, vel. do jogador, HP%, LoS, ameaças (atualização escalonada)
├── decisao.py        # IA de utilidade: pontuar(habilidade, ctx) + memória adaptativa
├── animador.py       # clips por estado, eventos de frame (hit frame), efeitos (flash, squash, rastro)
└── fases.py          # FaseBoss (dataclass) + subida de fase
source/feats/skills/  # blocos de habilidade reutilizáveis (cone, artilharia, EMP, purge, beam, tp...)
```
- **De onde vem a base:** a `BossBase` é **extraída do Arbiter**, que já roda e tem testes, e não escrita do zero. Ele já tem rotinas, `cd`, `wait`, fases, mira antecipada e anti-stuck.
- **Interface de cada boss:**
  - `FASES`;
  - `HABILIDADES` (nome → config com cooldown, alcance ideal e pré-condições);
  - `rotina_<nome>()`;
  - um `pontuar_<nome>(ctx)` opcional.

### 3.1 Inteligência (barata)
| Técnica | O que o jogador sente | Custo |
|---|---|---|
| **IA de utilidade**: cada habilidade dá uma nota de 0 a 1 a partir do contexto (distância ideal, jogador parado ou fugindo, HP do boss, invocados vivos) | o boss "escolhe a ferramenta certa" | uma decisão por segundo |
| **Mira preditiva** (`_ponto_antecipado`, que já existe no Arbiter) com um fator por fase | os tiros "leem" o movimento | desprezível |
| **Leitura de padrão**: um histograma de 8 direções de fuga e o tempo parado ou kitando | pune quem repete a mesma esquiva | uma atualização a cada 250 ms |
| **Memória adaptativa**: o peso de cada habilidade é ajustado pelo dano que ela causou *nesta luta* | o boss muda de estratégia no meio da luta | uma soma por acerto |
| **Esquiva reativa**: amostra os projéteis do jogador num cone à frente | desvia de rajadas óbvias | no máximo N verificações a cada 100 ms |
| **Fases que trocam o moveset**, não só os números | a luta tem atos | nenhum |
| **Coordenação**: o boss usa os invocados como escudo ou para cercar | sensação de comandante | só na decisão |

### 3.2 Habilidades
- Os blocos que já existem (`cone_strike`, `artilharia`, `onda_emp`, `purge_grid`, `continuousbeam`, `mortar`, `promethean_tp`) viram **componentes padronizados**: um preset em `config.py`, telegraph obrigatório e o parâmetro `dono`.
- Uma rotina é uma **composição de blocos**. Exemplo: `teleporte → cone em leque → artilharia no ponto previsto`. Habilidade nova = rotina nova + preset, sem motor novo.
- Combos crescem com a fase (`fase_cfg.golpes`) e encadeiam com `yield from`.

### 3.3 Animações
- **Clips declarativos por estado** (`idle`, `andar`, `telegraph`, `ataque`, `recuperacao`, `morte`): frames, fps e loop ficam no config.
- **Eventos de frame:** o dano sai no *hit frame* da animação, e não num timer solto. Isso sincroniza visual e mecânica.
- **Cache na carga:** flip, rotações em ângulos quantizados (ex.: 32 direções) e **máscaras por frame**. Hoje o Gravemind faz `mask.from_surface` a cada `animar()`.
- **Efeitos baratos:** flash de dano (já existe `trigger_flash`), squash/stretch no telegraph, rastro do dash com superfícies pré-escurecidas de um pool, e shake de câmera (já existe).

## 4. Etapas (cada uma entregue com testes verdes)
| # | Etapa | Entrega | Critério de pronto |
|---|---|---|---|
| 0 | **Folga de desempenho** | Grade espacial de segmentos de parede, para que cada inimigo teste só as células vizinhas a ele. Fim das alocações por frame em `ArtilhariaAviso.draw` e no `PlasmaGrenade.update` | Horda de 150 com **≤ 10 ms/frame**, medida por um script de perfil versionado (`tools/perf_luta.py`) |
| 1 | `BossBase` + `ContextoCombate` | Extraídos do Arbiter, que passa a usá-los sem mudar o comportamento | Smoke e regressão verdes; testes unitários do motor (cooldown, fases, interrupção, anti-stuck) |
| 2 | `Animador` | Clips, hit frames e cache de máscaras; o Arbiter migra para ele | O update do boss não aloca nenhuma `Surface` (verificado em teste) |
| 3 | IA de utilidade + memória adaptativa | `decisao.py`; o Arbiter passa a usar notas | Teste determinístico: dado o contexto X, a habilidade escolhida é Y |
| 4 | Bot jogador para simulação | Um jogador que esquiva e kita no `tests/helpers` | Métricas por boss: tempo para matar, % de acertos e uso de cada habilidade |
| 5 | Migração boss a boss | Primeiro Atriox e Escharum (hoje cópias do Tartarus: ganham identidade), depois os demais | Cada boss migrado continua nos smoke tests |
| 6 | Documentação | `docs/bosses.md` (guia final) + `boss_template` | Substitui de vez o `BOSS_CREATION.md` |

**Orçamento por boss depois da etapa 2:** até 1,5 ms/frame de update e até 2 ms de draw, com 20 projéteis/efeitos ativos.

## 5. Decisões (2026-11-21)
1. Ordem: a do `docs/roteiro_reformulacao.md` (a etapa 0 virou C1).
2. **Memória adaptativa reseta a cada luta.**
3. Arbiter commitado na linha de base (etapa A0 do roteiro); a extração da `BossBase` (F1) parte de um diff limpo.
